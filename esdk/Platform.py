#!/usr/bin/python -tt

import os, re, sys

from SDK import *
from FSet import *

class Platform:
    """
    The SDK is composed of a collection of platforms, where this class
    represents a specific platform.  A platform provides:
    - a list of packages to install directly into the platform (i.e. to use as
      a jailroot to isolate building target binaries from the host
      distribution)
    - a set of fsets that can be installed into a target
    - a list of yum repositories that are used to install the fsets

    """
    def __init__(self, SDK, name):
        self.SDK = SDK
        self.name = name
        self.path = os.path.join(self.SDK.path, 'platforms', self.name)

        # instantiate all fsets
        self.fset = Fset()
        fset_path = os.path.join(self.path, 'fsets')
        for filename in os.listdir(fset_path):
            self.fset.addFile(os.path.join(fset_path, filename))

        # instantiate all repos
        self.repos = []
        repo_path = os.path.join(self.path, 'repos')
        for repo in os.listdir(repo_path):
            self.repos.append(os.path.join(repo_path, repo))

        # determine what packages need to be installed in the jailroot
        self.jailroot_packages = []
        config = open(os.path.join(self.path, 'jailroot.packages'))
        for line in config:
            # Ignore lines beginning with '#'
            if not re.search(r'^\s*#', line):
                for p in line.split():
                    self.jailroot_packages.append(p)
        config.close()

    def __str__(self):
        return ("<Platform Object: \n\tname=%s, \n\tfsets=%s, \n\trepos=%s\n\tjailroot_packages=%s>\n" %
                (self.name, self.fsets, self.repos, self.jailroot_packages))

if __name__ == '__main__':
    for p in sys.argv[1:]:
        print Platform(SDK(), p)
