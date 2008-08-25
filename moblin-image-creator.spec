Summary: Mobline Image Creator -- Mobile & Internet Linux Development Kit
Name: moblin-image-creator
Version: 0.45
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
%setup -q

%build
./autogen.sh

%install
make DESTDIR=$RPM_BUILD_ROOT install
mkdir -p $RPM_BUILD_ROOT/etc/pam.d
mkdir -p $RPM_BUILD_ROOT/etc/security/console.apps
mkdir -p $RPM_BUILD_ROOT/usr/sbin
cp %_builddir/%{name}-%{version}/image-creator.helperconsole \
    $RPM_BUILD_ROOT/etc/security/console.apps/image-creator
cp %_builddir/%{name}-%{version}/image-creator.pam.d \
    $RPM_BUILD_ROOT/etc/pam.d/image-creator
cp %_builddir/%{name}-%{version}/suse/image-creator* \
    $RPM_BUILD_ROOT/usr/sbin
ln -f -s /usr/bin/consolehelper $RPM_BUILD_ROOT/usr/bin/image-creator

%clean
rm -rf %{buildroot}

%files
%defattr(-,root,root)
/etc/bash_completion.d/image-creator-completion.bash
/etc/pam.d/image-creator
/etc/security/console.apps/image-creator
/usr/bin/image-creator
/usr/sbin/image-creator-suse-install
/usr/sbin/image-creator-suse-mount
/usr/sbin/image-creator-suse-start
/usr/sbin/image-creator-suse-umount
/usr/share/applications/image-creator.desktop
/usr/share/locale/*/LC_MESSAGES/moblin-image-creator.mo
/usr/share/pdk/*

%changelog
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
