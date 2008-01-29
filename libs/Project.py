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

import mic_cfg
import moblin_pkg
import pdk_utils
import InstallImage
import SDK

debug = False
if mic_cfg.config.has_option('general', 'debug'):
    debug = int(mic_cfg.config.get('general', 'debug'))

# This is here for the testing of the new package manager code
USE_NEW_PKG = False
if mic_cfg.config.has_option('general', 'use_new_pkg'):
    USE_NEW_PKG = int(mic_cfg.config.get('general', 'use_new_pkg'))

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
    'installPackages' method for installing new RPM packages.
    """
    def __init__(self, path, progress_callback = None):
        if not path:
            raise ValueError("Empty argument passed in")
        self.progress_callback = progress_callback
        self.path = os.path.realpath(os.path.abspath(os.path.expanduser(path)))
        self.mounted = []

    def updateAndUpgrade(self):
        self.mount()
        return self.platform.pkg_manager.updateChroot(self.chroot_path,
            callback = self.progress_callback)
        
    def installPackages(self, packages_list):
        self.mount()
        return self.platform.pkg_manager.installPackages(self.chroot_path,
            packages_list, callback = self.progress_callback)

    def chroot(self, cmd, output = None):
        if not os.path.isfile(os.path.join(self.chroot_path, 'bin/bash')):
            print >> sys.stderr, "Incomplete jailroot at %s" % (self.chroot_path)
            raise ValueError("Internal Error: Invalid buildroot at %s" % (self.chroot_path))
        self.mount()
        if output == None:
            output = []
        result = pdk_utils.execChrootCommand(self.chroot_path, cmd, output = output, callback = self.progress_callback)
        if result != 0:
            print "Error in chroot command exec.  Result: %s" % result
            print "Command was: %s" % cmd
            print "chroot was: %s" % self.chroot_path
            sys.stdout.flush()
        return result

    mount_list = [
        # mnt_type, host_dirname, target_dirname, fs_type, device
        ('bind', '/tmp', False, None, None),
        ('bind', '/usr/share/pdk', False, None, None),
        ('host', '/dev/pts', 'dev/pts', 'devpts', 'devpts'),
        ('host', '/proc', False, 'proc', 'proc'),
        ('host', '/sys', False, 'sysfs', 'sysfs'),
    ]

    def mount(self):
        # We want to keep a list of everything we mount, so that we can use it
        # in the umount portion
        self.mounted = pdk_utils.mountList(FileSystem.mount_list, self.chroot_path)
        self.mounted.extend(self.platform.pkg_manager.mount(self.chroot_path))
        # Setup copies of some useful files from the host into the chroot
        for filename in ['etc/resolv.conf', 'etc/hosts']:
            source_file = os.path.join(os.sep, filename)
            target_file = os.path.join(self.chroot_path, filename)
            # Let's only copy if they don't already exist
            if os.path.isfile(source_file) and not os.path.isfile(target_file):
                shutil.copy(source_file, target_file)
        # first time mount
        buildstamp_path = os.path.join(self.path, 'etc', 'buildstamp')
        if not os.path.isfile(buildstamp_path):
            buildstamp = open(buildstamp_path, 'w')
            print >> buildstamp, "%s %s" % (socket.gethostname(), time.strftime("%d-%m-%Y %H:%M:%S %Z"))
            buildstamp.close()

    def umount(self):
        # Go through all the mount points that we recorded during the mount
        # function
        for mount_point in self.mounted:
            if os.path.exists(mount_point):
                result = os.system("umount %s" % (mount_point))
                if result:
                    # If error, return failure along with directory name of failure
                    return (False, mount_point)
        return pdk_utils.umountAllInPath(self.path)

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
        self.chroot_path = self.path
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
        return super(Project, self).installPackages(self.platform.buildroot_packages + self.platform.buildroot_extras)

    def umount(self):
        """We want to umount all of our targets and then anything in our project that we have mounted"""
        for target_name in self.targets:
            target = self.targets[target_name]
            result, dirname = target.umount()
            if not result:
                return result, dirname
        return FileSystem.umount(self)

    def create_target(self, name, use_rootstrap = True):
        if not name:
            raise ValueError("Target name was not specified")
        if not name in self.targets:
            install_path = os.path.join(self.path, 'targets', name, 'fs')
            self.platform.createChroot(install_path, callback = self.progress_callback)

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

    def delete_target(self, name, do_pop=True, callback = None):
        target = self.targets[name]
        result, dirname = target.umount()
        if not result:
            raise RuntimeError, "Could not unmount dir: %s" % dirname
        seen_paths = []
        while True:
            try:
                pdk_utils.rmtree(os.path.join(self.path, 'targets', name), callback = callback)
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
        result, dirname = target.umount()
        if not result:
            raise RuntimeError, "Could not unmount dir: %s" % dirname
        image = InstallImage.LiveIsoImage(self, self.targets[target_name], image_name, progress_callback = self.progress_callback)
        image.create_image()
        target.mount()

    def create_install_iso(self, target_name, image_name):
        target = self.targets[target_name]
        result, dirname = target.umount()
        if not result:
            raise RuntimeError, "Could not unmount dir: %s" % dirname
        image = InstallImage.InstallIsoImage(self, self.targets[target_name], image_name, progress_callback = self.progress_callback)
        image.create_image()
        target.mount()

    def create_live_usb(self, target_name, image_name, type="RAMFS"):
        target = self.targets[target_name]
        result, dirname = target.umount()
        if not result:
            raise RuntimeError, "Could not unmount dir: %s" % dirname
        image = InstallImage.LiveUsbImage(self, self.targets[target_name], image_name, progress_callback = self.progress_callback)
        image.create_image(type)
        target.mount()

    def create_install_usb(self, target_name, image_name):
        target = self.targets[target_name]
        result, dirname = target.umount()
        if not result:
            raise RuntimeError, "Could not unmount dir: %s" % dirname
        image = InstallImage.InstallUsbImage(self, self.targets[target_name], image_name, progress_callback = self.progress_callback)
        image.create_image()
        target.mount()

    def tar(self, tar_obj):
        """tar up the project.  Need to pass in a tarfile object"""
        result, dirname = self.umount()
        if not result:
            raise RuntimeError, "Could not unmount dir: %s" % dirname
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
        self.platform = project.platform
        self.top = os.path.join(project.path, "targets", name)

        # Load our target's filesystem directory
        self.fs_path = os.path.join(self.top, "fs")
        self.chroot_path = self.fs_path

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

    def __any_fset_installed(self, fset_list):
        """See if we have already installed the fset"""
        for fset_name in fset_list:
            if os.path.isfile(os.path.join(self.top, fset_name)):
                return True
        return False

    def installFset(self, fset, debug_pkgs = 0, fsets = None, seen_fsets = None):
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
            # An fset "DEP" value can contain a dependency list of the form:
            #   DEP=A B|C
            # Which means the fset depends on fset A and either fset B or C.
            # If B or C are not installed then it will attempt to install the
            # first one (fset B).
            dep_list = dep.split('|')
            if seen_fsets.intersection(dep_list):
                # If any of the fsets we have already seen satisfy the
                # dependency, then continue
                continue
            if not self.__any_fset_installed(dep_list):
                if fsets:
                    # Determine which fsets are needed to install the required fset
                    package_set.update(self.installFset(fsets[dep_list[0]],
                        fsets = fsets, debug_pkgs = debug_pkgs, seen_fsets = seen_fsets))
                else:
                    raise ValueError("fset %s must be installed first!" % (dep_list[0]))

        package_set.update(fset['pkgs'])
        if debug_pkgs == 1:
            package_set.update(fset['debug_pkgs'])
        if not root_fset:
            return package_set
        else:
            req_fsets = seen_fsets - set( [fset.name] )
            if req_fsets:
                print "Installing required Function Set: %s" % ' '.join(req_fsets)
            self.installPackages(package_set)
            # and now create a simple empty file that indicates that the fsets has
            # been installed.
            for fset_name in seen_fsets:
                fset_file = open(os.path.join(self.top, fset_name), 'w')
                fset_file.close()

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

