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

import ConfigParser
import os
import re
import shutil
import stat
import sys
import time

import fsets
import mic_cfg
import moblin_pkg
import pdk_utils

class Platform(object):
    """
    The SDK is composed of a collection of platforms, where this class
    represents a specific platform.  A platform provides:
    - a list of packages to install directly into the platform (i.e. to use as
      a jailroot to isolate building target binaries from the host
      distribution)
    - a set of fsets that can be installed into a target
    """
    def __init__(self, platform_path, platform_name, config_info = None):
        self.name = platform_name
        self.path = platform_path
        if config_info != None:
            self.config_info = {}
            for key, value in sorted(config_info):
                self.config_info[key] = value
        else:
            raise ValueError("Platform called but config_info value not passed in")
        # instantiate all fsets
        self.fset = fsets.FSet()
        fset_path = os.path.join(self.path, 'fsets')
        for filename in os.listdir(fset_path):
            # Only load files which end with the .fset extension
            if not filename.endswith('.fset'):
                continue
            full_path = os.path.join(fset_path, filename)
            self.fset.addFile(full_path)
        local_config = []
        for section in [ "platform.%s" % self.name, "platform" ]:
            if mic_cfg.config.has_section(section):
                # section is now set to the appropriate section
                break
        else:
            print "Error: No buildroot config file information found!"
            raise ValueError

        # determine what packages additional packages need to be installed
        # in the buildroot roostrap
        packages = mic_cfg.config.get(section, "buildroot_extras")
        self.buildroot_extras = packages.split()
        # determine what packages need to be installed in the buildroot
        # (outside the rootstrap archive)
        packages = mic_cfg.config.get(section, "buildroot_packages")
        self.buildroot_packages = packages.split()
        # determine what mirror to use for the buildroot
        self.buildroot_mirror = mic_cfg.config.get(section, "buildroot_mirror")
        # determine what codename to use for the buildroot mirror
        self.buildroot_codename = mic_cfg.config.get(section, "buildroot_codename")
        # determine what components to use for the buildroot mirror
        components = mic_cfg.config.get(section, "buildroot_components")
        self.buildroot_components = components.split()
        # determine default kernel cmdline options
        self.usb_kernel_cmdline = mic_cfg.config.get(section, "usb_kernel_cmdline")
        self.hd_kernel_cmdline = mic_cfg.config.get(section, "hd_kernel_cmdline")
        self.cd_kernel_cmdline = mic_cfg.config.get(section, "cd_kernel_cmdline")
        # Architecture
        self.architecture = mic_cfg.config.get(section, "architecture") or "i386"
        # Package Manager
        if self.config_info['package_manager'] == 'apt':
            self.pkg_manager = moblin_pkg.AptPackageManager()
            self.createChroot = self.aptCreateChroot
        elif self.config_info['package_manager'] == 'yum':
            self.pkg_manager = moblin_pkg.YumPackageManager()
            self.createChroot = self.yumCreateChroot
        else:
            raise ValueError("package manager value of: '%s' is invalid" % self.config_info['package_manager'])
        # Target OS
        self.target_os = self.config_info['target_os']

    def __str__(self):
        return ("<Platform Object: \n\tname=%s, \n\tfset=%s, \n\tbuildroot_packages=%s>\n" %
                (self.name, self.fset, self.buildroot_packages))

    def __repr__(self):
        return "Platform( %s, '%s')" % (self.path, self.name)

    def __createRootstrap(self, chroot_dir, rootstrap_file, callback = None):
        cmd = "tar -jcpvf %s -C %s ." % (rootstrap_file, chroot_dir)
        output = []
        result = pdk_utils.execCommand(cmd, output = output, callback = callback)
        if result != 0:
            print >> sys.stderr, "ERROR: Unable to archive rootstrap!"
            pdk_utils.rmtree(chroot_dir, callback = callback)
            # FIXME: Better exception here
            raise ValueError(" ".join(output))

    def aptCreateChroot(self, chroot_dir, use_rootstrap, callback = None):
        """Create chroot in chroot_dir for using APT tools"""
        if not os.path.exists(chroot_dir):
            os.makedirs(chroot_dir)
        target_os = self.target_os
        var_dir = mic_cfg.config.get('general', 'var_dir')
        rootstrap_file = os.path.join(var_dir, "rootstraps", "apt", target_os, self.name, "rootstrap.tgz")
        if not os.path.exists(rootstrap_file):
            if self.__aptCreateRootstrap(chroot_dir, rootstrap_file, use_rootstrap, callback = callback) == False:
                return False
        else:
            cmd = "tar -jxvf %s -C %s" % (rootstrap_file, chroot_dir)
            output = []
            result = pdk_utils.execCommand(cmd, output = output, callback = callback)
            if result != 0:
                print >> sys.stderr, "ERROR: Unable to rootstrap %s from %s!" % (rootstrap_file, self.name)
                pdk_utils.rmtree(chroot_dir, callback = callback)
                # FIXME: Better exception here
                raise ValueError(" ".join(output))
        # Setup copies of some useful files from the host into the chroot
        for filename in [ 'hosts', 'resolv.conf' ]:
            source_file = os.path.join("/etc", filename)
            target_file = os.path.join(chroot_dir, 'etc', filename)
            pdk_utils.safeTextFileCopy(source_file, target_file, force = True)
        return True

    def __aptCreateRootstrap(self, chroot_dir, rootstrap_file, use_rootstrap, callback = None):
        codename = self.buildroot_codename
        components = ",".join(self.buildroot_components)
        mirror = self.buildroot_mirror
        chroot_type_string = "Platform"
        basedir = os.path.dirname(rootstrap_file)
        if not os.path.exists(basedir):
            os.makedirs(basedir)
        cmd = "debootstrap --arch %s --include=apt --components=%s %s %s %s" % (self.architecture, components, codename, chroot_dir, mirror)
        output = []
        # XXX Evil hack
        if not os.path.isfile("/usr/lib/debootstrap/scripts/%s" % codename) and not os.path.isfile("/usr/share/debootstrap/scripts/%s" % codename):
            cmd += " /usr/share/pdk/debootstrap-scripts/%s" % codename
        # Sometimes we see network issues that trigger debootstrap to claim the
        # apt repository is corrupt.  This trick will force up to 10 attempts
        # before bailing out with an error
        count = 0
        while count < 10:
            count += 1
            print "--------%s rootstrap creation try: %s ----------" % (chroot_type_string, count)
            print "Execing command: %s" % cmd
            result = pdk_utils.execCommand(cmd, output = output, callback = callback)
            if result == 0:
                print "--------%s rootstrap creation completed successfully----------" % chroot_type_string
                break;
            if result < 0:
                print "Process Aborted"
                return False
            print "--------%s rootstrap creation failed result: %s ----------" % (chroot_type_string, result)
            sleeptime = 30
            print "--------For try: %s.  Sleeping for %s seconds... -----------------" % (count, sleeptime)
            time.sleep(sleeptime)
        if result != 0:
            print >> sys.stderr, "ERROR: Unable to generate %s rootstrap!" % chroot_type_string
            raise ValueError(" ".join(output))
        self.pkg_manager.cleanPackageCache(chroot_dir)
        source_dir = os.path.join(self.path, 'sources')
        for filename in os.listdir(source_dir):
            source_path = os.path.join(source_dir, filename)
            dest_path = os.path.join(chroot_dir, 'etc', 'apt', 'sources.list.d', filename)
            pdk_utils.copySourcesListFile(source_path, dest_path)
        source_path = os.path.join(self.path, 'preferences')
        if os.path.exists(source_path):
            shutil.copy(source_path, os.path.join(chroot_dir, 'etc', 'apt'))
        if use_rootstrap == True:
            self.__createRootstrap(chroot_dir, rootstrap_file, callback = None)

    def yumCreateChroot(self, chroot_dir, use_rootstrap, callback = None):
        if not os.path.exists(chroot_dir):
            os.makedirs(chroot_dir)
        target_os = self.target_os
        var_dir = mic_cfg.config.get('general', 'var_dir')
        rootstrap_file = os.path.join(var_dir, "rootstraps", "yum", target_os, "rootstrap.tgz")
        if not os.path.exists(rootstrap_file):
            self.__yumCreateRootstrap(chroot_dir, rootstrap_file, use_rootstrap, callback = callback)
        else:
            cmd = "tar -jxvf %s -C %s" % (rootstrap_file, chroot_dir)
            output = []
            result = pdk_utils.execCommand(cmd, output = output, callback = callback)
            if result != 0:
                print >> sys.stderr, "ERROR: Unable to rootstrap %s from %s!" % (rootstrap_file, name)
                pdk_utils.rmtree(chroot_dir, callback = callback)
                # FIXME: Better exception here
                raise ValueError(" ".join(output))

    def __yumCreateRootstrap(self, chroot_dir, rootstrap_file, use_rootstrap, callback = None):
        basedir = os.path.dirname(rootstrap_file)
        if not os.path.exists(basedir):
            os.makedirs(basedir)
        self.__yumCreateBase(chroot_dir)
        self.__yumCreateDevices(chroot_dir)
        self.__yumDoMounts(chroot_dir)
        # install yum inside the project using the host tools
        print "Creating rootstrap directory with yum..."
        output = []
        cmd = 'yum -y --disablerepo=localbase --installroot=%s install yum yum-protectbase' % chroot_dir
        cmd = 'yum -y --installroot=%s install yum yum-protectbase' % chroot_dir
        #cmd = 'yum -y --installroot=%s groupinstall buildsys-build' % chroot_dir
        print "Exec command: %s" % cmd
        result = pdk_utils.execCommand(cmd, output = output, callback = callback)
        if result != 0:
            raise RuntimeError("Failed to create Yum based rootstrap")
        # nuke all the yum cache to ensure that we get the latest greatest at project creation
        shutil.rmtree(os.path.join(chroot_dir, 'var', 'cache', 'yum'))
        self.__yumDoUmounts(chroot_dir)
        # Create the rootstrap archive file
        if use_rootstrap == True:
            self.__createRootstrap(chroot_dir, rootstrap_file, callback = callback)

    def __yumDoMounts(self, chroot_dir):
        for cmd in ['mount -n -t proc mic_chroot_proc   %s/proc' % chroot_dir,
                'mount -n -t devpts mic_chroot_devpts %s/dev/pts' % chroot_dir,
                'mount -n -t sysfs  mic_chroot_sysfs  %s/sys' % chroot_dir,
            ]:
            pdk_utils.execCommand(cmd)

    def __yumDoUmounts(self, chroot_dir):
        pdk_utils.umountAllInPath(chroot_dir)

    def __yumCreateBase(self, chroot_dir):
        for dirname in [
            'dev',
            'dev/pts',
            'etc/yum.repos.d',
            'proc',
            'var/lib/rpm', 
            'var/lib/yum',
            'var/log',
            'sys',
            ]:
            os.makedirs(os.path.join(chroot_dir, dirname))
        target_etc = os.path.join(chroot_dir, "etc")
        # Setup copies of some useful files from the host into the chroot
        for filename in [ 'hosts', 'resolv.conf' ]:
            source_file = os.path.join("/etc", filename)
            target_file = os.path.join(target_etc, filename)
            pdk_utils.safeTextFileCopy(source_file, target_file, force = True)
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
releasever=8
"""
        yumconf.close()
        yum_repos_dir = os.path.join(self.path, 'yum.repos.d')
        for filename in os.listdir(yum_repos_dir):
            source_path = os.path.join(yum_repos_dir, filename)
            dest_path = os.path.join(chroot_dir, 'etc', 'yum.repos.d', filename)
            pdk_utils.copySourcesListFile(source_path, dest_path)

    def __yumCreateDevices(self, chroot_dir):
        devices = [
            # name, major, minor, mode
            ('console', 5, 1, (0600 | stat.S_IFCHR)),
            ('null',    1, 3, (0666 | stat.S_IFCHR)),
            ('random',  1, 8, (0666 | stat.S_IFCHR)),
            ('urandom', 1, 9, (0444 | stat.S_IFCHR)),
            ('zero',    1, 5, (0666 | stat.S_IFCHR)),
        ]
        for device_name, major, minor, mode in devices:
            device_path = os.path.join(chroot_dir, 'dev', device_name)
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


if __name__ == '__main__':
    for p in sys.argv[1:]:
        print Platform('/usr/share/pdk', p)
