#!/usr/bin/python

import os
import sys
import yum

from SDK import *
from Platform import *

class FileSystem:
	"""
	This is the base class for any type of a filesystem.  This is used
	for both creating 'jailroot' filesystems that isolate a build from
	the host Linux distribution, and also for creating 'target' filesystems
	that will eventually be transformed into installation images
	to be burned/copied/whatever into the target device.

	By just instantiating a FileSystem object, the caller will trigger
	the basic root filesystem components to be intialized, but to do
	anything usefull with the root filesystem will require the caller
	to use the 'install' method for installing new RPM packages.
	"""
	def __init__(self, path):
		self.path = path

		if os.path.isdir(path) == 0:
			"""
			Initial filesystem stub has never been created, so
			setup the initial base directory structure with just
			enough done to allow yum to install packages from
			outside the root of the filesystem
			"""
			os.mkdir(self.path)
			# make all the minimal directory structures
			# mknod /dev/null and /dev/zero
			# create /etc/yum.conf and /etc/yum.repos.d/*.repo
		
	def install(self, packages, repos):
		"""
		Call into yum to install RPM packages using the
		specified yum repositories
		"""
		args = ['-y', '--installroot=' + self.path,  'install']
		for p in packages:
			args.append(p)
			
		sys.path.insert(0, '/usr/share/yum-cli')
		try:
			import yummain
			yummain.main(args)
		except KeyboardInterrupt, e:
			print >> sys.stderr, "\n\nExiting on user cancel."
			sys.exit(1)

class Project(FileSystem):
	"""
	A Project is a type of  'jailroot' filesystem that is used to
	isolate the build system from the host Linux distribution.  It
	also knows how to create new 'target' filesystems.
	"""
	def __init__(self, path, name, platform):
		self.targets = []
		self.path = path
		self.name = name
		self.platform = platform
		FileSystem.__init__(self, self.path)
		
	def install(self):
		"""
		Install all the packages defined by Platform.jailroot_packages
		"""
		FileSystem.install(self, self.platform.jailroot_packages, self.platform.repos)
		
	def __str__(self):
		return ("<Project: name=%s, path=%s>"
			% (self.name, self.path))

class Target(FileSystem):
	"""
	Represents a 'target' filesystem that will eventually be installed
	on the target device.
	"""
	def __init__(self, name, project):
		self.project = project
		self.fsets = []
		self.name = name
		self.path = jailroot.path + "/targets/fs"
		FileSystem.__init__(self, self.path)

	def __str__(self):
		return ("<Target: name=%s, path=%s>"
                        % (self.name, self.path))


if __name__ == '__main__':
	if len(sys.argv) != 4:
		print >> sys.stderr, "USAGE: %s path name platform" % (sys.argv[0])
		sys.exit(1)

	proj = Project(sys.argv[1], sys.argv[2], Platform(SDK(), sys.argv[3]))
	proj.install()
