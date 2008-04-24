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
#
#  Embedded Linux SDK main module
#
#  The SDK allows a developer to use any apt repository as seed material
#  for building a target filesystem for an embedded device.
#
#  User list available projects:
#  -----------------------------
#
#  # Input => Nothing
#
#  print 'Available projects: '
#  sdk = SDK()
#  for key in sorted(sdk.projects.iterkeys()):
#  	project = sdk.projects[key]
#  	print '\t - %s: %s' % (project.name, project.path)
#
#  User opens an existing project:
#  -------------------------------
#
#  Input => Name of existing project
#
#  proj = SDK().projects[project_name]
#
#  User list available platforms:
#  ------------------------------
#
#  # Input  => Name of the project (a string)
#
#  print 'Available platforms:'
#  sdk = SDK()
#  for pname in sorted(sdk.platforms.iterkeys()):
#  	print '\t - %s' % sdk.platforms[pname].name 
#
#  User creates a new project:
#  ---------------------------
#
#  Input => Path to the new project workspace
#  Input => Name to give the new project
#  Input => Description of project
#  Input => Platform object
#
#  sdk = SDK()
#
#  # construct the new project
#  proj = sdk.create_project(path, name, desc, sdk.platforms['donley'])
#
#  # install the platform defined list of RPM packages into the platform
#  # so that the platform directory can be used as a jailroot
#  proj.install()
#
#  # keep in mind, that at this point there are no target filesystems
#  # installed in the project
#
#  User list available targets installed in a project:
#  ---------------------------------------------------
#
#  Input => Project object
#
#  print 'Available targets:'
#  for key in sorted(project.targets.iterkeys()):
#  	target = project.targets[key]
#  	print '\t - %s' % (target.name)
#
#  User creates a new target inside a project:
#  -------------------------------------------
#
#  Input => Project object
#  Input => name to use for target
#
#  target = project.create_target(name)
#
#  User list available fsets for the platform:
#  -------------------------------------------
#
#  Input => Platform object
#
#  print 'Available fsets for the %s platform:' % (platform.name)
#  for key in platform.fset:
#  	fset = platform.fset[key]
#  	print '\t - %s' % (fset.name)
#
#  User installs a fset in target:
#  -------------------------------
#
#  Input => Target object
#  Input => fset object
#
#  # you could do a normal install
#  target.installFset(fset)
#
#  # or you could install debug packages in addition to the normal packages
#  target.installFset(fset, debug_pkgs = 1)

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

class SDK(object):
    def __init__(self, progress_callback = None, status_label_callback = None,
            path='/usr/share/pdk', var_dir = '/var/lib/moblin-image-creator/'):
        self.var_dir = var_dir
        self.path = os.path.realpath(os.path.abspath(os.path.expanduser(path)))
        self.version = "- Undefined"
        version_file = os.path.join(self.path, "version")
        if os.path.isfile(version_file):
            in_file = open(version_file, 'r')
            line = in_file.readline()
            line = line.strip()
            result = re.search(r'\((?P<version>.*)\) (?P<distribution>.*);', line)
            if result:
                self.version = "- %s - %s" % (result.group('version'), result.group('distribution'))
            in_file.close()
        self.progress_callback_func = progress_callback
        self.status_label_callback_func = status_label_callback
        self.config_path = os.path.join(self.var_dir, 'projects')
        if not os.path.isdir(self.config_path):
            os.mkdir(self.config_path)

        # instantiate all platforms
        self.platforms = {}
        dirname = os.path.join(self.path, 'platforms')
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
            
        # discover all existing projects
        self.discover_projects()

    def progress_callback(self, *args):
        if not self.progress_callback_func:
            return
        self.progress_callback_func(*args)

    def status_label_callback(self, *args):
        if not self.status_label_callback_func:
            return
        self.status_label_callback_func(*args)

    def discover_projects(self):
        self.projects = {}
        self.obsolete_projects = set()
        directories = [ os.path.join(self.config_path, x) for x in os.listdir(self.config_path) ]
        # FIXME: This is here for backwards compatibility, I would think that
        # after Jun-2008, we can delete this list
        old_directories = [ os.path.join(self.path, 'projects', x) for x in os.listdir(os.path.join(self.path, 'projects')) ]
        directories.extend(old_directories)
        for filename in directories:
            full_path = os.path.join(self.config_path, filename)
            full_path = filename
            if not os.path.isfile(full_path):
                continue
            config = PackageConfig(full_path)
            try:
                self.projects[config.name] = Project.Project(config, self.platforms[config.platform], self.progress_callback)
            except KeyError:
                self.obsolete_projects.add(config.name)
                print "Platform %s not found. Skipping the project %s" % (config.platform, config.name)       

    def return_obsolete_projects(self):
        return self.obsolete_projects
            
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
        if name in self.projects:
            raise ValueError("Project: %s already exists" % name)
        install_path = os.path.realpath(os.path.abspath(os.path.expanduser(parent_path)))
        self.status_label_callback("Creating the project chroot environment")
        if platform.createChroot(install_path, use_rootstrap, callback = self.progress_callback) == False:
            pdk_utils.rmtree(install_path, callback = self.progress_callback)
            raise ValueError("Rootstrap Creating cancelled")
        # create the config file
        self.status_label_callback("Creating Config file")
        config_path = os.path.join(self.config_path, "%s.proj" % name)
        config_file = open(config_path, 'w')
        config_file.write("NAME=%s\n" % (name))
        config_file.write("PATH=%s\n" % (install_path))
        config_file.write("DESC=%s\n" % (desc))
        config_file.write("PLATFORM=%s\n" % (platform.name))
        config_file.close()
        # instantiate the project
        self.status_label_callback("Initiating the project")
        config = PackageConfig(config_path)
        try:
            self.projects[name] = Project.Project(config, platform, self.progress_callback)
        except:
            pdk_utils.rmtree(install_path, callback = self.progress_callback)
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
        pdk_utils.execCommand("tar %s %s --numeric-owner" % (tar_options, filename), callback = progressCallback)
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
        pdk_utils.rmtree(tempdir, callback = self.progress_callback)
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
            self.progress_callback(None)
            proj.delete_target(target, False, callback = self.progress_callback)
        proj.targets.clear()
        # and then deal with the project
        directory_set = proj.umount()
        if directory_set:
            raise pdk_utils.ImageCreatorUmountError, directory_set
        pdk_utils.rmtree(proj.path, callback = self.progress_callback)
        os.unlink(proj.config_info.filename)

    def getProjects(self):
        """Return back a list containing all the projects that the SDK knows about"""
        project_list = []
        for key in sorted(self.projects.iterkeys()):
            project_list.append(self.projects[key])
        return project_list

    def clear_rootstraps(self):
        print "Deleting rootstraps..."
        for key in self.platforms.iterkeys():
            path = self.platforms[key].path
            for prefix in [ "build", "target" ]:
                root_strap_path = os.path.join(path, "%s-rootstrap.tar.bz2" % prefix)
                if os.path.exists(root_strap_path):
                    print "Deleting: %s" % root_strap_path
                    os.unlink(root_strap_path)
        var_dir = mic_cfg.config.get('general', 'var_dir')
        rootstrap_dir = os.path.join(var_dir, "rootstraps")
        if os.path.exists(rootstrap_dir):
            print "Deleting rootstrap directory: %s" % rootstrap_dir
            pdk_utils.rmtree(rootstrap_dir, callback = self.progress_callback)

    def umount(self):
        # Unmount all of our projects
        directory_set = set()
        for key in sorted(self.projects.iterkeys()):
            project = self.projects[key]
            project.umount(directory_set = directory_set)
        return directory_set

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
        self.filename = filename
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
