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
import sys

import fsets
import mic_cfg

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
        self.sdk_path = os.path.realpath(os.path.abspath(os.path.expanduser(sdk_path)))
        self.name = name
        self.path = os.path.join(self.sdk_path, 'platforms', self.name)
        # instantiate all fsets
        self.fset = fsets.FSet()
        fset_path = os.path.join(self.path, 'fsets')
        for filename in os.listdir(fset_path):
            self.fset.addFile(os.path.join(fset_path, filename))
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
        self.buildroot_extras = ""
        packages = mic_cfg.config.get(section, "buildroot_extras")
        for p in packages.split():
            self.buildroot_extras += p + ','
        # determine what packages need to be installed in the buildroot
        # (outside the rootstrap archive)
        self.buildroot_packages = []
        packages = mic_cfg.config.get(section, "buildroot_packages")
        for p in packages.split():
            self.buildroot_packages.append(p)
        # determine what mirror to use for the buildroot
        self.buildroot_mirror = mic_cfg.config.get(section, "buildroot_mirror")
        # determine what codename to use for the buildroot mirror
        self.buildroot_codename = mic_cfg.config.get(section, "buildroot_codename")
        # determine what mirror to use for the target
        self.target_mirror = mic_cfg.config.get(section, "target_mirror")
        # determine what codename to use for the buildroot mirror
        self.target_codename = mic_cfg.config.get(section, "target_codename")
        # determine default kernel cmdline options
        self.usb_kernel_cmdline = mic_cfg.config.get(section, "usb_kernel_cmdline")
        self.hd_kernel_cmdline = mic_cfg.config.get(section, "hd_kernel_cmdline")

    def __str__(self):
        return ("<Platform Object: \n\tname=%s, \n\tfset=%s, \n\tbuildroot_packages=%s>\n" %
                (self.name, self.fset, self.buildroot_packages))

    def __repr__(self):
        return "Platform( %s, '%s')" % (self.sdk_path, self.name)

if __name__ == '__main__':
    for p in sys.argv[1:]:
        print Platform('/usr/share/pdk', p)
