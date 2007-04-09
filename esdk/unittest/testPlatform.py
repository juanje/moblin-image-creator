#!/usr/bin/python -tt
# vim: ai ts=4 sts=4 et sw=4

import os, re, shutil, sys, tempfile, unittest
import testFSet
sys.path.insert(0, '/usr/share/esdk/lib')
import Platform

class TestPlatform(unittest.TestCase):
    def setUp(self):
        self.workdir = tempfile.mkdtemp()
        self.platform_dir = os.path.join(self.workdir, 'platforms', 'unittest')
        self.createSamplePlatformDir(self.platform_dir)
    def tearDown(self):
        if os.path.isdir(self.workdir):
            shutil.rmtree(self.workdir)
    def createSamplePlatformDir(self, platform_dir):
        os.makedirs(platform_dir)
        for dirname in ('buildroot_repos', 'fsets', 'target_repos'):
            os.mkdir(os.path.join(platform_dir, dirname))
        testFSet.createSampleFsetFile(os.path.join(platform_dir, 'fsets', 'unittest.fset'))
        createSampleJailrootPackages(os.path.join(platform_dir, 'jailroot.packages'))
    def testInstantiate(self):
        platform = Platform.Platform(self.workdir, 'unittest')
    def testStrRepr(self):
        platform = Platform.Platform(self.workdir, 'unittest')
        temp = platform.__str__()
        temp = platform.__repr__()

def createSampleJailrootPackages(filename):
    jailroot_file = open(filename, 'w')
    # Let's create a valid FSet file
    print >> jailroot_file, """\
# stuff needed for building pretty much any package
tar patch gcc gcc-c++ make automake autoconf libtool file rpm-build bzip2 

# not really needed for building, but it sure makes life easier
vim-enhanced tree less diffutils yum

# stuff needed for kernel development
module-init-tools ncurses-devel nash

# stuff needed for GUI development
#gtk2-devel gconf2-devel gettext-devel gtkdoc dbus-1-devel dbus-1-glib

# extras
#perl-XML-Parser

# Hildon related build stuff
#outo libmatchbox libfakekey esound-devel

# Packages required for making bootable images
syslinux busybox squashfs-tools
"""
    jailroot_file.close()

if __name__ == '__main__':
    unittest.main()
