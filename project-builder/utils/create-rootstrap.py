#!/usr/bin/python -tt
# vim: ai ts=4 sts=4 et sw=4

import sys, tempfile, subprocess, shutil

sys.path.insert(0, 'libs/')
import SDK, Project

class Callback:
    def iteration(self, process):
        return

if __name__ == '__main__':
    for platform_name in sys.argv[1:]:

        # Create a minimal project buildroot
        platform = SDK.SDK(cb = Callback()).platforms[platform_name]
        p = Project.Project(tempfile.mkdtemp(), platform.name, platform.name, platform, Callback())

        # install yum inside the project using the host tools
        cmd = 'yum -y --installroot=%s install yum' % p.path
        proc = subprocess.Popen(cmd.split(), stderr = subprocess.PIPE)
        if proc.wait() != 0:
            print >> sys.stderr, "ERROR: Unable to create %s rootstrap!" % (filename)
            for line in proc.stderr:
                print line.strip()
                sys.exit(1)

        # Create the rootstrap archive file
        cmd = "tar -jcpvf %s.tar.bz2 -C %s ." % (platform.name, p.path)
        proc = subprocess.Popen(cmd.split(), stderr = subprocess.PIPE)
        if proc.wait() != 0:
            print >> sys.stderr, "ERROR: Unable to create %s rootstrap!" % (filename)
            for line in proc.stderr:
                print line.strip()
                sys.exit(1)

        # cleanup the temporary project filesystem
        shutil.rmtree(p.path)
