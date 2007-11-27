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

import moblin_apt, moblin_pkg


class Callback:
    def iteration(process):
        return

class TestMoblin_Apt(unittest.TestCase):
    def setUp(self):
        self.workdir = tempfile.mkdtemp()
    def tearDown(self):
        if os.path.isdir(self.workdir):
            shutil.rmtree(self.workdir)
    def testInstantiate(self):
        aptPackageManager = moblin_pkg.AptPackageManager()
    def testInstallPackages(self):
        aptPackageManager = moblin_pkg.AptPackageManager()
        self.assertRaises(ValueError, aptPackageManager.installPackages, self.workdir, '')

if __name__ == '__main__':
    unittest.main()
