#!/usr/bin/python

import sys 
import os

from Platform import *

class SDK:
	def __init__(self, path='/usr/share/esdk'):
		self.path = path
		
		# instantiate all platforms
		self.platforms = {}
		for p in os.listdir(self.path + '/platforms/'):
			self.platforms[p] = Platform(self, p)

		self.jailroot_packages = []

	def __str__(self):
		return ("<SDK Object: path=%s, platform=%s>" %
			(self.path, self.platforms))

if __name__ == '__main__':
	for path in sys.argv[1:]:
		print SDK(path)
