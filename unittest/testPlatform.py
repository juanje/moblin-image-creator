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

import os, re, shutil, sys, tempfile, unittest
import test_fsets
sys.path.insert(0, '/usr/share/pdk/lib')

import Platform

class TestPlatform(unittest.TestCase):
    def setUp(self):
        self.workdir = tempfile.mkdtemp()
        self.platform_name = 'unittest_platform'
        self.platform_root = os.path.join(self.workdir, 'platforms')
        self.repo_filename = 'unittest.repo'
        createSamplePlatform(self.platform_root, self.platform_name, self.repo_filename)
    def tearDown(self):
        if os.path.isdir(self.workdir):
            shutil.rmtree(self.workdir)
    def test001Instantiate(self):
        """Simple instantiation test"""
        platform = Platform.Platform(self.workdir, self.platform_name)
    def testStrRepr(self):
        """Test __str__ and __repr__ functions"""
        platform = Platform.Platform(self.workdir, self.platform_name)
        temp = platform.__str__()
        temp = platform.__repr__()
    def testValues(self):
        """Test storing and retrieving values"""
        platform = Platform.Platform(self.workdir, self.platform_name)
        # Make sure it is storing what we passed in
        self.assertEqual(platform.sdk_path, self.workdir)
        self.assertEqual(platform.name, self.platform_name)
    def testRepoFiles(self):
        """Test correctness of repository files"""
        platform = Platform.Platform(self.workdir, self.platform_name)

def createSamplePlatformDir(platform_root, platform_name, repo_filename = "unittest.repo"):
    platform_dir = os.path.join(platform_root, platform_name)
    os.makedirs(platform_dir)
    for dirname in ('buildroot_repos', 'fsets', 'target_repos'):
        os.mkdir(os.path.join(platform_dir, dirname))
    cmdfile=open(os.path.join(platform_dir,'usb_kernel_cmdline'),'w')
    cmdfile.close()
    cmdfile=open(os.path.join(platform_dir,'hd_kernel_cmdline'),'w')
    cmdfile.close()
    test_fsets.createSampleFsetFile(os.path.join(platform_dir, 'fsets', 'unittest.fset'))
    createSampleJailrootPackages(os.path.join(platform_dir, 'buildroot.packages'))
    createSampleJailrootExtras(os.path.join(platform_dir, 'buildroot_extras'))
    createSamplePlatformConfigFile(platform_name, os.path.join(platform_root, "platforms.cfg"))

def createSampleJailrootPackages(filename):
    contents = """\
# stuff needed for building pretty much any package
tar patch gcc gcc-c++ make automake autoconf libtool file rpm-build bzip2 

# not really needed for building, but it sure makes life easier
vim-enhanced tree less diffutils yum

# stuff needed for kernel development
module-init-tools ncurses-devel nash

# Packages required for making bootable images
syslinux busybox squashfs-tools
"""
    text2file(filename, contents)

def createSampleJailrootExtras(filename):
    contents = """\
squashfs-tools busybox-initramfs dosfstools
syslinux module-init-tools mtools gpgv
"""
    text2file(filename, contents)

def createSamplePlatformConfigFile(platform_name, filename):
    contents = """\
[%s]
description = Unittest Platform
package_manager = apt
target_os = ubuntu""" % platform_name
    text2file(filename, contents)

def text2file(filename, text):
    out_file = open(filename, 'w')
    print >> out_file, text
    out_file.close()

if __name__ == '__main__':
    if len(sys.argv) == 2 and sys.argv[1] == "-v":
        suite = unittest.TestLoader().loadTestsFromTestCase(TestPlatform)
        unittest.TextTestRunner(verbosity=2).run(suite)
    else:
        unittest.main()
