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
import moblin_pkg

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
            self.config_info = None
        # instantiate all fsets
        self.fset = fsets.FSet()
        fset_path = os.path.join(self.path, 'fsets')
        for filename in os.listdir(fset_path):
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
        self.buildroot_extras = ','.join(packages.split())
        # determine what packages need to be installed in the buildroot
        # (outside the rootstrap archive)
        packages = mic_cfg.config.get(section, "buildroot_packages")
        self.buildroot_packages = packages.split()
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
        # Architecture
        self.architecture = mic_cfg.config.get(section, "architecture") or "i386"
        # Package Manager
        if self.config_info:
            if self.config_info['package_manager'] == 'apt':
                self.pkg_manager = moblin_pkg.AptPackageManager()
            elif self.config_info['package_manager'] == 'yum':
                self.pkg_manager = moblin_pkg.YumPackageManager()
            else:
                raise ValueError("package manager value of: '%s' is invalid" % self.config_info['package_manager'])
        else:
            self.pkg_manager = moblin_pkg.AptPackageManager()

    def __str__(self):
        return ("<Platform Object: \n\tname=%s, \n\tfset=%s, \n\tbuildroot_packages=%s>\n" %
                (self.name, self.fset, self.buildroot_packages))

    def __repr__(self):
        return "Platform( %s, '%s')" % (self.path, self.name)

if __name__ == '__main__':
    for p in sys.argv[1:]:
        print Platform('/usr/share/pdk', p)
