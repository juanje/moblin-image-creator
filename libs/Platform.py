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

import os
import re
import sys

import fsets

class Platform(object):
    """
    The SDK is composed of a collection of platforms, where this class
    represents a specific platform.  A platform provides:
    - a list of packages to install directly into the platform (i.e. to use as
      a jailroot to isolate building target binaries from the host
      distribution)
    - a set of fsets that can be installed into a target
    """
    def __init__(self, sdk_path, name):
        self.sdk_path = os.path.abspath(os.path.expanduser(sdk_path))
        self.name = name
        self.path = os.path.join(self.sdk_path, 'platforms', self.name)
        # instantiate all fsets
        self.fset = fsets.FSet()
        fset_path = os.path.join(self.path, 'fsets')
        for filename in os.listdir(fset_path):
            self.fset.addFile(os.path.join(fset_path, filename))
        # determine what packages need to be installed in the buildroot
        self.buildroot_packages = []
        config = open(os.path.join(self.path, 'buildroot.packages'))
        for line in config:
            # Ignore lines beginning with '#'
            if not re.search(r'^\s*#', line):
                for p in line.split():
                    self.buildroot_packages.append(p)
        config.close()
        # determine default kernel cmdline options
        self.usb_kernel_cmdline = ''
        self.hd_kernel_cmdline = ''
        config = open(os.path.join(self.path, 'usb_kernel_cmdline'), 'r')
        for line in config:
            if not re.search(r'^\s*#',line):
                self.usb_kernel_cmdline += line + ' '
        config.close()
        config = open(os.path.join(self.path, 'hd_kernel_cmdline'), 'r')
        for line in config:
            if not re.search(r'^\s*#',line):
                self.hd_kernel_cmdline += line + ' '
        config.close()

    def __str__(self):
        return ("<Platform Object: \n\tname=%s, \n\tfset=%s, \n\tbuildroot_packages=%s>\n" %
                (self.name, self.fset, self.buildroot_packages))

    def __repr__(self):
        return "Platform( %s, '%s')" % (self.sdk_path, self.name)

if __name__ == '__main__':
    for p in sys.argv[1:]:
        print Platform('/usr/share/pdk', p)
