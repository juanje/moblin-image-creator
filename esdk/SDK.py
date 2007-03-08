#!/usr/bin/python -tt

import sys
import os

from Platform import *
from Project import *

class ConfigFile:
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
    def __init__(self, path):
        self.path = path
        ConfigFile.__init__(self, path, ['name', 'desc', 'path', 'platform'])
        

class SDK:
    def __init__(self, path='/usr/share/esdk'):
        self.path = os.path.abspath(os.path.expanduser(path))
        
        self.config_path = os.path.join(os.getenv('HOME'), '.esdk')
        if not os.path.isdir(self.config_path):
            os.mkdir(self.config_path)

        # instantiate all platforms
        self.platforms = {}
        for p in os.listdir(os.path.join(self.path, 'platforms')):
            self.platforms[p] = Platform(self, p)

        # discover all existing projects
        self.projects = {}
        for file in os.listdir(self.config_path):
            config = PackageConfig(os.path.join(self.config_path, file))
            self.projects[config.name] = Project(config.path, config.name, self.platforms[config.platform])

    def create_project(self, path, name, desc, platform):

        # create the config file
        config_path = os.path.join(self.config_path, name + '.proj')
        os.path.isfile(config_path)
        config = open(config_path, 'w')
        config.write("NAME=%s\n" % (name))
        config.write("PATH=%s\n" % (path))
        config.write("DESC=%s\n" % (desc))
        config.write("PLATFORM=%s\n" % (platform.name))
        config.close()

        # instantiate the project
        self.projects[name] = Project(path, name, platform)
        return self.projects[name]
    
    def delete_project(self, project):
        print "TODO: delete the project"
        
    def __str__(self):
        return ("<SDK Object: path=%s, platform=%s>" %
                (self.path, self.platforms))

if __name__ == '__main__':
    for path in sys.argv[1:]:
        print SDK(path)
