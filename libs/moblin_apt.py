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
        raise NotImplementedError

    def installPackages(self, chroot_dir, package_list):
        """Install the list of packages in the chroot environement"""
        __aptgetPreCheck()
        raise NotImplementedError

    def updateChroot(self, chroot_dir, output = None, callback = None):
        __aptgetPreCheck()
        cmd_line = "apt-get update"
        result = pdk_utils.execChrootCommand(chroot_dir, cmd_line, output = output, callback = callback)
        if result:
            return result
        cmd_line = "apt-get upgrade -y --force-yes"
        result = pdk_utils.execChrootCommand(chroot_dir, cmd_line, output = output, callback = callback)
        return result

    def __aptgetPreCheck(self):
        """Stuff that we want to check for before we run an apt-get command"""
        required_dirs = [ "/var/cache/apt/archives/partial" ]
        for dirname in required_dirs:
            if not os.path.isdir(dirname):
                print "The directory: %s is missing, will create it" % dirname
                os.makedirs(dirname)
