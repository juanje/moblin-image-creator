#!/usr/bin/python

import os
import sys

class FSet:
	"""
	An FSet object represets a functional set of packages to install
	in a target filesystem.  An FSet contains an array of package names
	in FSet.packages, an array of additional debug packages in
	FSet.debug_packages, and an array of dependant FSet names in
	FSet.deps.
	"""
	def __init__(self, path):
		self.path = path
		self.name = ''
		self.packages = []
		self.debug_packages = []
		self.deps = []
		self.desc = ''

		# Parse the fset file
		fset = open(self.path)
                for line in fset:
                        tmp = line.split('=')
                        if tmp[0] == 'NAME':
                                self.name = tmp[1].strip()
			elif tmp[0] == 'PKGS':
				self.packages = tmp[1].strip().split()
			elif tmp[0] == 'DEBUG_PKGS':
				self.debug_packages = tmp[1].strip().split()
			elif tmp[0] == 'DEPS':
				self.deps = tmp[1].strip().split()
			elif tmp[0] == 'DESC':
				self.desc = tmp[1].strip()
		fset.close()

	def __str__(self):
		return ("<name=%s,desc=%s,packages=%s,debug_packages=%s,deps=%s>" 
                        % (self.name, self.desc, self.packages, self.debug_packages, self.deps))

if __name__ == '__main__':
	if len(sys.argv) == 1:
		print >> sys.stderr, "USAGE: %s FSET_FILE ..." % (sys.argv[0])
	else:
		for file in sys.argv[1:]:
			print FSet(file);
