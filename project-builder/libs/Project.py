#!/usr/bin/python -tt
# vim: ai ts=4 sts=4 et sw=4

import glob
import os
import re
import shutil
import socket
import stat
import subprocess
import sys
import time

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
    def __init__(self, path, repos, cb):
        if not path or not repos:
            raise ValueError("Empty argument passed in")
        self.cb = cb
        self.path = os.path.abspath(os.path.expanduser(path))
        try:
            print "FileSystem(%s, %s)" % (path, repos)
            self.__createBase(path, repos)
            self.__createDevices()
        except:
            print >> sys.stderr, "%s" % (sys.exc_value)
            pass

    def __createBase(self, path, repos):
        for dirname in [ 'proc', 'var/log', 'var/lib/rpm', 'dev', 'etc/yum.repos.d' ]:
            os.makedirs(os.path.join(path, dirname))
        target_etc = os.path.join(path, "etc")
        for filename in [ 'hosts', 'resolv.conf' ]:
            shutil.copy(os.path.join('/etc', filename), target_etc)
        yumconf = open(os.path.join(target_etc, 'yum.conf'), 'w')
        print >> yumconf, """\
[main]
cachedir=/var/cache/yum
keepcache=0
debuglevel=2
logfile=/var/log/yum.log
pkgpolicy=newest
distroverpkg=redhat-release
tolerant=1
exactarch=1
obsoletes=1
gpgcheck=0
plugins=1
metadata_expire=1800
"""
        yumconf.close()
        for repo in repos:
            shutil.copy(repo, os.path.join(target_etc, 'yum.repos.d'))

    def __createDevices(self):
        devices = [
            # name, major, minor, mode
            ('console', 5, 1, (0600 | stat.S_IFCHR)),
            ('null',    1, 3, (0666 | stat.S_IFCHR)),
            ('random',  1, 8, (0666 | stat.S_IFCHR)),
            ('urandom', 1, 9, (0444 | stat.S_IFCHR)),
            ('zero',    1, 5, (0666 | stat.S_IFCHR)),
        ]
        for device_name, major, minor, mode in devices:
            device_path = os.path.join(self.path, 'dev', device_name)
            device = os.makedev(major, minor)
            os.mknod(device_path, mode, device)
            # Seems redundant, but mknod doesn't seem to set the mode to
            # what we want :(
            os.chmod(device_path, mode)

    def update(self, path):
        command = '-y --installroot=%s update' % (path)
        ret = self.chroot("/usr/bin/yum", command) 
        if ret != 0:
            raise OSError("Internal error while attempting to run: %s" % command)


    def install(self, path, packages):
        """
        Call into yum to install RPM packages using the specified yum
        repositories
        """
        if not packages:
            # No packages, so nothing to do
            return
        command = '-y --installroot=%s install ' % (path)
        for p in packages:
            command += ' %s' % p
        ret = self.chroot("/usr/bin/yum", command) 
        if ret != 0:
            raise OSError("Internal error while attempting to run: %s" % command)

    def mount(self):
        path = os.path.join(self.path, 'proc')
        if not os.path.ismount(path):
            result = os.system('mount --bind /proc ' + path + ' 2> /dev/null')
            if result != 0:
                raise OSError("Internal error while attempting to mount proc filesystem!")

        # search for any file:// URL's in the configured yum repositories, and
        # when we find them make the equivilant directory in the new filesystem
        # and then mount --bind the file:// path into the filesystem.
        rdir = os.path.join(self.path, 'etc', 'yum.repos.d')
        if os.path.isdir(rdir):
            for fname in os.listdir(rdir):
                file = open(os.path.join(rdir, fname))
                for line in file:
                    if re.search(r'^\s*baseurl=file:\/\/\/', line):
                        p = line.split('baseurl=file:///')[1].strip()
                        os.makedirs(os.path.join(self.path, p))
                        result = os.system("mount --bind /%s %s 2> /dev/null" % (p, os.path.join(self.path, p)))
                        if result != 0:
                            self.umount()
                            raise OSError("Internal error while attempting to mount /%s!" % (p))
                file.close()
                
    def umount(self):
        for line in os.popen('mount', 'r').readlines():
            mpoint = line.split()[2]
            if self.path == mpoint[:len(self.path)]:
                os.system("umount %s" % (mpoint))

    def chroot(self, cmd_path, cmd_args):
        print "self.chroot(%s, %s)" % (cmd_path, cmd_args)
        if not os.path.isfile(os.path.join(self.path, 'bin/bash')):
            print >> sys.stderr, "Incomplete jailroot at %s" % (self.path)
            raise ValueError("Internal Error: Invalid buildroot at %s" % (self.path))
        self.mount()
        cmd_line = "chroot %s %s %s" % (self.path, cmd_path, cmd_args)
        p = subprocess.Popen(cmd_line.split())
        while p.poll() == None:
            try: 
                self.cb.iteration(process=p)
            except:
                pass
        return p.returncode

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
        FileSystem.__init__(self, self.path, self.platform.buildroot_repos, cb)

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
            self.targets[name] = Target(name, self, self.cb)
            self.targets[name].mount()
        return self.targets[name]

    def delete_target(self, name):
        target = self.targets[name]
        target.umount()
        shutil.rmtree(os.path.join(self.path, 'targets', name))

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

        # Instantiate the target filesystem
        FileSystem.__init__(self, self.fs_path, project.platform.target_repos, cb)

    def installed_fsets(self):
        result = []
        for fset in os.listdir(self.top):
            if fset not in ['fs', 'image']:
                result.append(fset)
        result.sort()
        return result

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
            if dep in seen_fsets:
                continue
            if not os.path.isfile(os.path.join(self.top, dep)):
                if fsets:
                    package_set.update(self.installFset(fsets[dep], fsets = fsets, debug = debug, seen_fsets = seen_fsets))
                else:
                    raise ValueError("fset %s must be installed first!" % (dep))

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
        return ("<Target: name=%s, path=%s, fs_path=%s, image_path=%s>"
                % (self.name, self.path, self.fs_path, self.image_path))
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

