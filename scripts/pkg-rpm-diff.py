#!/usr/bin/python
# vim: ai ts=4 sts=4 et sw=4

import commands, os, re, shutil, sys, tempfile, time

# Create a temporary directory
TEMP_DIR = tempfile.mkdtemp()

# RPM_DIFF is the file where the output is saved
RPM_DIFF = os.path.abspath("rpmdiffs")

def getAvailableRpms():
    command_line = "repoquery -qa --queryformat '%{name}'"
    status, output = commands.getstatusoutput(command_line)
    if status:
        print "Error running command: %s" % command_line
        print output
        sys.exit(1)
    rpm_list = output.splitlines()
    return rpm_list

def rpm_query(infile):
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

def rpm_compare(rpm_name, repo_rpms):
    RPM_QUERY_STR = "rpm -q -p --queryformat '%%{name}' %s" % rpm_name
    pkg_name = commands.getoutput(RPM_QUERY_STR)
    print "looking up package '%s' in yum repository:" % pkg_name

    if pkg_name not in repo_rpms:
        print "\tpackage '%s' not found in yum repository.\n" % pkg_name
        return False

    print "\tpackage '%s' found in yum repository.\n" % pkg_name

    print "downloading package from yum repository to %s:" % TEMP_DIR
    YUMDL_URL_CMD = "yumdownloader --url %s" % pkg_name
    status, output = commands.getstatusoutput(YUMDL_URL_CMD)
    if status:
        print "Error running command: %s" % YUMDL_URL_CMD
        print output
        sys.exit(1)
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
        print output
        sys.exit(1)
    print "\trpm downloaded: %s\n" % ORIG_RPM

    print "comparing the package with the original: "

    oinfo = rpm_query(ORIG_RPM)

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

def main():
    if len(sys.argv) != 2:
        print "Usage: %s: RPM_DIR" % sys.argv[0]
        return 1

    rpm_dir_name = os.path.abspath(os.path.expanduser(sys.argv[1]))
    if not os.path.isdir(rpm_dir_name):
        print "%s: is not a directory" % rpm_dir_name
        return 1

    repo_rpms = getAvailableRpms()
    original_rpm_list = []
    for filename in os.listdir(rpm_dir_name):
        full_path = os.path.join(rpm_dir_name, filename)
        found = rpm_compare(full_path, repo_rpms)
        if not found:
            original_rpm_list.append(filename)

    print "The list of rpms that are not found in the yum repository:"
    print original_rpm_list
    print "Deleting temp_dir: %s" % TEMP_DIR
    shutil.rmtree(TEMP_DIR)

if '__main__' == __name__:
    sys.exit(main())
