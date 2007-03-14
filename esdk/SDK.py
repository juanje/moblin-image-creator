#!/usr/bin/python -tt

"""
Embedded Linux SDK (esdk) main module

The SDK allows a developer to use any yum repository as seed material
for building a target filesystem for an embedded device.

User list available projects:
-----------------------------

# Input => Nothing

print 'Available projects: '
sdk = SDK()
for key in sdk.projects.keys():
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
for pname in sdk.platforms.keys():
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
for key in project.targets.keys():
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
for key in platform.fsets.keys():
	fset = platform.fsets[key]
	print '\t - %s' % (fset.name)

User installs a fset in target:
-------------------------------

Input => Target object
Input => fset object

# you could do a normal install
target.install(fset)

# or you could install debug packages in addition to the normal packages
target.install(fset, 1)

"""

import os, re, sys, unittest
import Platform, Project

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
                exec('self.%s = value' % key)
                continue
        config.close()

class PackageConfig(ConfigFile):
    """
    The PackageConfig class abstracts a SDK project configuration file.

    example usage:
    config = PackageConfig('~/.esdk/myproject.proj')
    print '~/esdk/myproject.proj: name=%s desc=%s path=%s platform=%s' %
          (config.name, config.desc, config.path, config.platform)
    """
    def __init__(self, path):
        self.path = path
        ConfigFile.__init__(self, path, ['name', 'desc', 'path', 'platform'])
        

class SDK(object):
    def __init__(self, path='/usr/share/esdk'):
        self.path = os.path.abspath(os.path.expanduser(path))
        
        self.config_path = os.path.join(os.getenv('HOME'), '.esdk')
        if not os.path.isdir(self.config_path):
            os.mkdir(self.config_path)

        # instantiate all platforms
        self.platforms = {}
        for p in os.listdir(os.path.join(self.path, 'platforms')):
            self.platforms[p] = Platform.Platform(self.path, p)

        # discover all existing projects
        self.projects = {}
        for file in os.listdir(self.config_path):
            try:
                config = PackageConfig(os.path.join(self.config_path, file))
                self.projects[config.name] = Project.Project(config.path, config.name, config.desc, self.platforms[config.platform])
            except:
                pass
            
    def create_project(self, install_path, name, desc, platform):
        """
        Create a new project by specifying an install path, a name, a
        short description, and a platform object.

        Example:

        # By 'creating' a project, the class will:
        #   - create a new directory (i.e. path)
        #   - create the initial directory structure
        #   - setup the project configuration files both inside the project
        #     directory, and also 'create the project config' in ~/.esdk/

        proj = SDK().create_project(self, '~/projects/myproject',
                                    'My Project',
                                    'This is a test, only a test', 'donley')

        # after creating the project, you still need to install the platform
        # specific packages to enable the project to be used as a jailroot
        proj.install()
        """
        install_path = os.path.abspath(os.path.expanduser(install_path))
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
        self.projects[name] = Project.Project(install_path, name, desc, platform)
        return self.projects[name]
    
    def delete_project(self, project):
        print "TODO: delete the project"
        
    def __str__(self):
        return ("<SDK Object: path=%s, platform=%s>" %
                (self.path, self.platforms))

    def __repr__(self):
        return "SDK(path='%s')" % self.path

class TestSDK(unittest.TestCase):
    def testInstantiate(self):
        sdk = SDK()
        for key in sdk.projects.keys():
                project = sdk.projects[key]
                a,b = (project.name, project.path)
    def testStrRepr(self):
        sdk = SDK()
        temp = sdk.__str__()
        temp = sdk.__repr__()

if __name__ == '__main__':
    if len(sys.argv) == 1:
        unittest.main()
    for path in sys.argv[1:]:
        print SDK(path)
