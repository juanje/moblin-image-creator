#!/usr/bin/python -tt
# vim: ai ts=4 sts=4 et sw=4

import os, re, sys, unittest
sys.path.insert(0, '/usr/share/esdk/lib')
import Platform

# FIXME: Need to create a temporary directory and populate it for the testing

class TestPlatform(unittest.TestCase):
    def testInstantiate(self):
        platform = Platform.Platform('/usr/share/esdk', 'donley')
    def testStrRepr(self):
        platform = Platform.Platform('/usr/share/esdk', 'donley')
        temp = platform.__str__()
        temp = platform.__repr__()

if __name__ == '__main__':
    unittest.main()
