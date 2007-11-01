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

import errno
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
    def __init__(self, path, progress_callback = None):
        if not path:
            raise ValueError("Empty argument passed in")
        self.progress_callback = progress_callback
        self.path = os.path.realpath(os.path.abspath(os.path.expanduser(path)))
        self.apt_cmd = '/usr/bin/apt-get -y --force-yes -o Dir::State=%(t)s/var/lib/apt -o Dir::State::status=%(t)s/var/lib/dpkg/status -o Dir::Cache=/var/cache/apt -o Dir::Etc=%(t)s/etc/apt/ -o DPkg::Options::=--root=%(t)s -o DPkg::Run-Directory=%(t)s'
        self.mounted = []

    def update(self):
        self.aptgetPreCheck()
        command = self.apt_cmd % {'t': self.path} + " update"
        command = "apt-get update"
        print "Running 'apt-get update' command: '%s' in chroot: %s " % (command, self.path)
        ret = self.chroot(command) 
        if ret != 0:
            raise OSError("Internal error while attempting to run: %s" % command)
        print "Completed 'apt-get update' successfully"
        
    def upgrade(self):
        self.aptgetPreCheck()
        command = self.apt_cmd % {'t': self.path} + " upgrade"
        command = "apt-get upgrade"
        print "Running 'apt-get upgrade' command: %s in chroot: %s" % (command, self.path)
        ret = self.chroot(command) 
        if ret != 0:
            raise OSError("Internal error while attempting to run: %s" % command)
        print "Completed 'apt-get upgrade' successfully"

    def updateAndUpgrade(self):
        self.update()
        self.upgrade()
        
    def install(self, path, packages):
        debian_frontend = os.environ.get("DEBIAN_FRONTEND")
        if debian_frontend == None:
            debian_frontend = ""
        os.environ['DEBIAN_FRONTEND'] = 'noninteractive'
        self.aptgetPreCheck()
        if not packages:
            # No packages, so nothing to do
            return
        retry_count = 0
        while (retry_count < 10):
            self.updateAndUpgrade()
            # apt-get install
            command = self.apt_cmd % {'t': path} + " install"
            for p in packages:
                command += ' %s' % p
            print "Running 'apt-get install' command: %s" % command
            ret = self.chroot(command) 
            if ret == 0:
                print "Completed 'apt-get install' successfully"
                break
            print
            print "Error running 'apt-get install' command: %s" % command
            print "Will try 'apt-get update' in 15 seconds"
            time.sleep(15)
            retry_count = retry_count + 1
            # apt-get update
            command = self.apt_cmd % {'t': path} + " update"
            print "Running 'apt-get update' command: %s" % command
            result = self.chroot(command)
            if result != 0:
                print
                print "Error running 'apt-get update' command: %s" % command
                print "Will try 'apt-get install' in 15 seconds"
                time.sleep(15)
            else:
                print "Completed 'apt-get update' successfully"
                print "Will try 'apt-get install -f' in 15 seconds"
                time.sleep(15)
            # apt-get install -f
            command = self.apt_cmd % {'t': path} + " install -f"
            ret = self.chroot(command) 
            if result != 0:
                print
                print "Error running 'apt-get install -f' command: %s" % command
                print "Will try 'apt-get install' in 15 seconds"
                time.sleep(15)
            else:
                print "Completed 'apt-get install -f' successfully"
                print "Will try 'apt-get install' in 15 seconds"
                time.sleep(15)
        else:
            raise OSError("Internal error while attempting to run: %s" % command)
        os.environ['DEBIAN_FRONTEND'] = debian_frontend

    def aptgetPreCheck(self):
        """Stuff that we want to check for before we run an apt-get command"""
        required_dirs = [ "/var/cache/apt/archives/partial" ]
        for dirname in required_dirs:
            if not os.path.isdir(dirname):
                print "The directory: %s is missing, will create it" % dirname
                os.makedirs(dirname)

    mount_list = [
        # mnt_type, host_dirname, target_dirname, fs_type, device
        ('bind', '/tmp', False, None, None),
        ('bind', '/usr/share/pdk', False, None, None),
        ('bind', '/var/cache/apt/archives', False, None, None),
        ('host', '/dev/pts', 'dev/pts', 'devpts', 'devpts'),
        ('host', '/proc', False, 'proc', 'proc'),
        ('host', '/sys', False, 'sysfs', 'sysfs'),
    ]

    def mount(self):
        # We want to keep a list of everything we mount, so that we can use it
        # in the umount portion
        self.mounted = []
        mounts = pdk_utils.getMountInfo()
        for mnt_type, host_dirname, target_dirname, fs_type, device in FileSystem.mount_list:
            # If didn't specify target_dirname then use the host_dirname path,
            # but we have to remove the leading '/'
            if not target_dirname and host_dirname:
                target_dirname = re.sub(r'^' + os.sep, '', host_dirname)

            # Do the --bind mount types
            if mnt_type == "bind":
                path = os.path.join(self.path, target_dirname)
                self.mounted.append(path)
                if not os.path.isdir(path):
                    os.makedirs(path)
                if not pdk_utils.ismount(path) and os.path.isdir(host_dirname):
                    result = os.system('mount --bind %s %s' % (host_dirname, path))
                    if result != 0:
                        raise OSError("Internal error while attempting to bind mount /%s!" % (mnt))
            # Mimic host mounts, if possible
            elif mnt_type == 'host':
                if host_dirname in mounts:
                    mount_info = mounts[host_dirname]
                    fs_type = mount_info.fs_type
                    device = mount_info.device
                    options = "-o %s" % mount_info.options
                else:
                    options = ""
                path = os.path.join(self.path, target_dirname)
                self.mounted.append(path)
                if not os.path.isdir(path):
                    os.makedirs(path)
                if not pdk_utils.ismount(path):
                    cmd = 'mount %s -t %s %s %s' % (options, fs_type, device, path)
                    result = pdk_utils.execCommand(cmd)
                    if result != 0:
                        raise OSError("Internal error while attempting to mount %s %s!" % (host_dirname, target_dirname))
        # Setup copies of some useful files from the host into the chroot
        for file in ['etc/resolv.conf', 'etc/hosts']:
            if os.path.isfile(os.path.join('/', file)):
                shutil.copy(os.path.join('/', file), os.path.join(self.path, file))

        if os.path.isfile(os.path.join(self.path, '.buildroot')):
            # search for any file:// URL's in the configured apt repositories, and
            # when we find them make the equivalent directory in the new filesystem
            # and then mount --bind the file:// path into the filesystem.
            rdir = os.path.join(self.path, 'etc', 'apt', 'sources.list.d')
            if os.path.isdir(rdir):
                for fname in os.listdir(rdir):
                    file = open(os.path.join(rdir, fname))
                    for line in file:
                        if re.search(r'^\s*deb file:\/\/\/', line):
                            p = line.split('file:///')[1].split(' ')[0]
                            new_mount = os.path.join(self.path, p)
                            self.mounted.append(new_mount)
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
            self.chroot("/usr/bin/apt-get update")
                
    def umount(self):
        # Go through all the mount points that we recorded during the mount
        # function
        for mount_point in self.mounted:
            os.system("umount %s" % (mount_point))
        # Have to add a '/' on the end to prevent /foo/egg and /foo/egg2 being
        # treated as if both were under /foo/egg
        our_path = os.path.realpath(os.path.abspath(self.path)) + os.sep
        mounts = pdk_utils.getMountInfo()
        for mpoint in mounts:
            mpoint = os.path.realpath(os.path.abspath(mpoint)) + os.sep
            if our_path == mpoint[:len(our_path)]:
                os.system("umount %s" % (mpoint))

    def chroot(self, cmd, output = None):
        if not os.path.isfile(os.path.join(self.path, 'bin/bash')):
            print >> sys.stderr, "Incomplete jailroot at %s" % (self.path)
            raise ValueError("Internal Error: Invalid buildroot at %s" % (self.path))
        self.mount()
        self.disable_init_scripts()
        if output == None:
            output = []
        cmd_line = "chroot %s %s" % (self.path, cmd)
        result = pdk_utils.execCommand(cmd_line, output = output, callback = self.progress_callback)
        if result != 0:
            print "Error in chroot.  Result: %s" % result
            print "Command was: %s" % cmd_line
            sys.stdout.flush()
        return result

    def disable_init_scripts(self):
        # In debian if we have the file /usr/sbin/policy-rc.d, which just
        # return the value 101.  Then package postinstall scripts are not
        # supposed to run.
        # http://people.debian.org/~hmh/invokerc.d-policyrc.d-specification.txt
        filename = os.path.join(self.path, "usr/sbin/policy-rc.d")
        if not os.path.exists(filename):
            out_file = open(filename, 'w')
            print >> out_file, "#!/bin/sh"
            print >> out_file, "exit 101"
            out_file.close()
        os.chmod(filename, 0755)

class Project(FileSystem):
    """
    A Project is a type of  'jailroot' filesystem that is used to isolate the
    build system from the host Linux distribution.  It also knows how to create
    new 'target' filesystems.
    """
    def __init__(self, path, name, desc, platform, progress_callback = None):
        if not path or not name or not desc or not platform:
            raise ValueError("Empty argument passed in")
        self.path = os.path.realpath(os.path.abspath(os.path.expanduser(path)))
        self.name = name
        self.platform = platform
        self.desc = desc
        self.progress_callback = progress_callback
        FileSystem.__init__(self, self.path, progress_callback = progress_callback)

        # Create our targets directory
        targets_path = os.path.join(self.path, 'targets')
        if not os.path.isdir(targets_path):
            os.makedirs(targets_path)

        # Instantiate all targets
        self.targets = {}
        for dirname in os.listdir(targets_path):
            target = Target(dirname, self, self.progress_callback)
            self.targets[target.name] = target

    def install(self):
        """
        Install all the packages defined by Platform.buildroot_packages
        """
        FileSystem.install(self, "/", self.platform.buildroot_packages)

    def umount(self):
        """We want to umount all of our targets and then anything in our project that we have mounted"""
        for target_name in self.targets:
            target = self.targets[target_name]
            target.umount()
        FileSystem.umount(self)

    def create_target(self, name, use_rootstrap = True):
        if not name:
            raise ValueError("Target name was not specified")
        if not name in self.targets:
            count =  0
            install_path = os.path.join(self.path, 'targets', name, 'fs')
            os.makedirs(install_path)
            rootstrap = os.path.join(self.platform.path, "target-rootstrap.tar.bz2")
            if not os.path.isfile(rootstrap) or not use_rootstrap:
                cmd = "debootstrap --arch %s --include=apt %s %s %s" % (self.platform.architecture, self.platform.target_codename, install_path, self.platform.target_mirror)
                output = []

                # XXX Evil hack
                if not os.path.isfile("/usr/lib/debootstrap/scripts/%s" % self.platform.target_codename):
                    cmd += " /usr/share/pdk/debootstrap-scripts/%s" % self.platform.target_codename

                # Sometimes we see network issues that trigger debootstrap
                # to claim the apt repository is corrupt.  This trick will
                # force up to 10 attempts before bailing out with an error
                while count < 10:
                    count += 1
                    print "--------Target rootstrap creation try: %s ----------" % count
                    result = pdk_utils.execCommand(cmd, output = output, callback = self.progress_callback)
                    if result == 0:
                        print "--------Target rootstrap creation completed successfully----------"
                        break;
                    print "--------Target rootstrap creation failed result: %s ----------" % result
                    sleeptime = 30
                    print "--------For try: %s.  Sleeping for %s seconds... -----------------" % (count, sleeptime)
                    time.sleep(sleeptime)
                if result != 0:
                    print >> sys.stderr, "ERROR: Unable to generate target rootstrap!"
                    raise ValueError(" ".join(output))
                pdk_utils.execChrootCommand(install_path, 'apt-get clean')

                # workaround for ubuntu kernel package bug
                os.system('touch %s/etc/kernel-img.conf' % (install_path))
                os.system('touch %s/etc/kernel-pkg.conf' % (install_path))
               
                source_dir = os.path.join(self.platform.path, 'sources')
                for f in os.listdir(source_dir):
                    source_path = os.path.join(source_dir, f)
                    dest_path = os.path.join(install_path, 'etc', 'apt', 'sources.list.d', f)
                    pdk_utils.copySourcesListFile(source_path, dest_path)
#                    shutil.copy(source_path, os.path.join(install_path, 'etc', 'apt', 'sources.list.d'))
                source_path = os.path.join(self.platform.path, 'preferences')
                if os.path.exists(source_path):
                    shutil.copy(source_path, os.path.join(install_path, 'etc', 'apt'))
                if use_rootstrap:
                    cmd = "tar -jcpvf %s -C %s ." % (rootstrap, install_path)
                    output = []
                    result = pdk_utils.execCommand(cmd, output = output, callback = self.progress_callback)
                    if result != 0:
                        print >> sys.stderr, "ERROR: Unable to archive rootstrap!"
                        shutil.rmtree(install_path)
                        raise ValueError(" ".join(output))
            else:
                cmd = "tar -jxvf %s -C %s" % (rootstrap, install_path)
                output = []
                result = pdk_utils.execCommand(cmd, output = output, callback = self.progress_callback)
                if result != 0:
                    print >> sys.stderr, "ERROR: Unable to rootstrap %s from %s!" % (rootstrap, name)
                    shutil.rmtree(os.path.join(self.path, 'targets', name))
                    raise ValueError(" ".join(output))

            self.targets[name] = Target(name, self, self.progress_callback)
            self.targets[name].mount()
            self.targets[name].updateAndUpgrade()
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
        seen_paths = []
        while True:
            try:
                shutil.rmtree(os.path.join(self.path, 'targets', name))
                break
            except OSError, e:
                # See if we get a resource busy error, if so we think it is a
                # mounted filesystem issue
                if e.errno == errno.EBUSY:
                    if e.filename in seen_paths:
                        raise OSError, e
                    else:
                        seen_paths.append(e.filename)
                        os.system("umount %s" % (e.filename))
                else:
                    raise OSError, e
        if do_pop:
            self.targets.pop(name)
        
    def create_live_iso(self, target_name, image_name):
        target = self.targets[target_name]
        target.umount()
        image = InstallImage.LiveIsoImage(self, self.targets[target_name], image_name, progress_callback = self.progress_callback)
        image.create_image()
        target.mount()

    def create_install_iso(self, target_name, image_name):
        target = self.targets[target_name]
        target.umount()
        image = InstallImage.InstallIsoImage(self, self.targets[target_name], image_name, progress_callback = self.progress_callback)
        image.create_image()
        target.mount()

    def create_live_usb(self, target_name, image_name, type="RAMFS"):
        target = self.targets[target_name]
        target.umount()
        image = InstallImage.LiveUsbImage(self, self.targets[target_name], image_name, progress_callback = self.progress_callback)
        image.create_image(type)
        target.mount()

    def create_install_usb(self, target_name, image_name):
        target = self.targets[target_name]
        target.umount()
        image = InstallImage.InstallUsbImage(self, self.targets[target_name], image_name, progress_callback = self.progress_callback)
        image.create_image()
        target.mount()

    def tar(self, tar_obj):
        """tar up the project.  Need to pass in a tarfile object"""
        self.umount()
        tar_obj.add(self.path, arcname = "project/")

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
    def __init__(self, name, project, progress_callback = None):
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
        FileSystem.__init__(self, self.fs_path, progress_callback = progress_callback)

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
    install_path = os.path.realpath(os.path.abspath(os.path.expanduser(sys.argv[2])))
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

