#!/usr/bin/python

import os
import sys

class FSet:
	def __init__(self, path):
		self.path = path
		self._parse()

	def _parse(self):
		self.name = ''
		self.packages = []
		self.debug_packages = []
		self.deps = []
		self.desc = ''

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
	for file in sys.argv[1:]:
		print FSet(file);
