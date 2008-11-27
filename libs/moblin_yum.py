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

# The purpose of this library is to provide an abstraction layer to the YUM
# functionality.  This way the image-creator will not care if you are using apt
# or yum or whatever package management system you want to use.

import gettext
import os
import sys
import time

import mic_cfg
import moblin_pkgbase
import pdk_utils

_ = gettext.lgettext

class YumPackageManager(moblin_pkgbase.PackageManager):
    """Yum class for package management"""

    def __init__(self):
        pass

    def installGroups(self, chroot_dir, groups_list, callback = None):
        """Install the list of groups in the chroot environement"""
        self.__yumPreRun(chroot_dir)
        if not groups_list:
            # No groups, so nothing to do
            return
        retry_count = 0
        # Convert our list of packages to a space separated string
        groups = ' '.join(groups_list)
        while (retry_count < 10):
            self.updateChroot(chroot_dir, callback = callback)
            # yum groupinstall
            command = "yum -y groupinstall "
            for group in groups_list:
                command += "\"%s\" " % group
            #command = "yum -y groupinstall %s" % (groups)
            print _("Running 'yum groupinstall' command: %s") % (command)
            print _("\t in the chroot: %s") % (chroot_dir)
            result = pdk_utils.execChrootCommand(chroot_dir, command, callback = callback)
            if result == 0:
                print _("Completed 'yum groupinstall' successfully")
                break
            print
            print _("Error running 'yum groupinstall' command: %s") % command
            print _("Will try 'yum update' in 15 seconds")
            time.sleep(15)
            retry_count += 1
            # yum update
            command = "yum -y update"
            print _("Running 'yum update' command: %s") % command
            result = pdk_utils.execChrootCommand(chroot_dir, command, callback = callback)
            if result != 0:
                print
                print _("Error running 'yum update' command: %s") % command
                time.sleep(15)
            else:
                print _("Completed 'yum update' successfully")
                print _("Will try 'yum install -f' in 15 seconds")
                time.sleep(15)
        else:
            raise OSError(_("Internal error while attempting to run: %s") % command)
        self.__yumPostRun(chroot_dir)


    def installPackages(self, chroot_dir, package_list, callback = None):
        """Install the list of packages in the chroot environement"""
        self.__yumPreRun(chroot_dir)
        if not package_list:
            # No packages, so nothing to do
            return
        retry_count = 0
        # Convert our list of packages to a space separated string
        packages = ' '.join(package_list)
        while (retry_count < 10):
            self.updateChroot(chroot_dir, callback = callback)
            # yum install
            command = "yum -y install %s" % (packages)
            print _("Running 'yum install' command: %s") % (command)
            print _("\t in the chroot: %s") % (chroot_dir)
            result = pdk_utils.execChrootCommand(chroot_dir, command, callback = callback)
            if result == 0:
                print _("Completed 'yum install' successfully")
                break
            print
            print _("Error running 'yum install' command: %s") % command
            print _("Will try 'yum update' in 15 seconds")
            time.sleep(15)
            retry_count += 1
            # yum update
            command = "yum -y update"
            print _("Running 'yum update' command: %s") % command
            result = pdk_utils.execChrootCommand(chroot_dir, command, callback = callback)
            if result != 0:
                print
                print _("Error running 'yum update' command: %s") % command
                time.sleep(15)
            else:
                print _("Completed 'yum update' successfully")
                print _("Will try 'yum install -f' in 15 seconds")
                time.sleep(15)
        else:
            raise OSError(_("Internal error while attempting to run: %s") % command)
        self.__yumPostRun(chroot_dir)

    def updateChroot(self, chroot_dir, callback = None):
        """Update the chroot environment to have the latest packages"""
        command = "yum clean metadata"
        print _("Running 'yum update' command: %s") % (command)
        print _("\t in the chroot: %s") % (chroot_dir)
        pdk_utils.execChrootCommand(chroot_dir, command, callback = callback)

        command = "yum -y update"
        print _("Running 'yum update' command: %s") % (command)
        print _("\t in the chroot: %s") % (chroot_dir)
        result = pdk_utils.execChrootCommand(chroot_dir, command, callback = callback)
        return result

    def cleanPackageCache(self, chroot_dir):
        """Clean out any cached package files"""
        command = "yum clean all"
        print _("Running 'yum clean' command: %s") % (command)
        print _("\t in the chroot: %s") % (chroot_dir)
        result = pdk_utils.execChrootCommand(chroot_dir, command, callback = callback)
        return result

    def resetPackageDB(self, chroot_dir, callback):
        """reset rpm database to deal with case of running in IA64"""

        """ due to unknown reason execChrootCommand doesn't work on wide-match symbol"""
        #FIXME
        command = "/usr/sbin/chroot %s rm -fr /var/lib/rpm/*db*" % (chroot_dir)
        print _("Running command: %s") % (command)
        os.system(command)
        command = "rpm --rebuilddb"
        print _("Running rpm db reset command: %s") % (command)
        print _("\t in the chroot: %s") % (chroot_dir)
        result = pdk_utils.execChrootCommand(chroot_dir, command, callback = callback)
        if result != 0 :
            print _("Error running command %s") %(command)
        return result

    def mount(self, chroot_dir):
        return []

    def __yumPreRun(self, chroot_dir):
        pass

    def __yumPostRun(self, chroot_dir):
        pass
