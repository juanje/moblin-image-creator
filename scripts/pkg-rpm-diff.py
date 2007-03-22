#!/usr/bin/python
# vim: ai ts=4 sts=4 et sw=4

import sys, re, os, time, commands, shutil, glob

# TEMP_DIR should be absolute path
TEMP_DIR = "/tmp"

# RPM_DIFF is the file where the output is saved
RPM_DIFF = "./rpmdiffs"

def rpm_query(infile) :
    oinfo = []
    QUERY_CMD = "rpm -qpl --dump %s" % infile
    output = commands.getoutput(QUERY_CMD)
    t = output.splitlines()
    for i in t :
        f = i.split()
        # ignore docs and symlinks and directories
        if f[8] == "1" or f[3] == "00000000000000000000000000000000" :
            continue
        oinfo.append(f)
#       print oinfo
    return oinfo

def rpm_compare(rpm_name):

    RPM_QUERY_STR = "rpm -q -p --queryformat '%%{name}' %s" % rpm_name
    pkg_name = commands.getoutput(RPM_QUERY_STR)
    print "looking up pakage '%s' in yum repository:" % pkg_name

    YUM_CMD = "yum list %s" % pkg_name
    status, output = commands.getstatusoutput(YUM_CMD)
#print "%s\n" % output

    pkg_notfound = []
    available = False
    t = output.splitlines()
    for line in t :
        if line == "Installed Packages" or line == "Available Packages" :
            available = True

    if not available :
        print "\tpackage '%s' not found in yum repository.\n" % pkg_name
        return False

    print "\tpackage '%s' found in yum repository.\n" % pkg_name

    print "downloading package from yum repository to %s:" % TEMP_DIR
    YUMDL_URL_CMD = "yumdownloader --url %s" % pkg_name
    output = commands.getoutput(YUMDL_URL_CMD)
#print output
    orig_rpm_name = output.rsplit('/', 1)
    orig_rpm_name.reverse()
#print orig_rpm_name

    YUMDL_CMD = "yumdownloader --destdir=%s %s" % (TEMP_DIR, pkg_name)
    output = commands.getoutput(YUMDL_CMD)
#print output
    ORIG_RPM = "%s/%s" % (TEMP_DIR, orig_rpm_name[0])
#print ORIG_RPM
    if not os.path.exists(ORIG_RPM) :
        print "\tyumdownloader failed to download the rpm.\n"
        sys.exit(1)
    print "\trpm downloaded: %s\n" % ORIG_RPM

    print "comparing the package with the original: "

    oinfo = []
    oinfo = rpm_query(ORIG_RPM)

    ninfo = []
    ninfo = rpm_query(rpm_name)

    lfile = open(RPM_DIFF, 'a')

    for i in ninfo :
        ffound = False
        match = False
        for j in oinfo :
            if i[0] == j[0] :
            # file name found
                ffound = True
                if i[3] != j[3] :
                    print "    %s MD5 differ from the original" % i[0]
                    OUTPUT = "%s, %s, %s" % (pkg_name, i[0], 'MD5 mismatch')
                    lfile.write("%s\n" % OUTPUT)
                else :
                    match = True
        if ffound == False :
            print "    %s not found in the original" % i[0]
            OUTPUT = "%s, %s, %s" % (pkg_name, i[0], 'not found in original')
            lfile.write("%s\n" % OUTPUT)

    lfile.close()

    print "\n\n"
    return True

if len(sys.argv) != 2 or not os.path.isdir(sys.argv[1]) :
    print "%s: RPM_DIR" % sys.argv[0]
    sys.exit(1)

rpm_dir_name = sys.argv[1]
dir = "%s/*" % rpm_dir_name
#dir = os.path.abspath(dir)
rpm_list = glob.glob(dir)

found = True
original_rpm_list = []
for i in rpm_list :
    found = rpm_compare(i)
    if not found :
        original_rpm_list.append(i)

print "The list of rpms that are not found in the yum repository:"
print original_rpm_list
