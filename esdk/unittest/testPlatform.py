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
        createSamplePlatformDir(self.platform_dir)
    def tearDown(self):
        if os.path.isdir(self.workdir):
            shutil.rmtree(self.workdir)
    def testInstantiate(self):
        platform = Platform.Platform(self.workdir, 'unittest')
    def testStrRepr(self):
        platform = Platform.Platform(self.workdir, 'unittest')
        temp = platform.__str__()
        temp = platform.__repr__()

def createSamplePlatformDir(platform_dir):
    os.makedirs(platform_dir)
    for dirname in ('buildroot_repos', 'fsets', 'target_repos'):
        os.mkdir(os.path.join(platform_dir, dirname))
    testFSet.createSampleFsetFile(os.path.join(platform_dir, 'fsets', 'unittest.fset'))
    createSampleJailrootPackages(os.path.join(platform_dir, 'jailroot.packages'))
    createSampleRepos(platform_dir)

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

def createSampleRepos(root_dir):
    repo_text = """\
[esdk-base]
name=ESDK Base
baseurl=http://umd-build2.jf.intel.com/yum-repos/fedora-6-core/
enabled=1
gpgcheck=0

[esdk-updates]
name=ESDK Updates
baseurl=http://umd-build2.jf.intel.com/yum-repos/fedora-6-updates/
enabled=1
gpgcheck=0

[esdk-extras]
name=ESDK Extras
baseurl=http://umd-build2.jf.intel.com/yum-repos/fedora-6-extras/
enabled=1
gpgcheck=0

[esdk-rpms]
name=ESDK RPMS
baseurl=http://umd-build2.jf.intel.com/yum-repos/mid-core/
enabled=1
gpgcheck=0"""
    for dirname in ('buildroot_repos', 'target_repos'):
        full_path = os.path.join(root_dir, dirname, "unittest.repo")
        text2file(full_path, repo_text)


def text2file(filename, text):
    out_file = open(filename, 'w')
    print >> out_file, text
    out_file.close()

if __name__ == '__main__':
    unittest.main()
