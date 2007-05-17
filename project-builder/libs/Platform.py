#!/usr/bin/python -tt
# vim: ai ts=4 sts=4 et sw=4

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

    def __str__(self):
        return ("<Platform Object: \n\tname=%s, \n\tfset=%s, \n\tbuildroot_packages=%s>\n" %
                (self.name, self.fset, self.buildroot_packages))

    def __repr__(self):
        return "Platform( %s, '%s')" % (self.sdk_path, self.name)

if __name__ == '__main__':
    for p in sys.argv[1:]:
        print Platform('/usr/share/pdk', p)
