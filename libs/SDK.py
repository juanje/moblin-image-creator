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

"""
Embedded Linux SDK main module

The SDK allows a developer to use any apt repository as seed material
for building a target filesystem for an embedded device.

User list available projects:
-----------------------------

# Input => Nothing

print 'Available projects: '
sdk = SDK()
for key in sorted(sdk.projects.iterkeys()):
	project = sdk.projects[key]
	print '\t - %s: %s' % (project.name, project.path)

User opens an existing project:
-------------------------------

Input => Name of existing project

proj = SDK().projects[project_name]

User list available platforms:
------------------------------

# Input  => Name of the project (a string)

print 'Available platforms:'
sdk = SDK()
for pname in sorted(sdk.platforms.iterkeys()):
	print '\t - %s' % sdk.platforms[pname].name 

User creates a new project:
---------------------------

Input => Path to the new project workspace
Input => Name to give the new project
Input => Description of project
Input => Platform object

sdk = SDK()

# construct the new project
proj = sdk.create_project(path, name, desc, sdk.platforms['donley'])

# install the platform defined list of RPM packages into the platform
# so that the platform directory can be used as a jailroot
proj.install()

# keep in mind, that at this point there are no target filesystems
# installed in the project

User list available targets installed in a project:
---------------------------------------------------

Input => Project object

print 'Available targets:'
for key in sorted(project.targets.iterkeys()):
	target = project.targets[key]
	print '\t - %s' % (target.name)

User creates a new target inside a project:
-------------------------------------------

Input => Project object
Input => name to use for target

target = project.create_target(name)

User list available fsets for the platform:
-------------------------------------------

Input => Platform object

print 'Available fsets for the %s platform:' % (platform.name)
for key in platform.fset:
	fset = platform.fset[key]
	print '\t - %s' % (fset.name)

User installs a fset in target:
-------------------------------

Input => Target object
Input => fset object

# you could do a normal install
target.installFset(fset)

# or you could install debug packages in addition to the normal packages
target.installFset(fset, 1)

"""

import os
import re
import shutil
import socket
import sys
import time

import Platform
import Project
import pdk_utils

class ConfigFile(object):
    """
    This is a class for generically parsing configuration files that
    contain 'NAME=VALUE' pairs, each on it's own line.

    example usage:
    
    string_vals = ['name', 'desc']
    config = ConfigFile('/etc/myconf', string_vals);
    print config.name
    print config.desc

    """
    def __init__(self, path, string_vals):
        self.path = path
        config = open(self.path)
        for line in config:
            if re.search(r'^\s*#', line):
                continue
            try:
                key, value = line.split('=')
            except:
                continue
            key = key.lower().strip()
            value = value.strip()
            if key in string_vals:
                setattr(self, key, value)
                continue
        config.close()

    def write(self):
        config = open(self.path, 'w')
        for key in self.__dict__.keys():
            if key != 'path':
                config.write("%s=%s\n" % (key, self.__dict__[key]))
                os.environ[key] = self.__dict__[key]
        config.close()

class PackageConfig(ConfigFile):
    def __init__(self, path):
        self.path = path
        ConfigFile.__init__(self, path, ['name', 'desc', 'path', 'platform'])
        

class SDK(object):
    def __init__(self, cb, path='/usr/share/pdk'):
        self.version = "0.1"
        self.path = os.path.abspath(os.path.expanduser(path))
        self.cb = cb
        self.config_path = os.path.join(self.path, 'projects')
        if not os.path.isdir(self.config_path):
            os.mkdir(self.config_path)

        # instantiate all platforms
        self.platforms = {}
        for p in os.listdir(os.path.join(self.path, 'platforms')):
            try:
                self.platforms[p] = Platform.Platform(self.path, p)
            except:
                print >> sys.stderr, "Platform Config Error for %s: %s" % (p, sys.exc_value)
                pass
            
        # discover all existing projects
        self.projects = {}
        for filename in os.listdir(self.config_path):
            full_path = os.path.join(self.config_path, filename)
            if not os.path.isfile(full_path):
                continue
            try:
                config = PackageConfig(full_path)
                self.projects[config.name] = Project.Project(config.path, config.name, config.desc, self.platforms[config.platform], self.cb)
            except:
                print >> sys.stderr, "Project Config Error: %s" % (sys.exc_value)
            
    def create_project(self, parent_path, name, desc, platform):
        """
        Create a new project by specifying an install path, a name, a
        short description, and a platform object.

        Example:

        # By 'creating' a project, the class will:
        #   - create a new directory (i.e. path)
        #   - create the initial directory structure
        #   - setup the project configuration files both inside the project
        #     directory, and also 'create the project config' in
        #     /usr/share/pdk/projects/

        proj = SDK().create_project(self, '~/projects/myproject',
                                    'My Project',
                                    'This is a test, only a test', 'donley')

        # after creating the project, you still need to install the platform
        # specific packages to enable the project to be used as a jailroot
        proj.install()
        """
        if not parent_path or not name or not desc or not platform:
            raise ValueError("Empty argument passed in")
        
        install_path = os.path.abspath(os.path.expanduser(parent_path))
        if not os.path.isdir(install_path):
            os.makedirs(install_path)

        rootstrap = os.path.join(platform.path, "build-rootstrap.tar.bz2")
        if not os.path.isfile(rootstrap):
            # create platform rootstrap file
            cmd = "debootstrap --arch i386 --variant=buildd --include=%s %s %s %s" % (platform.buildroot_extras, platform.buildroot_codename, install_path, platform.buildroot_mirror)
            output = []
            # XXX Evil hack
            if not os.path.isfile("/usr/lib/debootstrap/scripts/%s" % platform.target_codename):
                cmd += " /usr/share/pdk/debootstrap-scripts/%s" % platform.target_codename
            result = pdk_utils.execCommand(cmd, output = output, callback = self.cb.iteration)
            if result != 0:
                print >> sys.stderr, "ERROR: Unable to generate project rootstrap!"
                shutil.rmtree(install_path)
                raise ValueError(" ".join(output))
            os.system('rm -fR %s/var/cache/apt/archives/*.dev' % (install_path))
            for f in os.listdir(os.path.join(platform.path, 'sources')):
                shutil.copy(os.path.join(platform.path, 'sources', f), os.path.join(install_path, 'etc', 'apt', 'sources.list.d'))
            cmd = "tar -jcpvf %s -C %s ." % (rootstrap, install_path)
            output = []
            result = pdk_utils.execCommand(cmd, output = output, callback = self.cb.iteration)
            if result != 0:
                print >> sys.stderr, "ERROR: Unable to archive rootstrap!"
                shutil.rmtree(install_path)
                raise ValueError(" ".join(output))
        else:
            cmd = "tar -jxvf %s -C %s" % (rootstrap, install_path)
            output = []
            result = pdk_utils.execCommand(cmd, output = output, callback = self.cb.iteration)
            if result != 0:
                print >> sys.stderr, "ERROR: Unable to rootstrap %s from %s!" % (rootstrap, name)
                shutil.rmtree(install_path)
                raise ValueError(" ".join(output))
        
        # create the config file
        config_path = os.path.join(self.config_path, "%s.proj" % name)
        os.path.isfile(config_path)
        config = open(config_path, 'w')
        config.write("NAME=%s\n" % (name))
        config.write("PATH=%s\n" % (install_path))
        config.write("DESC=%s\n" % (desc))
        config.write("PLATFORM=%s\n" % (platform.name))
        config.close()

        # instantiate the project
        try:
            self.projects[name] = Project.Project(install_path, name, desc, platform, self.cb)
        except:
            shutil.rmtree(install_path)
            os.unlink(config_path)
            raise ValueError("%s" % (sys.exc_value))
        self.projects[name].mount()
        return self.projects[name]
    
    def delete_project(self, project_name):
        # first delete all contained targets
        proj = self.projects[project_name]
        for target in proj.targets:
            proj.delete_target(target, False)
        proj.targets.clear()
        # and then deal with the project
        proj.umount()
        # Maybe we should just use shutil.rmtree here??  Of course our progress
        # indicator won't move if we do that.
        cmd = "rm -fR %s" % (os.path.join(proj.path))
        output = []
        result = pdk_utils.execCommand(cmd, output = output, callback = self.cb.iteration)
        if result != 0:
            print >> sys.stderr, "ERROR: Unable to delete %s!" % (project_name)
            raise ValueError(" ".join(output))
        os.unlink(os.path.join(self.config_path, proj.name + '.proj'))
        
    def __str__(self):
        return ("<SDK Object: path=%s, platform=%s>" %
                (self.path, self.platforms))

    def __repr__(self):
        return "SDK(path='%s')" % self.path

class Callback:
    def iteration(self, process):
        return

if __name__ == '__main__':
    for path in sys.argv[1:]:
        print SDK(path = path, cb = Callback())
        
