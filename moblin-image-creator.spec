Summary: Mobline Image Creator -- Mobile & Internet Linux Development Kit
Name: moblin-image-creator
Version: 0.48
Release: 1%{?dist}
License: GPL
Group: Development
Packager: Mitsutaka Amano <mamano@miraclelinux.com>
Vendor: moblin.org
URL: http://moblin.org
Source: %{name}-%{version}.tgz
Buildroot: %{_tmppath}/%{name}-root
BuildArch: noarch
Requires: python >= 2.4, pam, usermode, bash-completion, qemu-img, kvm
BuildRequires: make, automake, autoconf, intltool, gettext-devel

%description
The moblin-image-creator utility enables developers to build full mobile
or single purposed Linux stacks using a mainstream distribution.

%prep
rm -rf $RPM_BUILD_ROOT
%setup -q

%build
./autogen.sh
%configure

%install
make DESTDIR=$RPM_BUILD_ROOT install
%{find_lang} %{name}
mkdir -p $RPM_BUILD_ROOT/etc/pam.d
mkdir -p $RPM_BUILD_ROOT/etc/security/console.apps
mkdir -p $RPM_BUILD_ROOT/usr/sbin
mkdir -p $RPM_BUILD_ROOT/usr/bin
cp %_builddir/%{name}-%{version}/image-creator.helperconsole \
    $RPM_BUILD_ROOT/etc/security/console.apps/image-creator
cp %_builddir/%{name}-%{version}/image-creator.pam.d \
    $RPM_BUILD_ROOT/etc/pam.d/image-creator
cp %_builddir/%{name}-%{version}/suse/image-creator* \
    $RPM_BUILD_ROOT/usr/sbin
ln -f -s /usr/bin/consolehelper $RPM_BUILD_ROOT/usr/bin/image-creator
sed -i "s|Exec=.*|Exec=/usr/bin/image-creator|" $RPM_BUILD_ROOT/usr/share/applications/image-creator.desktop

%clean
rm -rf %{buildroot}

%files
%defattr(-,root,root)
/etc/bash_completion.d/image-creator-completion.bash
/etc/pam.d/image-creator
/etc/security/console.apps/image-creator
/usr/bin/image-creator
/usr/sbin/image-creator
/usr/sbin/image-creator-suse-install
/usr/sbin/image-creator-suse-mount
/usr/sbin/image-creator-suse-start
/usr/sbin/image-creator-suse-umount
/usr/share/applications/image-creator.desktop
/usr/share/locale/*/LC_MESSAGES/moblin-image-creator.mo
/usr/share/pdk/*
/var/lib/moblin-image-creator/projects

%changelog
* Mon Nov 27 2008 Mitsutaka Amano <mamano@miraclelinux.com>
- Fixing a bug about http://bugzilla.moblin.org/show_bug.cgi?id=130

* Thu Nov 19 2008 Prajwal Mohan <prajwal@linux.intel.com>
- Adding mount in install script

* Thu Nov 13 2008 Prajwal Mohan <prajwal@linux.intel.com>
- Adding update column for target view

* Mon Nov 10 2008 Mitsutaka Amano <mamano@miraclelinux.com>
- Updated ja.po.

* Sun Nov 09 2008 Mitsutaka Amano <mamano@miraclelinux.com>
- Hiding PERL_BADLANG persistent messages when package installation.

* Thu Nov 06 2008 Prajwal Mohan <prajwal@linux.intel.com>
- Fixing usb script

* Wed Nov 05 2008 Mitsutaka Amano <mamano@miraclelinux.com>
- Fixed moblin 1.0 apt repository URL.
- Starting new version.

* Thu Oct 30 2008 Mitsutaka Amano <mamano@miraclelinux.com>
- Rebase with nfsboot function. Fixed some comments and install_kernels() arguments.
- Deleted necessary function in NFSLiveIsoImage. Adjusted NFSLiveUsbImage size.

* Wed Oct 22 2008 Mitsutaka Amano <mamano@miraclelinux.com>
- Added NFS Live CD Image function.

* Tue Oct 14 2008 Mitsutaka Amano <mamano@miraclelinux.com>
- Added NFS Live USB Image function.
- Added error handling and modified destination of isolinux.bin LiveIsoImage.

* Fri Oct 10 2008 Mitsutaka Amano <mamano@miraclelinux.com>
- Added the Create Install CD.

* Wed Oct 08 2008 Mitsutaka Amano <mamano@miraclelinux.com>
- Starting new version.

* Tue Oct 07 2008 Prajwal Mohan <prajwal@linux.intel.com>
- Setting defaults for moblin2 platforms
- Changing defaults for menlow-lpia-moblin2
- Adding moblin-installer to core fset of moblin2 platforms
- Setting root=/dev/sda2 in grub.conf for jax10

* Fri Oct 03 2008 Mitsutaka Amano <mamano@miraclelinux.com>
- Fixed newProject dialog stretch bug.

* Thu Oct 02 2008 Prajwal Mohan <prajwal@linux.intel.com>
- Changing progress bar label

* Thu Oct 02 2008 Mitsutaka Amano <mamano@miraclelinux.com>
- Added the Target config function.
- Updated debian/changelog and rpm spec file.
- Updated ja.po.
- Added welcome_message in the Target config.
- Updated ja.po.
- Fixed typo and resolved https://bugs.launchpad.net/moblin-image-creator/+bug/199180

* Wed Oct 01 2008 Prajwal Mohan <prajwal@linux.intel.com>
- Adding feature to install package groups

* Wed Oct 01 2008 Mitsutaka Amano <mamano@miraclelinux.com>
- Fixed rpm spec file for initial installation.

* Tue Sep 30 2008 Prajwal Mohan <prajwal@linux.intel.com>
- Adding tmpfs to fstab
- Changing repo url

* Mon Sep 29 2008 Prajwal Mohan <prajwal@linux.intel.com>
- Adding hal to communications fset
- setting root=/dev/sda2 in grub.conf
- Creating rootfs before bootfs

* Thu Sep 25 2008 Prajwal Mohan <prajwal@linux.intel.com>
- Fixing path for Nand image initrd

* Wed Sep 24 2008 Prajwal Mohan <prajwal@linux.intel.com>
- Added xfce4-session package to fset
- Continue with project creation if rootstrap creation fails

* Tue Sep 23 2008 Prajwal Mohan <prajwal@linux.intel.com>
- Changing init.1 script to accept init kernel param
- Adding communication fset to netbook and menlow platforms
- Adding post install scripts to menlow-lpia-moblin2
- Adding bluez packages to fset

* Fri Sep 19 2008 Mitsutaka Amano <mamano@miraclelinux.com>
- Added short of changelog(for Prajwal and Bob).

* Thu Sep 18 2008 Prajwal Mohan <prajwal@linux.intel.com>
- Changing run level

* Thu Sep 18 2008 Bob Spencer <bob.spencer@intel.com>
- Merge branch 'master' of ssh://bspencer@moblin.org/home/repos/tools/moblin-i
- A stand-alone python executable script that writes an image to a USB drive.
- Intended to be used with a QuickStart "Test Drive Moblin" online guide.

* Wed Sep 17 2008 Mitsutaka Amano <mamano@miraclelinux.com> [0.46]
- Starting new version. 

* Wed Sep 17 2008 Mitsutaka Amano <mamano@miraclelinux.com> [0.45]
- Starting new version
- https://bugs.launchpad.net/moblin-image-creator/+bug/203561
- Set a bigger bs paramter to dd command to speed up writing image
- Added libosso-dev to the developer tools fset
- Removing desktop-file-utils from Ubuntu-Mobile fset of all platforms
- Fixing image-creator path for image-creator.desktop in Makefile
- Adding cmd line option to display version
- Removing -v for version
- adding cancel button to progress dialog - not sensitive
- Adding packages to Asian-Fonts on gutsy. Chaning fset name to Asian-i18n-support
- Modifying Asian-i18n-support fset
- Removing libgl1-mesa-dri from Gnome-Mobile fset of menlow-lpia
- Adding ttf-kochi-gothic and ttf-kochi-mincho to asian-fonts fset
- Using list instead of set to list all fsets. https://bugs.launchpad.net/moblin-image-creator/+bug/211359
- Adding cancel option to add project
- Adding help - command line options
- Adding cmd line option to create live iso image
- Adding more help documentation
- bug fix for https://bugs.launchpad.net/moblin-image-creator/+bug/188158
- Adding a dialog before terminating MIC
- If project creating is cancelled during creation of rootstrap, it fails.  Fixing it
- usb mount script fails if another removable drive is found before USB flash drive. Fixing it.
- Added an error dialog if unknown projects/platforms are found
- Fixing bug in Fset info dialog
- Adding progress bar to term dialog
- Removing telepathy-core and telepathy-mission-control from mccaslin hardy ppa platforms
- Adding gnome-system-tools to ubuntu-mobile fset*-hardy-ppa and *-hardy-ppa-snapshot platforms
- Removing telepathy-core and telepathy-mission-control from menlow hardy ppa platforms
- Adding command line options to show packages for a given fset
- Adding command line options to show sources files
- Make file creates projects dir in /usr/share/pdk. Moving it to /var/lib/moblin-image-creator
- Supported autotools for preparing the internationalization.
- Supported the internationalization.
- Global name '_' is not defined in image-creator. Fixing it.
- Fixed permission of image-creator.
- Updated README to modified installation process.
- Fixed typo in README.
- Supported the internationalization on project_assistant.py.
- Added Japanese localization(ja.po).
- Removed local language some message that can't be printed multi-byte character.
- Renamed desktop file to image-creator.desktop.in from image-creator.desktop.
- Supported the internationalization on image-creator.desktop.in
- Checking in bug fix for 230331
- Checking in bug fix for 227013. /boot will be mounted rw on boot with disk initramfs script
- Releasing 0.45 version
- Starting new version
- Adding Nand kernel cmd line
- Adding KVM and NAND buttons to GUI
- Making changes to Yum package manager
- Adding functions to get/set NAND kernel cmd line
- Adding yum specific package handling
- Updated rpm spec file for 0.45.
- Added dist parametor on rpm spec file.
- Making changes to Install Image to handle yum based platforms
- Making changes to Makefile
- Adding creating grub menu
- Fixing problems with creating images for yum platforms on apt host
- kvm has different binaries on yum and apt platforms
- Added package reaquire.
- Fixing bug in applying hd_kernel_cmd_line
- Fixing update-grub path
- Checking in scripts for initrd
- Added entry Makefile.am on mccaslin-lpia-fedora.
- Added entry busybox in defaults.cfg.
- Cleaned to dirty codes.
- Added some localization and cleaned to dirty codes.
- Added some localization.
- Adding nand to command line
- Adding repo editor and changes to gui
- Adding conflicts to fsets
- Minor changes to pdk_utils and mic_cfg
- Bug fixes in InstallImage.py
- Adding nand scripts to common-apt
- Adding repo_editor.py to makefile
- Fixed bug about can't create /var/lib/moblin-image-creator/kvm.
- Adding ubuntu jax10 platform
- Adding platform definition for netbook-lpia-moblin and menlow-lpia-moblin
- Adjusting kvm parameters
- Deleted unnecessary temporary Makefile.
- Adding ability to execute post install scripts
- Fixing Jax10 platform
- Using squashfs for Jax10 platform
- Reducing boot partition size for netbook
- Merged from UME patches. Based patch file is moblin-image-creator-0.44+repack/debian/patches/40_fsets.patch. Thanks to Loic Minier <lool@dooz.org>.
- Merged from UME patches. Based patch file is moblin-image-creator-0.44+repack/debian/patches/60_var-lib-projects.patch. Thanks to Loic Minier <lool@dooz.org>.
- Merged from UME patches. Based patch file is moblin-image-creator-0.44+repack/debian/patches/61_skip-usr-share-projects.patch. Thanks to Loic Minier <lool@dooz.org>.
- Merged from UME patches. Based patch file is moblin-image-creator-0.44+repack/debian/patches/66_mount-boot.patch. Thanks to Loic Minier <lool@dooz.org>.
- Merged from UME patches. Based patch file is moblin-image-creator-0.44+repack/debian/patches/68_clean-default-kopts.patch. Thanks to Loic Minier <lool@dooz.org>.
- Merged from UME patches. Based patch file is moblin-image-creator-0.44+repack/debian/patches/69_run-update-grub.patch. Thanks to Loic Minier <lool@dooz.org>.
- Merged from UME patches. Based patch file is moblin-image-creator-0.44+repack/debian/patches/70_menu-lst-default.patch. Thanks to Loic Minier <lool@dooz.org>.
- Merged from UME patches. Based patch file is moblin-image-creator-0.44+repack/debian/patches/71_install_locale.patch. Thanks to Loic Minier <lool@dooz.org>.
- Merged from UME patches. Based patch file is moblin-image-creator-0.44+repack/debian/patches/72_ume-platforms.patch. Thanks to Loic Minier <lool@dooz.org>.
- Fixed some Makefile.am to entried .empty file. It can correspond only Makefile.am. so Removed a .empty file.
- Merged from UME patches. Based patch file is moblin-image-creator-0.44+repack/debian/patches/73_create-kernel-img-conf.patch. Thanks to Loic Minier <lool@dooz.org>.
- Merged from UME patches. Based patch file is moblin-image-creator-0.44+repack/debian/patches/74_boot-is-really-boot.patch. Thanks to Loic Minier <lool@dooz.org>.
- Droped backwords compatibility codes.
- Passing callback to pdk_utils.copy causing problems in FC9
- Droped unnecessary codes. Added a Japanese localization.
- Droped unnecessary %files entry in spec file. Cleaned dirty codes.
- Added Japaense localization in gui/repo_editor.py and more.
- Fixing bug in saving repo file
- Updated Japanese localization.
- Adding option to set install prefix, sysconfdir, localdatadir etc
- Fixed installation path of deb and rpm. When manual install process, MIC install in /usr/local.
- I forgot add chagnelog in spec file.
- Fixed image-creator installation in deb and rpm.
- Adding gtk2-devel to the netbook's 'X-Dev' fset
- Improved layout and stretchability of the add project dialog
- Made platform description uneditable. Removed reference to EeeeeeePC
- Follow someone changelog. Updated the README.
- Fixed image-creator help output.  One mispelling and a little confusion on usb-image options listed
- Changing fset X for netbook. Using xorg-x11-drv-intel instead of xorg-x11-drv-i810
- Adding post install scripts to netbook platform

* Mon Sep 04 2008 Mitsutaka Amano <mamano@miraclelinux.com>
- Fixed image-creator installation in deb and rpm.

* Mon Aug 27 2008 Mitsutaka Amano <mamano@miraclelinux.com>
- Added configure process on %build section.

* Mon Aug 25 2008 Mitsutaka Amano <mamano@miraclelinux.com>
- Droped unnecessary %files entry.

* Thu Jul 31 2008 Mitsutaka Amano <mamano@miraclelinux.com>
- Added Requires:.

* Thu Jul 29 2008 Mitsutaka Amano <mamano@miraclelinux.com>
- Added dist parametor on rpm spec file.

* Thu Jul 24 2008 Mitsutaka Amano <mamano@miraclelinux.com>
- Rebuild for 0.45

* Wed Jun 06 2007 Rusty Lynch <rusty.lynch@intel.com>
- Adding a workaround for a bug on SELinux enable systems

* Fri Jun 01 2007 Rusty Lynch <rusty.lynch@intel.com>
- Updating spec for building in a debian environment

* Sat Apr 21 2007 Rusty Lynch <rusty.lynch@intel.com>
- Initial package creation
