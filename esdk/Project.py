#!/usr/bin/python

import os
import sys
import yum

from SDK import *
from Platform import *
from stat import *
from shutil import *

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
	def __init__(self, path, repos):
		self.path = os.path.abspath(os.path.expanduser(path))

		if not os.path.isdir(self.path):
			"""
			Initial filesystem stub has never been created, so
			setup the initial base directory structure with just
			enough done to allow yum to install packages from
			outside the root of the filesystem
			"""
			
			# Create our directories
                        for dirname in [ 'proc', 'var/log', 'var/lib/rpm', 'dev', 'etc/yum.repos.d' ]:
                            full_path = os.path.join(self.path, dirname)
                            os.makedirs(full_path)

                        target_etc = os.path.join(self.path, "etc")
                        for filename in [ 'hosts', 'passwd', 'group', 'resolv.conf' ]:
                            copy(os.path.join('/etc', filename), target_etc)
			yumconf = open(os.path.join(target_etc, 'yum.conf'), 'w')
			print >> yumconf, """\
[main]
cachedir=/var/cache/yum
keepcache=0
debuglevel=2
logfile=/var/log/yum.log
pkgpolicy=newest
distroverpkg=redhat-release
tolerant=1
exactarch=1
obsoletes=1
gpgcheck=0
plugins=1
metadata_expire=1800
"""
			yumconf.close()

			for r in repos:
				copy(r, os.path.join(target_etc, 'yum.repos.d'))

			os.mknod(self.path + '/dev/null', S_IFCHR | 0666, os.makedev(1,3))
			os.mknod(self.path + '/dev/zero', S_IFCHR | 0666, os.makedev(1,5))

			
	def install(self, packages, repos):
		"""
		Call into yum to install RPM packages using the
		specified yum repositories
		"""
		command = 'yum -y --installroot=' + self.path + ' install '
		for p in packages:
			command = command + ' ' + p
		print "About to call: " + command
		os.system(command)

class Project(FileSystem):
	"""
	A Project is a type of  'jailroot' filesystem that is used to
	isolate the build system from the host Linux distribution.  It
	also knows how to create new 'target' filesystems.
	"""
	def __init__(self, path, name, platform):
		self.targets = []
		self.path = os.path.abspath(path)
		self.name = name
		self.platform = platform
		FileSystem.__init__(self, self.path, self.platform.repos)
		
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
