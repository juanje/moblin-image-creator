#!/usr/bin/python -tt

import ConfigParser, os, re, sys, unittest

class FSet(object):
    """
    An FSet object represents a functional set of packages to install in a
    target filesystem.  An FSet contains an array of package names in
    FSet.packages, an array of additional debug packages in
    FSet.debug_packages, and an array of dependant FSet names in FSet.deps.
    """
    def __init__(self):
        self.filenames = []
        self.__fsets = {}

    def addFile(self, filename):
        """Add a config file to the FSet"""
        filename = os.path.abspath(os.path.expanduser(filename))
        self.filenames.append(filename)
        self.__parseFile(filename)


    def __parseFile(self, filename):
        valid_values = { 'name' : '', 'desc' : '', 'pkgs' : [],
            'debug_pkgs' : [], 'deps' : [] }
        p = ConfigParser.ConfigParser()
        filenames = p.read(filename)
        for section in p.sections():
            orig_section = section
            section = section.lower()
            if section in self.__fsets:
                print "Error: Already have a section called: %s" % section
                print "Tried to add the section from file: %s" % filename
                print "But already have that section from file: %s" % self.__fsets[section]['filename']
                raise ValueError
            work_dict = {}
            work_dict['filename'] = filename
            for name, value in p.items(orig_section):
                name = name.lower()
                if name not in valid_values:
                    print "Found unsupported value, ignoring: %s %s" % (name, filename)
                    continue
                work_type = type(valid_values[name])
                if work_type == type([]):
                    value = value.split()
                elif work_type == type(''):
                    pass
                else:
                    print "Error: Unsupported type specified in valid_values"
                    print "Type was: %s" % work_type
                    raise ValueError
                work_dict[name] = value
            self.__fsets[section] = FsetInstance(section, work_dict)

    def __getitem__(self, key):
        return self.__fsets[key.lower()]
    def __iter__(self):
        return self.__fsets.__iter__()

    def __str__(self):
        return ('<data="%s">'
                % (self.__fsets))
    def __repr__(self):
        return "FSet()"

class FsetInstance(object):
    def __init__(self, name, data_dict):
        self.name = name.lower()
        self.data = data_dict
    def __getitem__(self, key):
        return self.data[key.lower()]
    def __getattr__(self, name):
        return self.data[name.lower()]
    def __repr__(self):
        return ('FsetInstance("%s", %s)' % (self.name, self.data))
    def __str__(self):
        return ('<fset name="%s" data="%s">' % (self.name, self.data))


class TestFset(unittest.TestCase):
    # FIXME: This stuff should probably be moved into a separate file which
    # creates fset files and then runs some tests using the created files.
    def testInstantiate(self):
        fset = FSet()
        fset.addFile("/usr/share/esdk/platforms/donley/fsets/donley.fset")
        if "blah" in fset:
            a = 1
        for key in fset:
            print key
    def testStrRepr(self):
        fset = FSet()
        temp = fset.__str__()
        temp = fset.__repr__()
        fset.addFile("/usr/share/esdk/platforms/donley/fsets/donley.fset")
        temp = fset['core'].__str__()
        temp = fset['core'].__repr__()


if __name__ == '__main__':
    if len(sys.argv) == 1:
        unittest.main()
        print >> sys.stderr, "USAGE: %s FSET_FILE ..." % (sys.argv[0])
    else:
        fset = FSet()
        for filename in sys.argv[1:]:
            fset.addFile(filename)
        print fset
        for key in fset.fsets:
            print
            print key, fset[key]
            print fset[key].filename, fset[key]['filename']
