#! /bin/sh
# define your target type, "suse" or "redhat"
#target="suse"
gitproj="OpenSuSE10.2"
target="redhat"
#gitproj="FC6"
gitbranch="UMD"

if [ "$target" == "redhat" ]; then
   rpmdir="redhat"
elif [ "$target" == "suse" ]; then
   rpmdir="redhat"
fi

# put your url and proxy configuration here
check_url1="http://linux-ftp.jf.intel.com/pub/mirrors/kernel.org/v2.6/"
check_url2="http://linux-ftp.jf.intel.com/pub/mirrors/kernel.org/v2.6/testing/"
#check_url1="http://www2.kernel.org/pub/linux/kernel/v2.6/"
#check_url2="http://www2.kernel.org/pub/linux/kernel/v2.6/testing/"
check_url3="http://people.redhat.com/mingo/realtime-preempt/"
myhttpproxy="xdu1-desk-linux.sh.intel.com:9110"

# set you umd-repo user name here
# before use the script, you must put you public key to umd-repo homedir/.ssh dir, thus no password input needs for ssh and scp operation
reposuser=xdu1
reposhost="$reposuser@umd-repo.jf.intel.com"
myremotedir="/home/repos/users/$reposuser"
myrepository="$myremotedir/$target"

# execution env
testmode="0"

if [ $testmode -eq 1 ]; then
   echo "test mode"
   mailto="alek.du@intel.com"
else
   echo "run mode"
   mailto="rob.rhoads@intel.com, feng.tang@intel.com, alek.du@intel.com"
fi

homedir=~
progdir=umd/kernelcron
PATH=$PATH:/usr/sbin:/sbin

# variables needs
newstamp=""
newver=""
stamp=""
ver=""
url=""
patch=""

# check env
cd $homedir/$progdir/
if [ $? -eq 1 ] ; then
   echo "Wrong when changing dir to $homedir/$progdir/"
   exit 1
fi
# check last time we got the "new" version 
if [ -e .oldtimestamp ]; then
    oldstamp=`cat .oldtimestamp`
fi
if [ -z "$oldstamp" ]; then
   echo "first time run!\n"
   oldstamp="1-Jan-2000"
fi

#set http_proxy if out side intel.com
HttpProxySetting() {
if [ -n "$(echo $1 | sed -n -e "/intel.com/p")" ]; then
   export http_proxy=""
else
   echo "set http proxy to $myhttpproxy..."
   export http_proxy="$myhttpproxy"
fi
}

# search new version on the web
SearchNewVersion() {
  HttpProxySetting $1
  rm -rf index.html
  curl -A "Mozila" $1 > index.html
  news=$(cat index.html | sed -n -e "/.tar.bz2/p" | tail -n 1);
  ver=$(echo $news | sed "s/.*\(linux-.*.tar.bz2\).*/\1/")
  stamp=$(echo $news | sed "s/.*\(..-...-.... ..:..\).*/\1/")
  echo "latest version at $1 is:"
  echo $stamp
  echo $ver

  s1=`date -d "$stamp" +%s`
  s2=`date -d "$2" +%s`
  if [ $s1 -gt $s2 ]; then
    echo "new version found against $2"
    return 1
  fi
    echo "not a new version against $2"
  return 0
}

SearchRTPatch() {
  HttpProxySetting $1
  rm -rf index.html
  curl -A "Mozila" $1 > index.html
  patch=$( cat index.html | sed -n -e "/patch-/p" | tail -n 1 | sed "s/.*\(patch-.*\)[\"<].*/\1/")
  [ -n "$patch" ] && echo "Found RT patch $patch at $1"
}

EmailNotification() {
  from="kernelbuild"
  msgdate=`date`
  to="$mailto"

  email=$(cat <<!
Date: $msgdate
From: $from
To: $to
Subject: kernel RPM auto build script report
Content-Type: text

################################################################################
This mail was generated by kernel RPM auto build script, do not reply this mail.
Any question please send mail to alek.du@intel.com instead.
################################################################################
Build info:

Build target is for $target.

The build for kernel version was $1.

Kernel version used:
$2

Patches applied:
$3
@RESTPATCH@

See build log for results:
$5

See build result (RPM, SRPM, tarball) under:
$6

Updated package-meta-data git repository:
$7

Browsable git repository here:
$8

_________________________________________________________________________________________
This automated email was generated by http://umd-repo.jf.intel.com/git/users/$reposuser/$target/scripts/kernelcron.sh
The build RPMS spec was based on http://umd-repo.jf.intel.com/git/users/$reposuser/$target/scripts/kernel-umd-source.spec.profile
!)
  echo "$email" | sed -e "s/@RESTPATCH@/$4/g" > $homedir/$progdir/msg.tmp
  cat $homedir/$progdir/msg.tmp | sendmail -t
}

# start search and hard work ...
SearchNewVersion "$check_url1" "$oldstamp"
if [ $?  -eq 1 ]; then
   echo "Formal release found new version, but need check rc release..."
   newstamp=$stamp
   newver=$ver
   url=$check_url1
   SearchNewVersion "$check_url2" "$stamp"
else SearchNewVersion "$check_url2" "$oldstamp"
fi

if [ $?  -eq 1 ]; then
   newstamp=stamp
   newver=ver
   url=$check_url2
fi

# direct hack here if you want to test the rest script
#newstamp="1-Jan-2008"
#newver="linux-2.6.20.tar.bz2"
#url=$check_url1

# start to update spec file and download tar ball to build SRPMS and RPMS
newurl=`echo $url |  sed -e "s/\//\x5c\x5c\x2f/g"`
echo $url
if [ -n "$newstamp" ]; then
   echo "at last, we found new version $newver!"
   echo "start to maintain remote server for upload purpose..."
   commands=$(cat <<!
       cd $myremotedir
       if [ ! -d $target ]; then
          mkdir $target
       fi
       cd $myrepository
       if [ ! -d logs ]; then 
          mkdir logs
       fi
       if [ ! -d scripts ]; then 
          mkdir scripts
       fi
       if [ ! -d RPMS ]; then
          mkdir RPMS
       fi
       if [ ! -d SRPMS ]; then
          mkdir SRPMS
       fi
       if [ ! -d tarball ]; then
          mkdir tarball
       fi
# let remote host do git stuff       
       if [ -d package-meta-data ]; then
          rm -rf package-meta-data
       fi
       git-clone -n -l /home/repos/$gitproj/package-meta-data.git package-meta-data       
       cd package-meta-data
       git-checkout $gitbranch
!)
   echo "$commands" > commands.sh
   scp commands.sh $reposhost:$myremotedir/
   ssh $reposhost "cd $myremotedir; sh commands.sh; rm commands.sh"
# save old patches info
   scp $reposhost:$myrepository/package-meta-data/Development/Sources/kernel-umd-source/specs/kernel-umd-source.spec kernel-umd-source.spec
   echo "getting patches info from spec file.."
   patches=$(cat kernel-umd-source.spec | sed -n -e "/Patch0/d" -e "/^Patch/p")
   patchesapply=$(cat kernel-umd-source.spec | sed -n -e "/^%patch0/d" -e "/^%patch/p")
   patches=$(echo $patches | sed -e "s/ Patch/\\\x0aPatch/g")
   patchesapply=$(echo $patchesapply | sed -e "s/ %patch/\\\x0a%patch/g")
   
#  split version string for spec.profile
   ver1=${newver%%.*}
   ver1=${ver1#linux-}
   ver2=${newver#linux-*.*}
   ver2=${ver2%%.*}
   ver3=${newver#linux-*.*.*}
   ver3=${ver3%%[.-]*}
   ver4=${newver#linux-*.*.$ver3*}
   ver4=${ver4%.tar.bz2}
   ver5=`echo $ver4 | sed -e "s/-/./g"`
   echo $ver1, $ver2, $ver3, $ver4

   echo "try to find coresponding RT_PREEMPT patch"
   SearchRTPatch "$check_url3"
   if [ -n "$patch" ]; then
      patchrt="Patch0: $patch"
      patchrtapply="%patch0 -p1"
      echo "downloading RT patch: $patch..."
      rm -rf $patch
      HttpProxySetting $check_url3
      wget --tries=10 $check_url3$patch 
   else
      patchrt=""
      patchrtapply=""
   fi
   echo "start to update kernel SRPM spec files and will download new kernel tar ball to build new RPMS"
   echo $patches
   (sed -e "s/@TARGET@/$target/g" \
        -e "s/@LEVEL@/$ver1.$ver2/g" \
        -e "s/@SUBLEVEL@/$ver3/g" \
        -e "s/@EXTRAVER@/$ver4/g" \
        -e "s/@EXTRAVER2@/$ver5/g" \
        -e "s/@URL@/$newurl/g" \
        -e "s/@PATCHRT@/$patchrt/g" \
        -e "s/@PATCHRTAPPLY@/$patchrtapply/g" \
        -e "s/@RESTPATCH@/$patches/g" \
        -e "s/@RESTPATCHAPPLY@/$patchesapply/g" \
        $homedir/$progdir/kernel-umd-source.spec.profile
   )> kernel-umd-source.spec
   echo "start to download new kernel at $url$newver"
   if [ $testmode -eq 0 ]; then
      rm -rf $newver
      HttpProxySetting $url
      wget --tries=10 $url$newver
   else
      echo "test mode, will not download kernel actually"
   fi   
   if [ $? -eq 0 ]; then
      echo "download successfully!"
      echo "start to build SRPM and RPMS"
      scp $reposhost:$myrepository/package-meta-data/Development/Sources/kernel-umd-source/files/* /usr/src/$rpmdir/SOURCES/
      cp kernel-umd-source.spec /usr/src/$rpmdir/SPECS/
      cp $newver $patch /usr/src/$rpmdir/SOURCES/
      cd /usr/src/$rpmdir
      rm -rf /usr/src/$rpmdir/RPMS/*
      rm -rf /usr/src/$rpmdir/SRPMS/*
      rm /usr/src/$rpmdir/*.log
      logfile=build-linux-$ver1.$ver2.$ver3$ver4-$(date +%Y%m%d%H%M).log
      if [ $testmode -eq 0 ]; then
         rpmbuild -ba ./SPECS/kernel-umd-source.spec > $logfile 2>&1
      else
         echo "in test mode, do not call rpmbuild"
      fi
      buildresult=$?
      echo "Build endtime $(date)" >> $logfile
      echo "uploading build result to server..."
      scp /usr/src/$rpmdir/$logfile $reposhost:$myrepository/logs/
# copy to remote package-meta-data for commit
      cd $homedir/$progdir/
      scp kernel-umd-source.spec.profile $reposhost:$myrepository/scripts/
      scp kernelcron.sh $reposhost:$myrepository/scripts/
      scp kernel-umd-source.spec $reposhost:$myrepository/package-meta-data/Development/Sources/kernel-umd-source/specs/
      ssh $reposhost "cd $myrepository/package-meta-data;git-update-index Development/Sources/kernel-umd-source/specs/kernel-umd-source.spec"
      if [ -n "$patch" ]; then
         scp $patch $reposhost:$myrepository/package-meta-data/Development/Sources/kernel-umd-source/files/
         ssh $reposhost "cd $myrepository/package-meta-data;git-update-index --add Development/Sources/kernel-umd-source/files/$patch"
      fi
      ssh $reposhost "cd $myrepository/package-meta-data;git-commit -a -m \"kernel auto build script check in for new kernel version\";git-update-server-info;[ -d ../package-meta-data.git ] && rm -rf ../package-meta-data.git;mv .git ../package-meta-data.git;cd ..; rm -rf package-meta-data"
      if [ $testmode -eq 0 ]; then
         scp $newver $reposhost:$myrepository/tarball
      fi   

      if [ $buildresult -eq 0 ]; then
# report good news to team
         echo "build successfully finished!"
         echo "uploading RPMS/SRPMS to server..."
         scp -r /usr/src/$rpmdir/RPMS $reposhost:$myrepository/
         scp -r /usr/src/$rpmdir/SRPMS $reposhost:$myrepository/
         echo "$newstamp" > .oldtimestamp
         echo "Email to CoreOS members..."
         EmailNotification "successful" "$url$newver" "$check_url3$patch" $(echo $patches | sed -e "s/Patch.\{1,5\}: //g") \
                           "http://umd-repo.jf.intel.com/git/users/$reposuser/$target/logs/$logfile" \
                           "http://umd-repo.jf.intel.com/git/users/$reposuser/$target/" \
                           "http://umd-repo.jf.intel.com/git/users/$reposuser/$target/package-meta-data.git/" \
                           "http://umd-repo.jf.intel.com/repos/?p=users/$reposuser/$target/package-meta-data.git;a=shortlog;h=$gitbranch"
# report bad news to team
      else
         echo "bad news: RPM build failed!"
         echo "Email to CoreOS members..."
         EmailNotification "failed" "$url$newver" "$check_url3$patch" $(echo $patches | sed -e "s/Patch.\{1,5\}: //g") \
                           "http://umd-repo.jf.intel.com/git/users/$reposuser/$target/logs/$logfile" \
                           "http://umd-repo.jf.intel.com/git/users/$reposuser/$target/" \
                           "http://umd-repo.jf.intel.com/git/users/$reposuser/$target/package-meta-data.git/" \
                           "http://umd-repo.jf.intel.com/repos/?p=users/$reposuser/$target/package-meta-data.git;a=shortlog;h=$gitbranch"
      fi
      exit 0
   fi   
   echo "download kernel version error!"
   exit 1
fi

echo "No new version found!"
exit 0
