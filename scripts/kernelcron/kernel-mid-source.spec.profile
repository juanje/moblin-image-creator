# spec file for kernel-mccaslin (Version @LEVEL@.@SUBLEVEL@@EXTRAVER@)
# Copyright (c) 2007, Intel Corp.
# This file and all modifications and additions to the pristine
# package are under the same license as the package itself.

# build for redhat or suse ?
%define target @TARGET@

# build environment
%define level @LEVEL@
%define sublevel @SUBLEVEL@
%define kversion %{level}.%{sublevel}
%define krelease %{kversion}@EXTRAVER@

%define all_mid_configs $RPM_SOURCE_DIR/kernel-*.config
%define buildflavors default developer

# we only let linux on i386 and x86_64 platform to build this package
ExclusiveArch: i586 x86_64
ExclusiveOs: linux

# primary package definition
Name: kernel-mid-source
License: GPL
Provides: Linux
Autoreqprov: off
Summary: MID kernel-source
Group: Development/Sources
PreReq: /bin/grep /bin/sed /bin/uname /bin/mkdir /bin/cat /bin/ln /bin/rm
Version: %{kversion}@EXTRAVER2@
@RELEASE@

BuildPreReq: nash, module-init-tools, gzip

# put sources here
Source0: @URL@linux-%{krelease}.tar.bz2
Source1: functions.sh
Source2: post.sh
Source3: postun.sh
Source4: source-post.sh
Source5: kabitool
Source6: kernel-default.config
Source7: kernel-developer.config
Source8: init
Source9: initrd_skeleton
Source10: installkernel.sh

# put patches here for MID add-on
# and do NOT forget to apply patches in setup section -- search "apply patches" in this file
# the patch0 is reserved for RT_PREEMPT
@PATCHRT@
@RESTPATCH@

# build attributes
BuildRoot: %_tmppath/%name-%version-build
AutoReq: no
AutoProv: yes

%description
This is kernel version special for Intel MID release.

# generate kernel code RPM patched with MID patches
%files
%defattr(-, root, root)
%ghost    /usr/src/linux
/usr/src/linux-%{krelease}

%post -f source-post.sh

# package for kernel headers
%package -n kernel-mid-headers
Summary:    mid kernel headers
Group:	    Development/System
Obsoletes:  glibc-kernheaders
Provides:   glibc-kernheaders = 3.0-46

%description -n kernel-mid-headers
Kernel-headers includes the C header files that specify the interface
between the Linux kernel and userspace libraries and programs.  The
header files define structures and constants that are needed for
building most standard programs and are also needed for rebuilding the
glibc package.

%files -n kernel-mid-headers
%defattr(-,root,root)
/usr/include/*

# package for default 
%package -n kernel-mid-default
Summary:    default built kernel binary package
Group:       System/Kernel
Provides:    kernel = %{krelease}

%description -n kernel-mid-default
This is kernel version special for Intel MID release.

%files -n kernel-mid-default
%defattr(-, root, root)
/boot/vmlinuz-%{krelease}-default
/boot/vmlinux-%{krelease}-default
/boot/System.map-%{krelease}-default
/boot/symvers-%{krelease}-default.gz
/boot/config-%{krelease}-default
%dir /lib/modules/%{krelease}-default
/lib/modules/%{krelease}-default/kernel
/lib/modules/%{krelease}-default/build
/lib/modules/%{krelease}-default/source
/lib/modules/%{krelease}-default/extra
/lib/modules/%{krelease}-default/updates
/lib/modules/%{krelease}-default/weak-updates
%if "%{target}" == "redhat"
/boot/initrd-%{krelease}-default.img
%else
/boot/initrd-%{krelease}-default
%endif
%ghost /boot/vmlinux
/usr/src/kernels/%{krelease}-default-%{_target_cpu}

# package for developer 
%package -n kernel-mid-developer
Summary:    mid developer built kernel binary package
Group:       System/Kernel
Provides:    kernel = %{krelease}

%description -n kernel-mid-developer
This is kernel version special for Intel MID release.

%files -n kernel-mid-developer
%defattr(-, root, root)
/boot/vmlinuz-%{krelease}-developer
/boot/vmlinux-%{krelease}-developer
/boot/System.map-%{krelease}-developer
/boot/symvers-%{krelease}-developer.gz
/boot/config-%{krelease}-developer
%dir /lib/modules/%{krelease}-developer
/lib/modules/%{krelease}-developer/kernel
/lib/modules/%{krelease}-developer/build
/lib/modules/%{krelease}-developer/source
/lib/modules/%{krelease}-developer/extra
/lib/modules/%{krelease}-developer/updates
/lib/modules/%{krelease}-developer/weak-updates
%if "%{target}" == "redhat"
/boot/initrd-%{krelease}-developer.img
%else
/boot/initrd-%{krelease}-developer
%endif
%ghost /boot/vmlinux
/usr/src/kernels/%{krelease}-developer-%{_target_cpu}

%install
if [ "%{target}" == "redhat" ]; then
(   echo "rm -f /usr/src/linux; ln -s linux-%{krelease} /usr/src/linux"
) > ../source-post.sh
# redhat source-post.sh must be in %_builddir while suse one must be in %_builddir/%{name}-{%release}
(cat %_sourcedir/installkernel.sh
 echo "$(cat <<!
  if [ `uname -i` == "x86_64" -o `uname -i` == "i386" ]; then
   if [ -f /etc/sysconfig/kernel ]; then
    /bin/sed -i -e 's/^DEFAULTKERNEL=kernel-smp$/DEFAULTKERNEL=kernel/' /etc/sysconfig/kernel || exit $?
   fi
  fi
  if [ -x /sbin/new-kernel-pkg ]; then
     /sbin/new-kernel-pkg --package kernel --depmod --install %{krelease}-default || exit $?
  else
    installkernel %{krelease}-default 
    /sbin/depmod %{krelease}-default
  fi
  if [ -x /sbin/weak-modules ]
  then
    /sbin/weak-modules --add-kernel %{krelease}-default || exit $?
  fi
  rm -f /boot/vmlinux;
  ln -s vmlinux-%{krelease}-default /boot/vmlinux
!)"
) > ../post-default.sh
(cat %_sourcedir/installkernel.sh
 echo "$(cat <<!
  if [ `uname -i` == "x86_64" -o `uname -i` == "i386" ]; then
   if [ -f /etc/sysconfig/kernel ]; then
    /bin/sed -i -e 's/^DEFAULTKERNEL=kernel-smp$/DEFAULTKERNEL=kernel/' /etc/sysconfig/kernel || exit $?
   fi
  fi
  if [ -x /sbin/new-kernel-pkg ]; then
     /sbin/new-kernel-pkg --package kernel --depmod --install %{krelease}-developer || exit $?
  else
     installkernel %{krelease}-developer
     /sbin/depmod %{krelease}-developer
     installkernel %{krelease}-developer --withserial
  fi
  updatedeveloperetc
  if [ -x /sbin/weak-modules ]
  then
    /sbin/weak-modules --add-kernel %{krelease}-developer || exit $?
  fi
  rm -f /boot/vmlinux;
  ln -s vmlinux-%{krelease}-developer /boot/vmlinux
!)"
) > ../post-developer.sh
else
(   cat %_sourcedir/functions.sh
    sed -e "s:@KERNELRELEASE@:%{krelease}:g" %_sourcedir/source-post.sh
) > source-post.sh
(   cat %_sourcedir/functions.sh
    echo "rm -f /boot/vmlinux; ln -s vmlinux-%{krelease}-default /boot/vmlinux"
    sed -e "s:@KERNELRELEASE@:%{krelease}-default:g" \
	-e "s:@IMAGE@:vmlinuz:g" \
	-e "s:@FLAVOR""@:default:g" \
        %_sourcedir/post.sh
) > post-default.sh

(   cat %_sourcedir/functions.sh
    sed -e "s:@KERNELRELEASE@:%{krelease}-default:g" \
	-e "s:@IMAGE@:vmlinuz:g" \
	-e "s:@FLAVOR""@:default:g" \
        %_sourcedir/postun.sh
) > postun-default.sh
(   cat %_sourcedir/functions.sh
    echo "rm -f /boot/vmlinux; ln -s vmlinux-%{krelease}-developer /boot/vmlinux"
    sed -e "s:@KERNELRELEASE@:%{krelease}-developer:g" \
	-e "s:@IMAGE@:vmlinuz:g" \
	-e "s:@FLAVOR""@:developer:g" \
        %_sourcedir/post.sh
) > post-developer.sh

(   cat %_sourcedir/functions.sh
    sed -e "s:@KERNELRELEASE@:%{krelease}-developer:g" \
	-e "s:@IMAGE@:vmlinuz:g" \
	-e "s:@FLAVOR""@:developer:g" \
        %_sourcedir/postun.sh
) > postun-developer.sh
fi

%post -n kernel-mid-default -f post-default.sh

%post -n kernel-mid-developer -f post-developer.sh

%if "%{target}" != "redhat"
%postun -n kernel-mid-developer -f postun-developer.sh
%postun -n kernel-mid-default -f postun-default.sh
%endif

# =====================Prepare==========================
# here start to unpack kernel and apply patch against it
%prep
echo        "Start to build kernel RPMS for MID Release"
echo        "possible configs are:"
for i in %{all_mid_configs}
do
    echo $i
done

if ! [ -e %_sourcedir/linux-%{krelease}.tar.bz2 ]; then
    echo "Please get a copy of linux-%{krelease}.tar.bz2 from @URL@."
fi

%setup -q -n %{name}-%{krelease} -c
# change the directory name to our desired version name
cd %_builddir/%{name}-%{krelease}
cd linux-%{krelease}

# apply patches
@PATCHRTAPPLY@
@RESTPATCHAPPLY@

# =========================Build============================
# here start to build kernel and copy results to right place
%build
rm -rf $RPM_BUILD_ROOT
mkdir -p $RPM_BUILD_ROOT/boot
ln -sf vmlinux $RPM_BUILD_ROOT/boot/vmlinux
mkdir -p $RPM_BUILD_ROOT/usr/src
cd $RPM_BUILD_ROOT/usr/src
# dummy link for %ghost
ln -sf linux linux 
# copy the already patched kernel to $RPM_BUILD_ROOT/usr/src to generate primary package kernel-source
cp -r %_builddir/%{name}-%{krelease}/linux-%{krelease} ./
buildheaders="1"

# start to compile kernel in several flavor
for flavor in %{buildflavors}; do
# enter the builddir and do something :-(
    cd %_builddir/%{name}-%{krelease}/linux-%{krelease}
    arch=%{_arch}
    kernelver=%{krelease}-$flavor
    develdir=/usr/src/kernels/$kernelver-%{_target_cpu}

# patch Makefile here to generate correct version
    perl -p -i -e "s/^EXTRAVERSION.*/EXTRAVERSION = @EXTRAVER@/" Makefile
# exec make   
    make mrproper
    cp $RPM_SOURCE_DIR/kernel-$flavor.config .config
# patch .config file to generate correct localversion
    perl -p -i -e "s/^CONFIG_LOCALVERSION.*/CONFIG_LOCALVERSION=\"-$flavor\"/" .config 
    kernelimg=arch/$arch/boot/bzImage    
    yes '' | make ARCH=$arch oldconfig
#   make ARCH=$arch silentoldconfig > /dev/null
    make %{?jobs:-j%jobs} ARCH=$arch bzImage
    make %{?jobs:-j%jobs} ARCH=$arch modules
    
    install -m 644 .config $RPM_BUILD_ROOT/boot/config-$kernelver
    install -m 644 System.map $RPM_BUILD_ROOT/boot/System.map-$kernelver
    cp $kernelimg $RPM_BUILD_ROOT/boot/vmlinuz-$kernelver
    cp vmlinux $RPM_BUILD_ROOT/boot/vmlinux-$kernelver
    mkdir -p $RPM_BUILD_ROOT/lib/modules/$kernelver
    make ARCH=$arch INSTALL_MOD_PATH=$RPM_BUILD_ROOT modules_install KERNELRELEASE=$kernelver
    if [ "$buildheaders" == "1" ]; then
       make ARCH=$arch INSTALL_HDR_PATH=$RPM_BUILD_ROOT/usr headers_install
       buildheaders="0"
# glibc provides scsi headers for itself, for now
       rm -rf $RPM_BUILD_ROOT/usr/include/scsi
       rm -f $RPM_BUILD_ROOT/usr/include/asm*/atomic.h
       rm -f $RPM_BUILD_ROOT/usr/include/asm*/io.h
       rm -f $RPM_BUILD_ROOT/usr/include/asm*/irq.h
    fi;
# Create the kABI metadata for use in packaging
    echo "**** GENERATING kernel ABI metadata ****"
    gzip -c9 < Module.symvers > $RPM_BUILD_ROOT/boot/symvers-$kernelver.gz
    chmod 0755 %_sourcedir/kabitool
    %_sourcedir/kabitool -b $RPM_BUILD_ROOT/$develdir -k $kernelver -l $RPM_BUILD_ROOT/kabi_whitelist
    rm -f %{_tmppath}/kernel-$KernelVer-kabideps
    %_sourcedir/kabitool -b . -d %{_tmppath}/kernel-$kernelver-kabideps -k $kernelver -w $RPM_BUILD_ROOT/kabi_whitelist
# and save the headers/makefiles etc for building modules against   
    rm -f $RPM_BUILD_ROOT/lib/modules/$kernelver/build
    rm -f $RPM_BUILD_ROOT/lib/modules/$kernelver/source
    mkdir -p $RPM_BUILD_ROOT/lib/modules/$kernelver/build
    (cd $RPM_BUILD_ROOT/lib/modules/$kernelver ; ln -s build source)
# dirs for additional modules per module-init-tools, kbuild/modules.txt
    mkdir -p $RPM_BUILD_ROOT/lib/modules/$kernelver/extra
    mkdir -p $RPM_BUILD_ROOT/lib/modules/$kernelver/updates
    mkdir -p $RPM_BUILD_ROOT/lib/modules/$kernelver/weak-updates
# first copy everything
    cp --parents `find  -type f -name "Makefile*" -o -name "Kconfig*"` $RPM_BUILD_ROOT/lib/modules/$kernelver/build
    cp Module.symvers $RPM_BUILD_ROOT/lib/modules/$kernelver/build
    mv $RPM_BUILD_ROOT/kabi_whitelist $RPM_BUILD_ROOT/lib/modules/$kernelver/build
    cp symsets-$kernelver.tar.gz $RPM_BUILD_ROOT/lib/modules/$kernelver/build
# then drop all but the needed Makefiles/Kconfig files
    rm -rf $RPM_BUILD_ROOT/lib/modules/$kernelver/build/Documentation
    rm -rf $RPM_BUILD_ROOT/lib/modules/$kernelver/build/scripts
    rm -rf $RPM_BUILD_ROOT/lib/modules/$kernelver/build/include
    cp .config $RPM_BUILD_ROOT/lib/modules/$kernelver/build
    cp -a scripts $RPM_BUILD_ROOT/lib/modules/$kernelver/build
    if [ -d arch/$arch/scripts ]; then
      cp -a arch/$arch/scripts $RPM_BUILD_ROOT/lib/modules/$kernelver/build/arch/$arch || :
    fi
    if [ -f arch/$arch/*lds ]; then
      cp -a arch/$arch/*lds $RPM_BUILD_ROOT/lib/modules/$kernelver/build/arch/$arch/ || :
    fi
    rm -f $RPM_BUILD_ROOT/lib/modules/$kernelver/build/scripts/*.o
    rm -f $RPM_BUILD_ROOT/lib/modules/$kernelver/build/scripts/*/*.o
    mkdir -p $RPM_BUILD_ROOT/lib/modules/$kernelver/build/include
    cd include
    cp -a acpi config keys linux math-emu media mtd net pcmcia rdma rxrpc scsi sound video asm asm-generic $RPM_BUILD_ROOT/lib/modules/$kernelver/build/include
    cp -a `readlink asm` $RPM_BUILD_ROOT/lib/modules/$kernelver/build/include
    if [ "$arch" = "x86_64" ]; then
      cp -a asm-i386 $RPM_BUILD_ROOT/lib/modules/$kernelver/build/include
    elif [ "$arch" = "i386" ]; then
      cp -a asm-x86_64 $RPM_BUILD_ROOT/lib/modules/$kernelver/build/include
    fi
# remove files that will be auto generated by depmod at rpm -i time
    rm -f $RPM_BUILD_ROOT/lib/modules/$kernelver/modules.*
# Make sure the Makefile and version.h have a matching timestamp so that
# external modules can be built
    touch -r $RPM_BUILD_ROOT/lib/modules/$kernelver/build/Makefile $RPM_BUILD_ROOT/lib/modules/$kernelver/build/include/linux/version.h
    touch -r $RPM_BUILD_ROOT/lib/modules/$kernelver/build/.config $RPM_BUILD_ROOT/lib/modules/$kernelver/build/include/linux/autoconf.h
# Copy .config to include/config/auto.conf so "make prepare" is unnecessary.
    cp $RPM_BUILD_ROOT/lib/modules/$kernelver/build/.config $RPM_BUILD_ROOT/lib/modules/$kernelver/build/include/config/auto.conf
# Move the devel headers out of the root file system
    mkdir -p $RPM_BUILD_ROOT/usr/src/kernels
    mv $RPM_BUILD_ROOT/lib/modules/$kernelver/build $RPM_BUILD_ROOT/$develdir
    ln -sf ../../..$develdir $RPM_BUILD_ROOT/lib/modules/$kernelver/build
# Create our initrd in the rpm build process
    cd %_builddir/%{name}-%{krelease}
    rm -rf initrd-$kernelver initrd_skeleton initrd_skeleton.gz
    mkdir initrd-$kernelver
    cp $RPM_SOURCE_DIR/initrd_skeleton ./  
    cd initrd-$kernelver
    mkdir bin lib
    initrd_bins="/sbin/insmod.static /sbin/nash"
    initrd_libs=$(
          for i in $initrd_bins ; do ldd "$i"; done \
          | sed -ne 's:\t\(.* => \)\?\(/.*\) (0x[0-9a-f]*):\2:p'
    )
    echo -n "$initrd_bins" | xargs -n 1 -d ' ' -I target cp target ./bin
    mv ./bin/insmod.static ./bin/insmod
    echo -n "$initrd_libs" | xargs -n 1 -I target cp target ./lib
    cp $RPM_SOURCE_DIR/init ./
    ln -s /sbin/nash bin/modprobe
# Copy needed modules to initrd
    kos=$(cat init | sed -n -e "s/^insmod \/lib\/\(.*.ko\)/\1/p")
    for ko in $kos ; do
        kof=`find $RPM_BUILD_ROOT/lib/modules/$kernelver -name "$ko" | tail -n 1`
        if [ -n "$kof" ] ; then 
          cp "$kof" ./lib
        fi
    done
    find . | cpio --quiet -c -oAF ../initrd_skeleton
    gzip ../initrd_skeleton
    %if "%{target}" == "redhat"
        cp ../initrd_skeleton.gz  $RPM_BUILD_ROOT/boot/initrd-$kernelver.img
    %else
        cp ../initrd_skeleton.gz $RPM_BUILD_ROOT/boot/initrd-$kernelver
    %endif
done

%clean
rm -rf $RPM_BUILD_ROOT 


