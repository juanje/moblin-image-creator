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

import ConfigParser
import os
import re
import shutil
import socket
import sys
import tarfile
import tempfile
import time

import Platform
import Project
import mic_cfg
import pdk_utils

# This is here for the testing of the new package manager code
USE_NEW_PKG = False
if mic_cfg.config.has_option('general', 'use_new_pkg'):
    USE_NEW_PKG = int(mic_cfg.config.get('general', 'use_new_pkg'))

class SDK(object):
    def __init__(self, progress_callback = None, status_label_callback = None, path='/usr/share/pdk'):
        self.version = "0.1"
        self.path = os.path.realpath(os.path.abspath(os.path.expanduser(path)))
        self.progress_callback = progress_callback
        self.status_label_callback = status_label_callback
        self.config_path = os.path.join(self.path, 'projects')
        if not os.path.isdir(self.config_path):
            os.mkdir(self.config_path)

        # instantiate all platforms
        self.platforms = {}
        dirname = os.path.join(self.path, 'platforms')
        if USE_NEW_PKG:
            platform_config_file = os.path.join(dirname, "platforms.cfg")
            if not os.path.isfile(platform_config_file):
                raise ValueError("Platforms config file not found: %s" % platform_config_file)
            config = ConfigParser.SafeConfigParser()
            config.read(platform_config_file)
            for section in config.sections():
                t_dirname = os.path.join(dirname, section)
                if not os.path.dirname(t_dirname):
                    raise ValueError("Platform config file: %s has a section: %s but no corresponding directory: %s" % (platform_config_file, section, t_dirname))
                self.platforms[section] = Platform.Platform(t_dirname, section, config.items(section))
        else:
            for filename in os.listdir(dirname):
                full_path = os.path.join(dirname, filename)
                if not os.path.isdir(full_path):
                    continue
                try:
                    self.platforms[filename] = Platform.Platform(full_path, filename)
                except:
                    print >> sys.stderr, "Platform Config Error for %s: %s" % (filename, sys.exc_value)
                    pass
            
        # discover all existing projects
        self.projects = {}
        for filename in os.listdir(self.config_path):
            full_path = os.path.join(self.config_path, filename)
            if not os.path.isfile(full_path):
                continue
            config = PackageConfig(full_path)
            self.projects[config.name] = Project.Project(config.path, config.name, config.desc, self.platforms[config.platform], self.progress_callback)

    def discover_projects(self):
        self.projects = {}
        for filename in os.listdir(self.config_path):
            full_path = os.path.join(self.config_path, filename)
            if not os.path.isfile(full_path):
                continue
            config = PackageConfig(full_path)
            self.projects[config.name] = Project.Project(config.path, config.name, config.desc, self.platforms[config.platform], self.progress_callback)
       
            
    def create_project(self, parent_path, name, desc, platform, use_rootstrap = True):
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
        
        install_path = os.path.realpath(os.path.abspath(os.path.expanduser(parent_path)))
        if not os.path.isdir(install_path):
            os.makedirs(install_path)

        rootstrap = os.path.join(platform.path, "build-rootstrap.tar.bz2")
        if self.status_label_callback:
            self.status_label_callback("Creating Rootstrap")
        if not os.path.isfile(rootstrap) or not use_rootstrap:
            # create platform rootstrap file
            count = 0
            cmd = "debootstrap --arch %s --variant=buildd --include=%s %s %s %s" % (platform.architecture, platform.buildroot_extras, platform.buildroot_codename, install_path, platform.buildroot_mirror)
            output = []
            # XXX Evil hack
            if not os.path.isfile("/usr/lib/debootstrap/scripts/%s" % platform.target_codename):
                cmd += " /usr/share/pdk/debootstrap-scripts/%s" % platform.target_codename
            # Sometimes we see network issues that trigger debootstrap
            # to claim the apt repository is corrupt.  This trick will
            # force up to 10 attempts before bailing out with an error
            while count < 10:
                count += 1
                print "--------Platform rootstrap creation try: %s ----------" % count
                print "Executing: %s" % cmd
                result = pdk_utils.execCommand(cmd, output = output, callback = self.progress_callback)
                if result == 0:
                    print "--------Platform rootstrap creation completed successfully ----------"
                    break;
                print "--------Platform rootstrap creation failed result: %s ----------" % result
                sleeptime = 10
                print "--------For try: %s.  Sleeping for %s seconds... -----------------" % (count, sleeptime)
                time.sleep(sleeptime)
            if result != 0:
                print >> sys.stderr, "ERROR: Unable to generate project rootstrap!"
                shutil.rmtree(install_path)
                raise ValueError(" ".join(output))
            # FIXME: Want to do an 'apt-get clean' here
            os.system('rm -fR %s/var/cache/apt/archives/*.deb' % (install_path))
            source_dir = os.path.join(platform.path, 'sources')
            for f in os.listdir(source_dir):
                source_path = os.path.join(source_dir, f)
                dest_path = os.path.join(install_path, 'etc', 'apt', 'sources.list.d', f)
                pdk_utils.copySourcesListFile(source_path, dest_path)
                # shutil.copy(os.path.join(platform.path, 'sources', f), os.path.join(install_path, 'etc', 'apt', 'sources.list.d'))
            if use_rootstrap:
                cmd = "tar -jcpvf %s -C %s ." % (rootstrap, install_path)
                output = []
                result = pdk_utils.execCommand(cmd, output = output, callback = self.progress_callback)
                if result != 0:
                    print >> sys.stderr, "ERROR: Unable to archive rootstrap!"
                    shutil.rmtree(install_path)
                    raise ValueError(" ".join(output))
        else:
            cmd = "tar -jxvf %s -C %s" % (rootstrap, install_path)
            output = []
            result = pdk_utils.execCommand(cmd, output = output, callback = self.progress_callback)
            if result != 0:
                print >> sys.stderr, "ERROR: Unable to rootstrap %s from %s!" % (rootstrap, name)
                shutil.rmtree(install_path)
                raise ValueError(" ".join(output))
        
        # create the config file
        if self.status_label_callback:
            self.status_label_callback("Creating Config file")
        config_path = os.path.join(self.config_path, "%s.proj" % name)
        os.path.isfile(config_path)
        config_file = open(config_path, 'w')
        config_file.write("NAME=%s\n" % (name))
        config_file.write("PATH=%s\n" % (install_path))
        config_file.write("DESC=%s\n" % (desc))
        config_file.write("PLATFORM=%s\n" % (platform.name))
        config_file.close()

        # instantiate the project
        if self.status_label_callback:
            self.status_label_callback("Initiating the project")
        try:
            self.projects[name] = Project.Project(install_path, name, desc, platform, self.progress_callback)
        except:
            shutil.rmtree(install_path)
            os.unlink(config_path)
            raise ValueError("%s" % (sys.exc_value))
        self.projects[name].mount()
        return self.projects[name]

    def isVerboseProjectTar(self):
        """See if we should be verbose during tarring for save/load projects"""
        try:
            result = mic_cfg.config.get("general", "verbose_project_tar")
            result = int(result)
            if result:
                result = 1
            else:
                result = 0
        except:
            result = 0
        return result

    def save_project(self, project_name, filename):
        """Save the project to the specified filename"""
        tar_filename = filename
        if not filename.endswith(".mic.tar.bz2"):
            tar_filename = "%s.mic.tar.bz2" % filename
        project = self.projects[project_name]
        config_file = os.path.join(self.config_path, "%s.proj" % project_name)
        # Create the compressed tarfile
        tar_file = tarfile.open(tar_filename, "w:bz2")
        tar_file.debug = self.isVerboseProjectTar()
        tar_file.add(config_file, arcname = "config/save.proj")
        print "Creating project tarfile.  This can take a long time..."
        print "Filename: %s" % tar_filename
        project.tar(tar_file)
        tar_file.close()
        print "Project tarfile created at: %s" % tar_filename
    
    def load_project(self, project_name, project_path, filename, progressCallback = None):
        """Load the specified filename as project_name and store it in
        project_path"""
        tar_filename = filename
        if not filename.endswith(".mic.tar.bz2"):
            raise ValueError("Specified project restore file: %s, does not end in .mic.tar.bz2")
        config_file = os.path.join(self.config_path, "%s.proj" % project_name)
        if os.path.exists(config_file):
            raise ValueError("A project already exists with that name: %s" % config_file)
        if project_path.find(' ') != -1:
            raise ValueError("Specified project path contains a space character, not allowed: %s" % project_path)
        if os.path.exists(project_path):
            if os.path.isdir(project_path):
                if len(os.listdir(project_path)):
                    raise ValueError("Specified project-path, is a directory, but it is NOT empty: %s" % project_path)
                else:
                    os.rmdir(project_path)
            else:
                raise ValueError("Specified project-path, exists, but it is not a directory")
        tempdir = tempfile.mkdtemp()
        cwd = os.getcwd()
        os.chdir(tempdir)
        print "Extracting: %s to temporary directory: %s/" % (filename, tempdir)
        time.sleep(2)
        if self.isVerboseProjectTar():
            tar_options = "xfjv"
        else:
            tar_options = "xfj"
        pdk_utils.execCommand("tar %s %s" % (tar_options, filename), callback = progressCallback)
        os.chdir(cwd)
        source_config_file = os.path.join(tempdir, "config", "save.proj")
        if not os.path.isfile(source_config_file):
            raise ValueError("Project config file did not exist in project tarfile.  Could not find: %s" % source_config_file)
        source_project = os.path.join(tempdir, "project")
        if not os.path.isdir(source_project):
            raise ValueError("Project directory did not exist in project tarfile.  Could not find: %s" % source_project)
        print "Writing new config file: %s" % config_file
        self.copyProjectConfigFile(source_config_file, config_file, project_name, project_path)
        print "Moving project directory into place at: %s" % project_path
        cmd_line = "mv -v %s %s" % (source_project, project_path)
        print cmd_line
        result = pdk_utils.execCommand(cmd_line)
        if result:
            print "Error doing 'mv' cmd"
            sys.exit(1)
        print "Removing temporary directory: %s" % tempdir
        shutil.rmtree(tempdir)
        print "Project: %s restored to: %s" % (project_name, project_path)

    def copyProjectConfigFile(self, source_config_file, dest_config_file, project_name, project_path):
        """Copy the config file over and update the fields that need to be updated"""
        config = PackageConfig(source_config_file)
        config.set('name', project_name)
        config.set('path', project_path)
        config.write(dest_config_file)
    
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
        result = pdk_utils.execCommand(cmd, output = output, callback = self.progress_callback)
        if result != 0:
            print >> sys.stderr, "ERROR: Unable to delete %s!" % (project_name)
            raise ValueError(" ".join(output))
        os.unlink(os.path.join(self.config_path, proj.name + '.proj'))

    def getProjects(self):
        """Return back a list containing all the projects that the SDK knows about"""
        project_list = []
        for key in sorted(self.projects.iterkeys()):
            project_list.append(self.projects[key])
        return project_list

    def umount(self):
        # Unmount all of our projects
        for key in sorted(self.projects.iterkeys()):
            project = self.projects[key]
            project.umount()

    def __str__(self):
        return ("<SDK Object: path=%s, platform=%s>" %
                (self.path, self.platforms))

    def __repr__(self):
        return "SDK(path='%s')" % self.path

class ConfigFile(object):
    """
    This is a class for generically parsing configuration files that contain
    'NAME=VALUE' pairs, each on it's own line.  We probably should be using the
    ConfigParser library instead :(

    example usage:
    
    string_vals = ['name', 'desc']
    config = ConfigFile('/etc/myconf', string_vals);
    print config.name
    print config.desc

    """
    def __init__(self, filename, string_vals):
        self.__filename = filename
        config = open(self.__filename)
        self.val_dict = {}
        for line in config:
            if re.search(r'^\s*#', line):
                continue
            try:
                key, value = line.split('=')
            except:
                continue
            key = key.lower().strip()
            if key in string_vals:
                self.set(key, value)
        config.close()

    def set(self, key, value):
        key = key.lower().strip()
        value = value.strip()
        self.val_dict[key] = value

    def __getattr__(self, key):
        if key in self.val_dict:
            return self.val_dict[key]
        else:
            if 'object_name' in self.__dict__:
                object_name = self.object_name
            else:
                object_name = "ConfigFile"
            raise AttributeError("'%s' object has no attribute '%s'" % (object_name, key))

    def write(self, filename = None):
        if filename == None:
            filename = self.__filename
        config = open(filename, 'w')
        for key in sorted(self.val_dict.iterkeys()):
            config.write("%s=%s\n" % (key, self.val_dict[key]))
#            os.environ[key] = self.val_dict[key]
        config.close()

    def __str__(self):
        return "ConfigFile('%s', %s)" % (self.__filename, self.val_dict)

class PackageConfig(ConfigFile):
    def __init__(self, path):
        self.object_name = 'PackageConfig'
        ConfigFile.__init__(self, path, ['name', 'desc', 'path', 'platform'])
        

if __name__ == '__main__':
    for path in sys.argv[1:]:
        print SDK(path = path)
