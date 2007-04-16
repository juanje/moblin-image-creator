#!/usr/bin/python -tt
# vim: ai ts=4 sts=4 et sw=4

import os, re, shutil, sys, tempfile, unittest
import test_fsets
sys.path.insert(0, '/usr/share/esdk/lib')
import Platform

class TestPlatform(unittest.TestCase):
    def setUp(self):
        self.workdir = tempfile.mkdtemp()
        self.platform_name = 'unittest_platform'
        self.platform_dir = os.path.join(self.workdir, 'platforms', self.platform_name)
        self.repo_filename = 'unittest.repo'
        createSamplePlatformDir(self.platform_dir, self.repo_filename)
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
        # Test buildroot_repos
        self.assertEqual(len(platform.buildroot_repos), 1)
        self.assertEqual(platform.buildroot_repos[0], os.path.join(self.platform_dir, 'buildroot_repos', self.repo_filename))
        # Test target_repos
        self.assertEqual(len(platform.target_repos), 1)
        self.assertEqual(platform.target_repos[0], os.path.join(self.platform_dir, 'target_repos', self.repo_filename))

def createSamplePlatformDir(platform_dir, repo_filename = "unittest.repo"):
    os.makedirs(platform_dir)
    for dirname in ('buildroot_repos', 'fsets', 'target_repos'):
        os.mkdir(os.path.join(platform_dir, dirname))
    test_fsets.createSampleFsetFile(os.path.join(platform_dir, 'fsets', 'unittest.fset'))
    createSampleJailrootPackages(os.path.join(platform_dir, 'buildroot.packages'))
    createSampleRepos(platform_dir, repo_filename)

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

def createSampleRepos(root_dir, repo_filename):
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
        full_path = os.path.join(root_dir, dirname, repo_filename)
        text2file(full_path, repo_text)


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
