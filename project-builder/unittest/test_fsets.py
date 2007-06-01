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
sys.path.insert(0, '/usr/share/pdk/lib')
import fsets
    
class TestFset(unittest.TestCase):
    def setUp(self):
        self.workdir = tempfile.mkdtemp()
        self.fset_filename = os.path.join(self.workdir, 'unittest.fset')
        createSampleFsetFile(self.fset_filename)
        # Create another file with same info.
        self.fset_dupfilename = os.path.join(self.workdir, 'unittest2.fset')
        createSampleFsetFile(self.fset_dupfilename)
    def tearDown(self):
        if os.path.isdir(self.workdir):
            shutil.rmtree(self.workdir)
    def testInstantiate(self):
        fset = fsets.FSet()

    def testLoadingFsets(self):
        fset = fsets.FSet()
        fset.addFile(self.fset_filename)
        # Make sure len operator works and we have greater than zero fsets
        self.assert_(len(fset))
        # Make sure we can see if something is in the fset
        if "blah" in fset:
            pass
        # make sure we can iterate over the Fsets
        for key in fset:
            temp = key

    def testFsetInstance(self):
        """Test the FsetInstance class"""
        fset_instance = fsets.FsetInstance('foo')
        for key, value in fsets.FsetInstance.valid_values.iteritems():
            self.assertEqual(fset_instance[key], value)
            self.assertEqual(eval('fset_instance.%s' % key), value)
        # Make sure a bad key raises a KeyError exception
        self.assertRaises(KeyError, fset_instance.get, 'bonk')
        # Make sure we store our values correctly
        sample_pkg_list = ['foo', 'spam']
        fset_instance.add('pkgs', " ".join(sample_pkg_list))
        result = fset_instance['pkgs']
        result.sort()
        self.assertEqual(result, sample_pkg_list)

    def testStrRepr(self):
        fset = fsets.FSet()
        temp = fset.__str__()
        temp = fset.__repr__()
        fset.addFile(self.fset_filename)
        temp = fset['core'].__str__()
        temp = fset['core'].__repr__()
    def testCollision(self):
        fset = fsets.FSet()
        fset.addFile(self.fset_filename)
        self.failUnlessRaises(ValueError, fset.addFile, self.fset_dupfilename)

def createSampleFsetFile(filename):
    fset_file = open(filename, 'w')
    # Let's create a valid FSet file
    print >> fset_file, """\
[Core]
DESC=Fundamental fset that provides a root filesystem
PKGS=kernel-umd-default grub coreutils rpm
DEBUG_PKGS=kernel-umd-developer gdb yum
DEPS=

[Internet]
DESC=Internet fset pulling in basic web 2.0 capabilities
PKGS=firefox
DEBUG_PKGS=firefox-devel
DEPS=core gnome-mobile"""
    fset_file.close()

if __name__ == '__main__':
    unittest.main()
