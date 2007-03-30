#!/usr/bin/python -tt
# vim: ai ts=4 sts=4 et sw=4

import os, shutil, stat, sys, time, socket

import SDK
import InstallImage

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
    def __init__(self, path, repos):
        self.ismounted = 0
        
        self.path = os.path.abspath(os.path.expanduser(path))
        if not os.path.isfile(os.path.join(self.path, 'etc', 'buildstamp')):
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
            # Create our devices
            self.__createDevices()

            # create a build timestamp file
            buildstamp = open(os.path.join(target_etc, 'buildstamp'), 'w')
            print >> buildstamp, "%s %s-%s" % (SDK.SDK().version, socket.gethostname(), time.strftime("%d%m%Y%Z%H%M%s"))
            buildstamp.close()
            
    def __createDevices(self):
            devices = [
                # name, major, minor, mode
                ('null', 1, 3, (0666 | stat.S_IFCHR)),
                ('zero', 1, 5, (0666 | stat.S_IFCHR)),
                ('console', 5, 1, (0600 | stat.S_IFCHR)),
            ]
            for device_name, major, minor, mode in devices:
                device_path = os.path.join(self.path, 'dev', device_name)
                device = os.makedev(major, minor)
                os.mknod(device_path, mode, device)
                # Seems redundant, but mknod doesn't seem to set the mode to
                # what we want :(
                os.chmod(device_path, mode)

    def update(self, path):
        result = os.system("yum -y --installroot=%s update" % (path))
        if result != 0:
            raise Exception("Internal error while attempting to update!")
        
        self.__rebuild_rpmlist(path)

    def install(self, path, packages):
        """
        Call into yum to install RPM packages using the specified yum
        repositories
        """
        command = 'yum -y --installroot=' + path + ' install '
        for p in packages:
            command = command + ' ' + p
        result = os.system(command)
        if result != 0:
            raise Exception("Internal error while attempting to install!")
        
        self.__rebuild_rpmlist(path)
        
    def __rebuild_rpmlist(self, path):
        root_path = os.path.abspath(path)
        BASE_RPM_LIST = "/etc/base-rpms.list"
        command = 'rpm -r %s -qa > %s%s' % (root_path, root_path, BASE_RPM_LIST)
        result = os.system(command)
        if result != 0:
            raise Exception("Internal error while attempting to build package list!")

        # Since we are using yum from the host machine, if this is a
        # 64bit machine then yum produces 64bit database indexes, while
        # our chroot runtime is 32bit.  To keep the target from chroot's
        # 32bit rpm from chocking on the 64bit index, we rebuild the
        # index from inside the chroot.
        # TODO: there has got to be a better way of doing this
        if os.uname()[4] == "x86_64":
            # regenerate the rpmdb.  needed for x86_64 system.
            command = "rm -rf %s%s" % (root_path, "/var/lib/rpm/__*")
            result = os.system(command)
            if result != 0:
                raise Exception("Internal error while attempting to rebuild package database!")
            
            self.chroot('rpm', '--rebuilddb -v -v')

    def mount(self):
        path = os.path.join(self.path, 'proc')
        if not os.path.ismount(path):
            result = os.system('mount --bind /proc ' + path + ' 2> /dev/null')
            if result != 0:
                raise Exception("Internal error while attempting to mount proc filesystem!")
        self.ismounted = 1

    def umount(self):
        for line in os.popen('mount', 'r').readlines():
            mpoint = line.split()[2]
            if self.path == mpoint[:len(self.path)]:
                result = os.system("umount %s" % (mpoint))
                if result != 0:
                    raise Exception("Internal error while attempting to umount!")
        self.ismounted = 0

    def chroot(self, cmd_path, cmd_args):
        if not os.path.isfile(os.path.join(self.path, 'bin/bash')):
            raise ValueError, "Jailroot not installed"
        
        self.mount()
        cmd_line = "chroot %s %s %s" % (self.path, cmd_path, cmd_args)
        ret = os.system(cmd_line)
        self.umount()
        return ret

class Project(FileSystem):
    """
    A Project is a type of  'jailroot' filesystem that is used to isolate the
    build system from the host Linux distribution.  It also knows how to create
    new 'target' filesystems.
    """
    def __init__(self, path, name, desc, platform):
        self.path = os.path.abspath(os.path.expanduser(path))
        self.name = name
        self.platform = platform
        self.desc = desc
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
        FileSystem.install(self, self.path, self.platform.jailroot_packages)

    def update(self):
        FileSystem.update(self, self.path)
        
    def create_target(self, name):
        if name and not name in self.targets:
            self.targets[name] = Target(name, self)
        return self.targets[name]

    def delete_target(self, name):
        target = self.targets[name]
        target.umount()
        shutil.rmtree(os.path.join(self.path, 'targets', name))

    def create_live_iso(self, target_name, image_name):
        image = InstallImage.LiveIsoImage(self, self.targets[target_name], image_name)
        image.create_image()
        
    def create_install_iso(self, target_name, image_name):
        image = InstallImage.InstallIsoImage(self, self.targets[target_name], image_name)
        image.create_image()

    def create_live_usb(self, target_name, image_name):
        image = InstallImage.LiveUsbImage(self, self.targets[target_name], image_name)
        image.create_image()

    def create_install_usb(self, target_name, image_name):
        image = InstallImage.InstallUsbImage(self, self.targets[target_name], image_name)
        image.create_image()
    
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
    def __init__(self, name, project):
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
        FileSystem.__init__(self, self.fs_path, project.platform.target_repos)

    def installed_fsets(self):
        result = []
        for fset in os.listdir(self.top):
            if fset not in ['fs', 'image']:
                result.append(fset)
        return result
        
    def install(self, fset, debug=0):
        """
        Install a fset into the target filesystem
        """
        if os.path.isfile(os.path.join(self.top, fset.name)):
            raise ValueError("fset %s is already installed!" % (fset.name))
        
        for dep in fset['deps']:
            if not os.path.isfile(os.path.join(self.top, dep)):
                raise ValueError("fset %s must be installed first!" % (dep))

        FileSystem.install(self, self.fs_path, fset['pkgs'])
        if debug == 1:
            FileSystem.install(self, self.fs_path, fset['debug_pkgs'])

        # and now create a simple empty file that indicates that the fset
        # has been installed...
        result = os.system('touch ' + os.path.join(self.top, fset.name))
        if result != 0:
            raise Exception("Unable to create fset file!");

    def update(self):
        FileSystem.update(self, self.fs_path)

    def __str__(self):
        return ("<Target: name=%s, path=%s, fs_path=%s, image_path>"
                % (self.name, self.path, self.fs_path, self.image_path))
    def __repr__(self):
        return "Target('%s', %s)" % (self.path, self.project)


if __name__ == '__main__':
    if len(sys.argv) != 6:
        print >> sys.stderr, "USAGE: %s PROJECT_NAME PROJECT_PATH PROJECT_DESCRIPTION TARGET_NAME PLATFORM_NAME" % (sys.argv[0])
        print >> sys.stderr, "\tPROJECT_NAME: name to call the project.  The config file /usr/share/esdk/projects/project_name.proj is used or created"
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
    
    sdk = SDK.SDK()

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
        print "Used info from config file: /usr/share/esdk/projects/%s.proj" % name
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
            proj.targets[target_name].install(proj.platform.fset[key])
