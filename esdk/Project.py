#!/usr/bin/python -tt

import os, sys, yum

from SDK import *
from Platform import *
from stat import *
from shutil import *

class FileSystem:
    """
    This is the base class for any type of a filesystem.  This is used for both
    creating 'jailroot' filesystems that isolate a build from the host Linux
    distribution, and also for creating 'target' filesystems that will
    eventually be transformed into installation images to be
    burned/copied/whatever into the target device.

    By just instantiating a FileSystem object, the caller will trigger the
    basic root filesystem components to be intialized, but to do anything
    usefull with the root filesystem will require the caller to use the
    'install' method for installing new RPM packages.
    """
    def __init__(self, path, repos):
        self.path = os.path.abspath(os.path.expanduser(path))

        if not os.path.isdir(self.path):
            """
            Initial filesystem stub has never been created, so setup the
            initial base directory structure with just enough done to allow yum
            to install packages from outside the root of the filesystem
            """

            # Create our directories
            for dirname in [ 'proc', 'var/log', 'var/lib/rpm', 'dev', 'etc/yum.repos.d' ]:
                full_path = os.path.join(self.path, dirname)
                os.makedirs(full_path)

            target_etc = os.path.join(self.path, "etc")
            for filename in [ 'hosts', 'passwd', 'group', 'resolv.conf' ]:
                copy(os.path.join('/etc', filename), target_etc)
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

            for r in repos:
                copy(r, os.path.join(target_etc, 'yum.repos.d'))

            os.system('sudo mknod ' + os.path.join(self.path, 'dev/null') + ' c 1 3')
            os.system('sudo mknod ' + os.path.join(self.path, 'dev/zero') + ' c 1 5')

    def install(self, path, packages, repos):
        """
        Call into yum to install RPM packages using the specified yum
        repositories
        """
        command = 'sudo yum -y --disablerepo=* --enablerepo=esdk* --installroot=' + path + ' install '
        for p in packages:
            command = command + ' ' + p
        os.system(command)

    def mount(self):
        os.system('mount --bind /proc ' + os.path.join(self.path, 'proc'))

    def umount(self):
        os.system('umount ' + os.path.join(self.path, 'proc'))


class Project(FileSystem):
    """
    A Project is a type of  'jailroot' filesystem that is used to isolate the
    build system from the host Linux distribution.  It also knows how to create
    new 'target' filesystems.
    """
    def __init__(self, path, name, platform):
        self.path = os.path.abspath(os.path.expanduser(path))
        self.name = name
        self.platform = platform
        FileSystem.__init__(self, self.path, self.platform.buildroot_repos)

        # Create our targets directory
        targets_path = os.path.join(self.path, 'targets')
        if not os.path.isdir(targets_path):
            os.makedirs(targets_path)

        # Instantiate all targets
        self.targets = {}
        for dirname in os.listdir(targets_path):
            target = Target(dirname, self)
            self.targets[target.name] = target

    def install(self):
        """
        Install all the packages defined by Platform.jailroot_packages
        """
        FileSystem.install(self, self.path, self.platform.jailroot_packages, self.platform.buildroot_repos)

    def create_target(self, name):
        if not self.targets.has_key(name):
            self.targets[name] = Target(name, self)

    def __str__(self):
        return ("<Project: name=%s, path=%s>"
                % (self.name, self.path))

class Target(FileSystem):
    """
    Represents a 'target' filesystem that will eventually be installed on the
    target device.
    """
    def __init__(self, name, project):
        self.project = project
        self.name = name
        self.path = os.path.join(project.path, "targets", name)


        # Load our target's filesystem directory
        self.fs_path = os.path.join(self.path, "fs")

        # Load/create our target's image directory
        self.image_path = os.path.join(self.path, "image")
        if not os.path.isdir(self.image_path):
            os.makedirs(self.image_path)

        # Instantiate the target filesystem
        FileSystem.__init__(self, self.fs_path, project.platform.target_repos)

    def install(self, fset, debug=0):
        """
        Install a fset into the target filesystem
        """
        FileSystem.install(self, self.fs_path, fset['pkgs'], self.project.platform.buildroot_repos)
        if debug == 1:
            FileSystem.install(self, self.fs_path, fset['debug_pkgs'], self.project.platform.buildroot_repos)

    def __str__(self):
        return ("<Target: name=%s, path=%s, fs_path=%s, image_path>"
                % (self.name, self.path, self.fs_path, self.image_path))


if __name__ == '__main__':
    if len(sys.argv) != 6:
        print >> sys.stderr, "USAGE: %s PROJECT_NAME PROJECT_PATH PROJECT_DESCRIPTION PLATFORM_NAME TARGET_NAME" % (sys.argv[0])
        sys.exit(1)

    name = sys.argv[1]
    path = sys.argv[2]
    desc = sys.argv[3]
    target_name = sys.argv[4]
    platform_name = sys.argv[5]
    
    sdk = SDK()

    # verify the platform exist
    if not sdk.platforms.has_key(platform_name):
        print >> sys.stderr, "ERROR: %s is not a valid platform!" % (platform_name)
        print >> sys.stderr, "Available platforms include:"
        for key in sdk.platforms.keys():
            print "\t%s" % (key)
        sys.exit(1)
        
    platform = sdk.platforms[platform_name]
        
    # find an existing project, or create a new one
    if sdk.projects.has_key(sys.argv[1]):
        print "Opening existing project..."
        proj = sdk.projects[name]
    else:
        print "Creating new project..."
        proj = sdk.create_project(path, name, desc, platform)
        proj.install()

    # see if the target exist
    if proj.targets.has_key(target_name):
        print "Target already exists"
    else:
        print "Creating new project target filesystem..."
        proj.create_target(target_name)

        print "Installing all available fsets inside target..."
        for key in proj.platform.fset.fsets.keys():
            proj.targets[target_name].install(proj.platform.fset[key])
