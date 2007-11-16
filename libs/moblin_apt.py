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

# The purpose of this library is to provide an abstraction layer to the APT
# functionality.  This way the image-creator will not care if you are using apt
# or yum or whatever package management system you want to use.

import os
import sys
import time

import mic_cfg
import moblin_pkgbase
import pdk_utils

class AptPackageManager(moblin_pkgbase.PackageManager):
    """Apt class for package management"""

    def __init__(self):
        self.apt_cmd = "apt-get -y --force-yes "
        self.debian_frontend = []

    def __createRootstrap(self, chroot_dir, rootstrap_file, platform, callback = None):
        codename = platform.buildroot_codename
        mirror = platform.buildroot_mirror
        chroot_type_string = "Platform"
        basedir = os.path.dirname(rootstrap_file)
        if not os.path.exists(basedir):
            os.makedirs(basedir)
        cmd = "debootstrap --arch %s --include=apt %s %s %s" % (platform.architecture, codename, chroot_dir, mirror)
        output = []
        # XXX Evil hack
        if not os.path.isfile("/usr/lib/debootstrap/scripts/%s" % codename):
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
            print "--------%s rootstrap creation failed result: %s ----------" % (chroot_type_string, result)
            sleeptime = 30
            print "--------For try: %s.  Sleeping for %s seconds... -----------------" % (count, sleeptime)
            time.sleep(sleeptime)
        if result != 0:
            print >> sys.stderr, "ERROR: Unable to generate %s rootstrap!" % chroot_type_string
            raise ValueError(" ".join(output))
        platform.pkg_manager.cleanPackageCache(chroot_dir)
        # workaround for ubuntu kernel package bug
        pdk_utils.touchFile('touch %s/etc/kernel-img.conf' % (chroot_dir))
        pdk_utils.touchFile('touch %s/etc/kernel-pkg.conf' % (chroot_dir))
        source_dir = os.path.join(platform.path, 'sources')
        for f in os.listdir(source_dir):
            source_path = os.path.join(source_dir, f)
            dest_path = os.path.join(chroot_dir, 'etc', 'apt', 'sources.list.d', f)
            pdk_utils.copySourcesListFile(source_path, dest_path)
        source_path = os.path.join(platform.path, 'preferences')
        if os.path.exists(source_path):
            shutil.copy(source_path, os.path.join(chroot_dir, 'etc', 'apt'))
        cmd = "tar -jcpvf %s -C %s ." % (rootstrap_file, chroot_dir)
        output = []
        result = pdk_utils.execCommand(cmd, output = output, callback = callback)
        if result != 0:
            print >> sys.stderr, "ERROR: Unable to archive rootstrap!"
            shutil.rmtree(chroot_dir)
            # FIXME: Better exception here
            raise ValueError(" ".join(output))

    def createChroot(self, chroot_dir, platform, callback = None):
        """Create chroot in chroot_dir"""
        if not os.path.exists(chroot_dir):
            os.makedirs(chroot_dir)
        target_os = platform.target_os
        var_dir = mic_cfg.config.get('general', 'var_dir')
        rootstrap_file = os.path.join(var_dir, "rootstraps", "apt", target_os, platform.name, "rootstrap.tgz")
        if not os.path.exists(rootstrap_file):
            self.__createRootstrap(chroot_dir, rootstrap_file, platform, callback = callback)
        else:
            cmd = "tar -jxvf %s -C %s" % (rootstrap_file, chroot_dir)
            output = []
            result = pdk_utils.execCommand(cmd, output = output, callback = callback)
            if result != 0:
                print >> sys.stderr, "ERROR: Unable to rootstrap %s from %s!" % (rootstrap_file, name)
                shutil.rmtree(chroot_dir)
                # FIXME: Better exception here
                raise ValueError(" ".join(output))

    def installPackages(self, chroot_dir, package_list, callback = None):
        """Install the list of packages in the chroot environement"""
        self.__aptgetPreRun(chroot_dir)
        if not package_list:
            # No packages, so nothing to do
            return
        retry_count = 0
        # Convert our list of packages to a space separated string
        packages = ' '.join(package_list)
        while (retry_count < 10):
            self.updateChroot(chroot_dir, callback = callback)
            # apt-get install
            command = "%s install %s" % (self.apt_cmd, packages)
            print "Running 'apt-get install' command: %s" % (command)
            print "\t in the chroot: %s" % (chroot_dir)
            result = pdk_utils.execChrootCommand(chroot_dir, command, callback = callback)
            if result == 0:
                print "Completed 'apt-get install' successfully"
                break
            print
            print "Error running 'apt-get install' command: %s" % command
            print "Will try 'apt-get update' in 15 seconds"
            time.sleep(15)
            retry_count += 1
            # apt-get update
            command = "apt-get update"
            print "Running 'apt-get update' command: %s" % command
            result = pdk_utils.execChrootCommand(chroot_dir, command, callback = callback)
            if result != 0:
                print
                print "Error running 'apt-get update' command: %s" % command
                print "Will try 'apt-get install -f' in 15 seconds"
                time.sleep(15)
            else:
                print "Completed 'apt-get update' successfully"
                print "Will try 'apt-get install -f' in 15 seconds"
                time.sleep(15)
            # apt-get install -f
            command = "apt-get install -f"
            result = pdk_utils.execChrootCommand(chroot_dir, command, callback = callback)
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
        self.__aptgetPostRun()

    def updateChroot(self, chroot_dir, output = None, callback = None):
        self.__aptgetPreRun(chroot_dir)
        print "Updating the chroot dir: %s" % chroot_dir
        cmd_line = "apt-get update"
        result = pdk_utils.execChrootCommand(chroot_dir, cmd_line, output = output, callback = callback)
        if result:
            self.__aptgetPostRun()
            return result
        cmd_line = "apt-get upgrade -y --force-yes"
        result = pdk_utils.execChrootCommand(chroot_dir, cmd_line, output = output, callback = callback)
        self.__aptgetPostRun()
        return result

    def cleanPackageCache(self, chroot_dir, output = None, callback = None):
        """Clean out any cached package files"""
        cmd_line = "apt-get clean"
        return pdk_utils.execChrootCommand(chroot_dir, cmd_line, output = output, callback = callback)

    def __aptgetPreCheck(self):
        """Stuff that we want to check for before we run an apt-get command"""
        required_dirs = [ "/var/cache/apt/archives/partial" ]
        for dirname in required_dirs:
            if not os.path.isdir(dirname):
                print "The directory: %s is missing, will create it" % dirname
                os.makedirs(dirname)

    def __aptgetPreRun(self, chroot_dir):
        """Stuff to do before we do any apt-get actions"""
        self.__aptgetPreCheck()
        if not os.path.isfile(os.path.join(chroot_dir, 'bin/bash')):
            print >> sys.stderr, "Incomplete jailroot at %s" % (chroot_dir)
            raise ValueError("Internal Error: Invalid buildroot at %s" % (chroot_dir))
        self.debian_frontend.append(os.environ.get("DEBIAN_FRONTEND"))
        os.environ['DEBIAN_FRONTEND'] = 'noninteractive'
        self.__disable_init_scripts(chroot_dir)

    def __aptgetPostRun(self):
        """Stuff to do after we do any apt-get actions"""
        if self.debian_frontend:
            debian_frontend = self.debian_frontend.pop()
            if debian_frontend == None:
                del os.environ['DEBIAN_FRONTEND']
            else:
                os.environ['DEBIAN_FRONTEND'] = debian_frontend
        else:
            print "moblin_apt.__aptgetPostRun() called without corresponding aptgetPreRun()"

    def __disable_init_scripts(self, chroot_dir):
        # In debian if we have the file /usr/sbin/policy-rc.d, which just
        # return the value 101.  Then package postinstall scripts are not
        # supposed to run.
        # http://people.debian.org/~hmh/invokerc.d-policyrc.d-specification.txt
        filename = os.path.join(chroot_dir, "usr/sbin/policy-rc.d")
        if not os.path.exists(filename):
            out_file = open(filename, 'w')
            print >> out_file, "#!/bin/sh"
            print >> out_file, "exit 101"
            out_file.close()
        os.chmod(filename, 0755)
