#!/usr/bin/python
# vim: ai ts=4 sts=4 et sw=4

# The idea for this library is to make functions that help in working with our
# source code repository.

import ConfigParser
import datetime
import os
import re
import rpm
import shutil
import stat
import sys
import tarfile
import time

def main():
    print "This is only a library"

debug = False
#debug = True

def findPackages(config_info, dirname = None):
    """Given a cBuildConfigInstance object.  Find all the packages in the
    source repository"""
    if dirname == None:
        dirname = config_info['packages_dir']
    package_dict = {}
    for filename in os.listdir(dirname):
        full_path = os.path.join(dirname, filename)
        if not os.path.isdir(full_path):
            continue
        if filename == "specs":
            try:
                package_info = cPackageInfo(dirname, config_info)
            except ValueError, error_msg:
                multipleSpecFilesError(base_dirname, dirname, error_msg)
                continue
            package_name = package_info.name
            if package_name in package_dict:
                print "Duplicate package name found: %s" % package_name, package_info
                print package_dict[package_name]
            package_dict[package_name] = package_info
            continue
        if filename == "files" or filename == "src":
            continue
        if os.path.isdir(full_path):
            package_dict.update(findPackages(config_info, dirname = full_path))
    return package_dict

def getFilesInDirectory(dirname):
    """Return a list object containing the full path names of all the files in a directory"""
    out_list = []
    if not dirname:
        return out_list
    dirname = os.path.abspath(dirname)
    if not os.path.isdir(dirname):
        return out_list
    for filename in os.listdir(dirname):
        full_path = os.path.join(dirname, filename)
        out_list.append(full_path)
    return out_list

def getNewestFileDate(file_list):
    """Return the date/time of the file that was most recently modified"""
    newest_date = datetime.datetime.min
    for filename in file_list:
        stat_info = os.stat(filename)
        file_time = datetime.datetime.fromtimestamp(stat_info[stat.ST_MTIME])
        newest_date = max(file_time, newest_date)
    return newest_date

def readLineFromFile(filename):
    """Simple helper to read the first line of a file and return it back as a
    stripped string"""
    in_file = open(filename, 'r')
    out_string = ""
    for line in in_file:
        out_string += "%s " % line.strip()
    return out_string.strip()

class cPackageInfo:
    def __init__(self, dirname, config_info):
        self.config_info = config_info
        self.info = {}
        dirname = os.path.abspath(dirname)
        if not os.path.isdir(dirname):
            raise ValueError("%s is NOT a directory" % dirname)
        self.dirname = dirname
        files = os.listdir(dirname)
        if 'specs' not in files or 'info' not in files:
            raise ValueError("'specs' or 'info' directories not found in: %s" % dirname)
        info_dir = os.path.join(dirname, "info")
        for filename in os.listdir(info_dir):
            full_name = os.path.join(info_dir, filename)
            self.info[filename] = readLineFromFile(full_name)
        self.name = self.info['name']
        self.version = self.info['version']
        self.release = self.info['release']

        self.tarball_dir = self.getPristineForPackage()

        spec_dir = os.path.join(dirname, "specs")
        self.specfile = getFilesInDirectory(spec_dir)[0]
        if len(os.listdir(spec_dir)) > 1:
            raise ValueError("Multiple Specfiles found: %s" % dirname)
        src_dir = os.path.join(dirname, "src")
        if os.path.isdir(src_dir):
            self.src_dir = src_dir
        else:
            self.src_dir = None
        file_dir = os.path.join(dirname, "files")
        self.file_dir = file_dir
        temp_file_list = self.getSourceFiles()
        self.lastmodified = max(getNewestFileDate(temp_file_list), getNewestFileDate([self.specfile]))

    def ownsPath(self, path_name):
        """Returns true if this package owns the specified path"""
        path_name = os.path.abspath(path_name)
        if path_name.find(self.dirname) == 0:
            return True
        return False

    def __repr__(self):
        return self.name
        out_string = ""
        keys = self.info.keys()
        keys.sort()
        for key in keys:
            out_string += "%10s\t%s\n" % (key, self.info[key])
        return out_string

    def __str__(self):
        return "Package Info(name = '%s', dirname = '%s')" % (self.name, self.dirname)

    def __setitem__(self, key, value):
        self.info[key] = value

    def __getitem__(self, key):
        return self.info[key]

    def __cmp__(self, other):
        return cmp(self.name, other.name)

    def tarSrcDirectoryAndCopy(self, dest_dir):
        if not self.src_dir:
            return
        name = "%s-%s" % (self.name, self.version)
        tarball_name = os.path.join(dest_dir, "%s.tgz" % name)
        tar_obj = tarfile.open(tarball_name, 'w:gz')
        tar_obj.add(self.src_dir, name)
        tar_obj.close()

    def copySpecFile(self, dest_dir):
        if debug: print "Copying: %s -> %s" % (self.specfile, dest_dir)
        shutil.copy(self.specfile, dest_dir)

    def getSourceFiles(self):
        """Return back a list of all the files associated with this package,
        except the spec file"""
        file_list = getFilesInDirectory(self.file_dir)
        file_list.extend(getFilesInDirectory(self.tarball_dir))
        return file_list

    def copySources(self, dest_dir):
        file_list = self.getSourceFiles()
        for filename in file_list:
            if not os.path.isfile(filename):
                return False
            if debug: print "Copying: %s -> %s" % (filename, dest_dir)
            shutil.copy(filename, dest_dir)
        return True

    def getPristineForPackage(self):
        """Figure out the pristine files directory (in the PRISTINE_SOURCE
        directory) for this package"""
        # Get the part which is not the meta data dir
        basedir = self.dirname.split(self.config_info['packages_dir'])[1]
        # Also remove the package name from the directory, since that package name
        # contains the version also
        basedir = ".%s" % os.path.split(basedir)[0]
        package_name = self.name
        if not package_name:
            raise ValueError("Empty name file: %s" % package_info['dirname'])
        tarball_dir = os.path.normpath(os.path.join(self.config_info['pristine_dir'], basedir, package_name))
        return tarball_dir

class cBuildConfig:
    value_mapping = { 'source_repo' : 'dir', 'pristine_dir' : 'dir',
        'status_dir' : 'dir', 'packages_dir' : 'dir', 'pristine_repo' : 'str'}
    def __init__(self, config_file):
        self.instances = {}
        self.config_file = os.path.abspath(config_file)
        self.configparser = ConfigParser.SafeConfigParser()
        self.configparser.read(config_file)
        # Make sure to validate before doing anything else
        self.validateItems()
        for section in self.configparser.sections():
            items = self.configparser.items(section)
            self.instances[section] = cBuildConfigInstance(section, items)

    def __repr__(self):
        return "cBuildConfig(%s)" % self.instances
    def __iter__(self):
        return self.configparser.sections().__iter__()

#    def __getattr__(self, name):
#        return cBuildConfigInstance(self.configparser.items(name))

    def __getitem__(self, key):
        return self.instances[key]
    
    def validateItems(self):
        sections = self.configparser.sections()
        sections.append('DEFAULT')
        for section in sections:
            items = self.configparser.items(section)
            for name, value in items:
                if name not in cBuildConfig.value_mapping:
                    raise ValueError("Invalid name: %s" % name)
                val_type = cBuildConfig.value_mapping[name]
                if val_type == 'dir':
                    value = os.path.abspath(os.path.expanduser(value))
                    self.configparser.set(section, name, value)
                    if not os.path.isdir(value):
                        raise ValueError("%s is not a directory" % value)

class cBuildConfigInstance:
    def __init__(self, name, items):
        self.work_dict = {}
        for key, value in items:
            self.work_dict[key] = value
        self.revision_filename = os.path.join(self.work_dict['status_dir'], '%s.status' % name)
        try:
            self.last_revision = readLineFromFile(self.revision_filename)
        except IOError:
            self.last_revision = None

    def __iter__(self):
        return self.work_dict.__iter__()
#    def __getattr__(self, name):
#        return self.work_dict[name]
    def __getitem__(self, key):
        return self.work_dict[key]
    def __str__(self):
        return self.work_dict.__str__()
    def getLastRevision(self):
        return self.last_revision
    
    def setLastRevision(self, revision):
        if revision != self.last_revision:
            self.last_revision = revision
            out_file = open(self.revision_filename, 'w')
            out_file.write("%s\n" % self.last_revision)
            out_file.close()

if '__main__' == __name__:
    sys.exit(main())
