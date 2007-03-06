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
		for fset in os.listdir(fset_path):
			self.fsets[fset] = FSet(fset_path + '/' + fset)

		# instantiate all repos
		self.repos = []
		repo_path = self.SDK.path + '/platforms/' + self.name + '/repos'
		for repo in os.listdir(repo_path):
			self.repos.append(repo_path + '/' + repo)

	def __str__(self):
		return ("<Platform Object: \n\tname=%s, \n\tfsets=%s, \n\trepos=%s>\n" %
			(self.name, self.fsets, self.repos))

if __name__ == '__main__':
	for p in sys.argv[1:]:
		print Platform(SDK(), p)
