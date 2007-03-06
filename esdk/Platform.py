#!/usr/bin/python

import sys 
import os

from SDK import *
from FSet import *

class Platform:
	def __init__(self, SDK, name):
		self.SDK = SDK
		self.name = name

		# instantiate all fsets
		self.fsets = {}
		fset_path = self.SDK.path + '/platforms/' + self.name + '/fsets'
		for file in os.listdir(fset_path):
			fset = FSet(fset_path + '/' + file)
			self.fsets[fset.name] = fset

		# instantiate all repos
		self.repos = []
		repo_path = self.SDK.path + '/platforms/' + self.name + '/repos'
		for repo in os.listdir(repo_path):
			self.repos.append(repo_path + '/' + repo)

		# determine what packages need to be installed in the jailroot
		self.jailroot_packages = []
		config = open(self.SDK.path + '/platforms/' + self.name + '/jailroot.packages')
                for line in config:
			if line[:1] != '#':
				for p in line.split():
					self.jailroot_packages.append(p)
		config.close()

	def __str__(self):
		return ("<Platform Object: \n\tname=%s, \n\tfsets=%s, \n\trepos=%s\n\tjailroot_packages=%s>\n" %
			(self.name, self.fsets, self.repos, self.jailroot_packages))

if __name__ == '__main__':
	for p in sys.argv[1:]:
		print Platform(SDK(), p)
