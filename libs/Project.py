#!/usr/bin/python -tt
# vim: ai ts=4 sts=4 et sw=4

#    Copyright (c) 2007 Intel Corporation
#
#    This program is free software; you can redistribute it and/or modify it
#    under the terms of the GNU General Public License as published by the Free
#    Software Foundation; version 2 of the License
#
#    This program is distributed in the hope that it will be useful, but
#    WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY
#    or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License
#    for more details.
#
#    You should have received a copy of the GNU General Public License along
#    with this program; if not, write to the Free Software Foundation, Inc., 59
#    Temple Place - Suite 330, Boston, MA 02111-1307, USA.

import glob
import os
import re
import shutil
import socket
import stat
import sys
import time

import pdk_utils
import InstallImage
import SDK

class FileSystem(object):
    """
    This is the base class for any type of a filesystem.  This is used for both
    creating 'jailroot' filesystems that isolate a build from the host Linux
    distribution, and also for creating 'target' filesystems that will
    eventually be transformed into installation images to be
    burned/copied/whatever into the target device.

    By just instantiating a FileSystem object, the caller will trigger the
    basic root filesystem components to be initialized, but to do anything
    usefull with the root filesystem will require the caller to use the
    'install' method for installing new RPM packages.
    """
    def __init__(self, path, cb):
        if not path:
            raise ValueError("Empty argument passed in")
        self.cb = cb
        self.path = os.path.abspath(os.path.expanduser(path))

    def update(self, path):
        command = '-y --force-yes -o Dir::State=%(t)s/var/lib/apt -o Dir::State::status=%(t)s/var/lib/dpkg/status -o Dir::Cache=/var/cache/apt -o Dir::Etc::Sourcelist=%(t)s/etc/apt/sources.list -o Dir::Etc::main=%(t)s/etc/apt/apt.conf -o Dir::Etc::parts=%(t)s/etc/apt/apt.conf.d -o DPkg::Options::=--root=%(t)s -o DPkg::Run-Directory=%(t)s update' % {'t': path}
        ret = self.chroot("/usr/bin/apt-get", command) 
        if ret != 0:
            raise OSError("Internal error while attempting to run: %s" % command)
        
    def install(self, path, packages):
        if not packages:
            # No packages, so nothing to do
            return
        command = '-y --force-yes -o Dir::State=%(t)s/var/lib/apt -o Dir::State::status=%(t)s/var/lib/dpkg/status -o Dir::Cache=/var/cache/apt -o Dir::Etc::Sourcelist=%(t)s/etc/apt/sources.list -o Dir::Etc::main=%(t)s/etc/apt/apt.conf -o Dir::Etc::parts=%(t)s/etc/apt/apt.conf.d -o DPkg::Options::=--root=%(t)s -o DPkg::Run-Directory=%(t)s install ' % {'t': path}
        for p in packages:
            command += ' %s' % p
        ret = self.chroot("/usr/bin/apt-get", command) 
        if ret != 0:
            raise OSError("Internal error while attempting to run: apt-get %s" % command)

    def mount(self):
        for mnt in ['var/cache/apt/archives', 'tmp', 'proc', 'sys', 'usr/share/pdk']:
            path = os.path.join(self.path, mnt)
            if not os.path.isdir(path):
                os.makedirs(path)
            if not os.path.ismount(path) and os.path.isdir(os.path.join('/', mnt)):
                result = os.system('mount --bind /%s %s' % (mnt, path))
                if result != 0:
                    raise OSError("Internal error while attempting to bind mount /%s!" % (mnt))

        for file in ['etc/resolv.conf', 'etc/hosts']:
            if os.path.isfile(os.path.join('/', file)):
                shutil.copy(os.path.join('/', file), os.path.join(self.path, file))

        if os.path.isfile(os.path.join(self.path, '.buildroot')):
            # search for any file:// URL's in the configured apt repositories, and
            # when we find them make the equivilant directory in the new filesystem
            # and then mount --bind the file:// path into the filesystem.
            rdir = os.path.join(self.path, 'etc', 'apt', 'sources.list.d')
            if os.path.isdir(rdir):
                for fname in os.listdir(rdir):
                    file = open(os.path.join(rdir, fname))
                    for line in file:
                        if re.search(r'^\s*deb file:\/\/\/', line):
                            p = line.split('file:///')[1].split(' ')[0]
                            new_mount = os.path.join(self.path, p)
                            if not os.path.isdir(new_mount):
                                os.makedirs(new_mount)
                                os.system("mount --bind /%s %s" % (p, new_mount))
                    # Its no big deal if the repo is really empty, so
                    # ignore mount errors.
                    file.close()

        # first time mount
        buildstamp_path = os.path.join(self.path, 'etc', 'buildstamp')
        if not os.path.isfile(buildstamp_path):
            buildstamp = open(buildstamp_path, 'w')
            print >> buildstamp, "%s %s" % (socket.gethostname(), time.strftime("%d-%m-%Y %H:%M:%S %Z"))
            buildstamp.close()
            self.chroot("/usr/bin/apt-get", "update")
                
    def umount(self):
        for line in os.popen('mount', 'r').readlines():
            mpoint = line.split()[2]
            if self.path == mpoint[:len(self.path)]:
                os.system("umount %s" % (mpoint))

    def chroot(self, cmd_path, cmd_args, output = None):
        print "self.chroot(%s, %s)" % (cmd_path, cmd_args)
        if output == None:
            output = []
        if not os.path.isfile(os.path.join(self.path, 'bin/bash')):
            print >> sys.stderr, "Incomplete jailroot at %s" % (self.path)
            raise ValueError("Internal Error: Invalid buildroot at %s" % (self.path))
        self.mount()
        cmd_line = "chroot %s %s %s" % (self.path, cmd_path, cmd_args)
        result = pdk_utils.execCommand(cmd_line, output = output, callback = self.cb.iteration)
        if result != 0:
            # This is probably redundant
            sys.stdout.flush()
            print "Error in chroot"
            print "Command was: %s" % cmd_line
            sys.stdout.flush()
        return result

class Project(FileSystem):
    """
    A Project is a type of  'jailroot' filesystem that is used to isolate the
    build system from the host Linux distribution.  It also knows how to create
    new 'target' filesystems.
    """
    def __init__(self, path, name, desc, platform, cb):
        if not path or not name or not desc or not platform:
            raise ValueError("Empty argument passed in")
        self.path = os.path.abspath(os.path.expanduser(path))
        self.name = name
        self.platform = platform
        self.desc = desc
        FileSystem.__init__(self, self.path, cb)

        # Create our targets directory
        targets_path = os.path.join(self.path, 'targets')
        if not os.path.isdir(targets_path):
            os.makedirs(targets_path)

        # Instantiate all targets
        self.targets = {}
        for dirname in os.listdir(targets_path):
            target = Target(dirname, self, self.cb)
            self.targets[target.name] = target

    def install(self):
        """
        Install all the packages defined by Platform.buildroot_packages
        """
        FileSystem.install(self, "/", self.platform.buildroot_packages)

    def update(self):
        FileSystem.update(self, "/")

    def create_target(self, name):
        if not name:
            raise ValueError("Target name was not specified")
        if not name in self.targets:
            install_path = os.path.join(self.path, 'targets', name, 'fs')
            os.makedirs(install_path)
            rootstrap = os.path.join(self.platform.path, "target-rootstrap.tar.bz2")
            if not os.path.isfile(rootstrap):
                cmd = "debootstrap --arch i386 --include=apt %s %s %s" % (self.platform.target_codename, install_path, self.platform.target_mirror)
                output = []
                result = pdk_utils.execCommand(cmd, output = output, callback = self.cb.iteration)
                if result != 0:
                    print >> sys.stderr, "ERROR: Unable to generate target rootstrap!"
                    raise ValueError(" ".join(output))
                os.system('rm -fR %s/var/cache/apt/archives/*.dev' % (install_path))

                # workaround for ubuntu kernel package bug
                os.system('touch %s/etc/kernel-img.conf' % (install_path))
                os.system('touch %s/etc/kernel-pkg.conf' % (install_path))
                
                for f in os.listdir(os.path.join(self.platform.path, 'sources')):
                    shutil.copy(os.path.join(self.platform.path, 'sources', f), os.path.join(install_path, 'etc', 'apt', 'sources.list.d'))
                cmd = "tar -jcpvf %s -C %s ." % (rootstrap, install_path)
                output = []
                result = pdk_utils.execCommand(cmd, output = output, callback = self.cb.iteration)
                if result != 0:
                    print >> sys.stderr, "ERROR: Unable to archive rootstrap!"
                    shutil.rmtree(install_path)
                    raise ValueError(" ".join(output))
            else:
                cmd = "tar -jxvf %s -C %s" % (rootstrap, install_path)
                output = []
                result = pdk_utils.execCommand(cmd, output = output, callback = self.cb.iteration)
                if result != 0:
                    print >> sys.stderr, "ERROR: Unable to rootstrap %s from %s!" % (rootstrap, name)
                    shutil.rmtree(os.path.join(self.path, 'targets', name))
                    raise ValueError(" ".join(output))

            self.targets[name] = Target(name, self, self.cb)
            self.targets[name].mount()
            self.targets[name].update()            
            # Install platform default kernel cmdline
            self.set_target_usb_kernel_cmdline(name, self.platform.usb_kernel_cmdline)
            self.set_target_hd_kernel_cmdline(name, self.platform.hd_kernel_cmdline)
        return self.targets[name]
    
    def get_target_usb_kernel_cmdline(self, name):
        if not name:
           raise ValueError("Target name was not specified")
        cmdline = open(os.path.join(self.targets[name].config_path, 'usb_kernel_cmdline'), 'r')
        usb_kernel_cmdline = ''
        for line in cmdline:
            if not re.search(r'^\s*#',line): 
                usb_kernel_cmdline += line + ' '
        cmdline.close()
        return usb_kernel_cmdline.strip()

    def get_target_hd_kernel_cmdline(self, name):
        if not name:
           raise ValueError("Target name was not specified")
        cmdline = open(os.path.join(self.targets[name].config_path, 'hd_kernel_cmdline'), 'r')
        hd_kernel_cmdline = ''
        for line in cmdline:
            if not re.search(r'^\s*#',line): 
                hd_kernel_cmdline += line + ' '
        cmdline.close()
        return hd_kernel_cmdline.strip()

    def set_target_usb_kernel_cmdline(self, name, str):
        if not name:
           raise ValueError("Target name was not specified")
        cmdline = open(os.path.join(self.targets[name].config_path, 'usb_kernel_cmdline'), 'w')
        print >> cmdline, str
        cmdline.close()

    def set_target_hd_kernel_cmdline(self, name, str):
        if not name:
           raise ValueError("Target name was not specified")
        cmdline = open(os.path.join(self.targets[name].config_path, 'hd_kernel_cmdline'), 'w')
        print >> cmdline, str
        cmdline.close()

    def delete_target(self, name, do_pop=True):
        target = self.targets[name]
        target.umount()
        shutil.rmtree(os.path.join(self.path, 'targets', name))
        if do_pop:
            self.targets.pop(name)
        
    def create_live_iso(self, target_name, image_name):
        target = self.targets[target_name]
        target.umount()
        image = InstallImage.LiveIsoImage(self, self.targets[target_name], image_name)
        image.create_image()
        target.mount()

    def create_install_iso(self, target_name, image_name):
        target = self.targets[target_name]
        target.umount()
        image = InstallImage.InstallIsoImage(self, self.targets[target_name], image_name)
        image.create_image()
        target.mount()

    def create_live_usb(self, target_name, image_name, type="RAMFS"):
        target = self.targets[target_name]
        target.umount()
        image = InstallImage.LiveUsbImage(self, self.targets[target_name], image_name)
        image.create_image(type)
        target.mount()

    def create_install_usb(self, target_name, image_name):
        target = self.targets[target_name]
        target.umount()
        image = InstallImage.InstallUsbImage(self, self.targets[target_name], image_name)
        image.create_image()
        target.mount()

    def __str__(self):
        return ("<Project: name=%s, path=%s>"
                % (self.name, self.path))
    def __repr__(self):
        return "Project('%s', '%s', '%s', %s)" % (self.path, self.name, self.desc, self.platform)

class Target(FileSystem):
    """
    Represents a 'target' filesystem that will eventually be installed on the
    target device.
    """
    def __init__(self, name, project, cb):
        if not name or not project:
            raise ValueError("Empty argument passed in")
        self.project = project
        self.name = name
        self.top = os.path.join(project.path, "targets", name)

        # Load our target's filesystem directory
        self.fs_path = os.path.join(self.top, "fs")

        # Load/create our target's image directory
        self.image_path = os.path.join(self.top, "image")
        if not os.path.isdir(self.image_path):
            os.makedirs(self.image_path)

        # Load/create our target's config directory
        self.config_path = os.path.join(self.top, "config")
        if not os.path.isdir(self.config_path):
            os.makedirs(self.config_path)

        # Instantiate the target filesystem
        FileSystem.__init__(self, self.fs_path, cb)

    def installed_fsets(self):
        result = []
        for fset in os.listdir(self.top):
            if fset not in ['fs', 'image', 'config']:
                result.append(fset)
        result.sort()
        return result


    def __list_contains(self, needles, haystack):
        for n in needles:
            if n in haystack:
                return True
        return False

    def __any_fset_installed(self, needles):
        for n in needles:
            if os.path.isfile(os.path.join(self.top, n)):
                return True
        return False

    def installFset(self, fset, debug=0, fsets = None, seen_fsets = None):
        """
        Install a fset into the target filesystem.  If the fsets variable is
        supplied with a list of fsets then we will try to recursively install
        any missing deps that exist.
        """
        if os.path.isfile(os.path.join(self.top, fset.name)):
            raise ValueError("fset %s is already installed!" % (fset.name))

        root_fset = False
        if not seen_fsets:
            print "Installing Function Set: %s (and any dependencies)" % fset.name
            root_fset = True
            seen_fsets = set()
        if fset.name in seen_fsets:
            raise RuntimeError, "Circular fset dependency encountered for: %s" % fset.name
        seen_fsets.add(fset.name)

        package_set = set()
        for dep in fset['deps']:
            if self.__list_contains(dep.split('|'), seen_fsets):
                continue
            if not self.__any_fset_installed(dep.split('|')):
                if fsets:
                    package_set.update(self.installFset(fsets[dep.split('|')[0]], fsets = fsets, debug = debug, seen_fsets = seen_fsets))
                else:
                    raise ValueError("fset %s must be installed first!" % (dep.split('|')[0]))

        package_set.update(fset['pkgs'])
        if debug == 1:
            package_set.update(fset['debug_pkgs'])
        if not root_fset:
            return package_set
        req_fsets = seen_fsets - set( [fset.name] )
        if req_fsets:
            print "Installing required Function Set: %s" % ' '.join(req_fsets)
        self.install("/targets/%s/fs" % (self.name), package_set)
        # and now create a simple empty file that indicates that the fsets has
        # been installed.
        for fset_name in seen_fsets:
            fset_file = open(os.path.join(self.top, fset_name), 'w')
            fset_file.close()

    def install(self, path, packages):
        FileSystem.install(self.project, "/targets/%s/fs" % (self.name), packages)
            
    def update(self):
        FileSystem.update(self.project, "/targets/%s/fs" % (self.name))

    def __str__(self):
        return ("<Target: name=%s, path=%s, fs_path=%s, image_path=%s, config_path=%s>"
                % (self.name, self.path, self.fs_path, self.image_path, self.config_path))
    def __repr__(self):
        return "Target('%s', %s)" % (self.path, self.project)

class Callback:
    def iteration(process):
        return

if __name__ == '__main__':
    if len(sys.argv) != 6:
        print >> sys.stderr, "USAGE: %s PROJECT_NAME PROJECT_PATH PROJECT_DESCRIPTION TARGET_NAME PLATFORM_NAME" % (sys.argv[0])
        print >> sys.stderr, "\tPROJECT_NAME: name to call the project.  The config file /usr/share/pdk/projects/project_name.proj is used or created"
        print >> sys.stderr, "\tPROJECT_PATH: directory to install the project"
        print >> sys.stderr, "\tPROJECT_DESCRIPTION: Textual description of the project"
        print >> sys.stderr, "\tTARGET_NAME: ???"
        print >> sys.stderr, "\tPLATFORM_NAME: The platform.  e.g. donley"
        sys.exit(1)

    name = sys.argv[1]
    install_path = os.path.abspath(os.path.expanduser(sys.argv[2]))
    desc = sys.argv[3]
    target_name = sys.argv[4]
    platform_name = sys.argv[5]

    sdk = SDK.SDK(Callback())

    # verify the platform exists
    if not platform_name in sdk.platforms:
        print >> sys.stderr, "ERROR: %s is not a valid platform!" % (platform_name)
        print >> sys.stderr, "Available platforms include:"
        for key in sorted(sdk.platforms.iterkeys()):
            print "\t%s" % (key)
        sys.exit(1)
    platform = sdk.platforms[platform_name]

    # find an existing project, or create a new one
    existing_project = False
    if name in sdk.projects:
        print "Opening existing project...Using info from config file..."
        proj = sdk.projects[name]
        existing_project = True
    else:
        print "Creating new project..."
        proj = sdk.create_project(install_path, name, desc, platform)
        proj.install()
    print "Install path: %s" % proj.path
    print "Name: %s" % proj.name
    print "Description: %s" % proj.desc
    if existing_project:
        print "Used info from config file: /usr/share/pdk/projects/%s.proj" % name
        time.sleep(2)

    # see if the target exist
    if target_name in proj.targets:
        print "Target already exists: %s" % target_name
        print proj.targets
    else:
        print "Creating new project target filesystem..."
        proj.create_target(target_name)

        print "Installing all available fsets inside target..."
        for key in proj.platform.fset:
            proj.targets[target_name].installFset(proj.platform.fset[key])

