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

import moblin_pkgbase
import pdk_utils

class AptPackageManager(moblin_pkgbase.PackageManager):
    """Apt class for package management"""

    def __init__(self):
        self.debian_frontend = os.environ.get("DEBIAN_FRONTEND")
        if self.debian_frontend == None:
            self.debian_frontend = ""

    def installPackages(self, chroot_dir, package_list):
        """Install the list of packages in the chroot environement"""
        self.__aptgetPreRun()


        self.__aptgetPostRun()
        raise NotImplementedError

    def updateChroot(self, chroot_dir, output = None, callback = None):
        self.__aptgetPreRun()
        print "Using moblin_apt library for updateChroot()"
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
        os.environ['DEBIAN_FRONTEND'] = 'noninteractive'

    def __aptgetPostRun(self):
        """Stuff to do after we do any apt-get actions"""
        os.environ['DEBIAN_FRONTEND'] = self.debian_frontend
