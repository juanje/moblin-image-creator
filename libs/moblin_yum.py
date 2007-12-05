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

import moblin_pkgbase

class YumPackageManager(moblin_pkgbase.PackageManager):
    """Yum class for package management"""

    def __init__(self):
        pass

    def mount(self, chroot_dir):
        return []

    def installPackages(self, chroot_dir, package_list, callback = None):
        """Install the list of packages in the chroot environement"""
        print "yum.installPackages: Not implemented yet!!!!"

    def updateChroot(self, chroot_dir):
        """Update the chroot environment to have the latest packages"""
        print "Not implemented yet!!!!"
        print "yum.updateChroot: Not implemented yet!!!!"

    def cleanPackageCache(self, chroot_dir):
        """Clean out any cached package files"""
        print "yum.cleanPackageCache: Not implemented yet!!!!"
