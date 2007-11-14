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
import time

import moblin_pkgbase
import pdk_utils

class AptPackageManager(moblin_pkgbase.PackageManager):
    """Apt class for package management"""

    def __init__(self):
        self.debian_frontend = os.environ.get("DEBIAN_FRONTEND")
        if self.debian_frontend == None:
            self.debian_frontend = ""
        self.apt_cmd = "apt-get -y --force-yes "

    def createChroot(self, chroot_dir):
        # FIXME: Not yet working :(
        raise NotImplementedError
        if not os.path.isfile(rootstrap) or not use_rootstrap:
            # create platform rootstrap file
            count = 0
            cmd = "debootstrap --arch %s --variant=buildd --include=%s %s %s %s" % (platform.architecture, platform.buildroot_extras, platform.buildroot_codename, install_path, platform.buildroot_mirror)
            output = []
            # XXX Evil hack
            if not os.path.isfile("/usr/lib/debootstrap/scripts/%s" % platform.target_codename):
                cmd += " /usr/share/pdk/debootstrap-scripts/%s" % platform.target_codename
            # Sometimes we see network issues that trigger debootstrap
            # to claim the apt repository is corrupt.  This trick will
            # force up to 10 attempts before bailing out with an error
            while count < 10:
                count += 1
                print "--------Platform rootstrap creation try: %s ----------" % count
                print "Executing: %s" % cmd
                result = pdk_utils.execCommand(cmd, output = output, callback = self.progress_callback)
                if result == 0:
                    print "--------Platform rootstrap creation completed successfully ----------"
                    break;
                print "--------Platform rootstrap creation failed result: %s ----------" % result
                sleeptime = 10
                print "--------For try: %s.  Sleeping for %s seconds... -----------------" % (count, sleeptime)
                time.sleep(sleeptime)
            if result != 0:
                print >> sys.stderr, "ERROR: Unable to generate project rootstrap!"
                shutil.rmtree(install_path)
                raise ValueError(" ".join(output))
            # FIXME: Want to do an 'apt-get clean' here
            os.system('rm -fR %s/var/cache/apt/archives/*.deb' % (install_path))
            source_dir = os.path.join(platform.path, 'sources')
            for f in os.listdir(source_dir):
                source_path = os.path.join(source_dir, f)
                dest_path = os.path.join(install_path, 'etc', 'apt', 'sources.list.d', f)
                pdk_utils.copySourcesListFile(source_path, dest_path)
                # shutil.copy(os.path.join(platform.path, 'sources', f), os.path.join(install_path, 'etc', 'apt', 'sources.list.d'))
            if use_rootstrap:
                cmd = "tar -jcpvf %s -C %s ." % (rootstrap, install_path)
                output = []
                result = pdk_utils.execCommand(cmd, output = output, callback = self.progress_callback)
                if result != 0:
                    print >> sys.stderr, "ERROR: Unable to archive rootstrap!"
                    shutil.rmtree(install_path)
                    raise ValueError(" ".join(output))

    def installPackages(self, chroot_dir, package_list, callback = None):
        """Install the list of packages in the chroot environement"""
        self.__aptgetPreRun()
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
            ret = pdk_utils.execChrootCommand(chroot_dir, command, callback = callback)
            if ret == 0:
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
            ret = pdk_utils.execChrootCommand(chroot_dir, command, callback = callback)
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
            ret = pdk_utils.execChrootCommand(chroot_dir, command, callback = callback)
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
        self.__aptgetPreRun()
        print "Updating the chroot dir: %s" % chroot_dir
        cmd_line = "apt-get update"
        result = pdk_utils.execChrootCommand(chroot_dir, cmd_line, output = output, callback = callback)
        if result:
            __aptgetPostRun()
            return result
        cmd_line = "apt-get upgrade -y --force-yes"
        result = pdk_utils.execChrootCommand(chroot_dir, cmd_line, output = output, callback = callback)
        self.__aptgetPostRun()
        return result

    def __aptgetPreCheck(self):
        """Stuff that we want to check for before we run an apt-get command"""
        required_dirs = [ "/var/cache/apt/archives/partial" ]
        for dirname in required_dirs:
            if not os.path.isdir(dirname):
                print "The directory: %s is missing, will create it" % dirname
                os.makedirs(dirname)

    def __aptgetPreRun(self):
        """Stuff to do before we do any apt-get actions"""
        self.__aptgetPreCheck()
        os.environ['DEBIAN_FRONTEND'] = 'Noninteractive'

    def __aptgetPostRun(self):
        """Stuff to do after we do any apt-get actions"""
        os.environ['DEBIAN_FRONTEND'] = self.debian_frontend
