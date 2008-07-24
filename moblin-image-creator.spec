Summary: Mobline Image Creator -- Mobile & Internet Linux Development Kit
Name: moblin-image-creator
Version: 0.45
Release: 1
License: GPL
Group: Development
Source: %{name}-%{version}.tar.gz
Buildroot: %{_tmppath}/%{name}-root
Requires: python >= 2.4
Requires: pam
Requires: usermode
Requires: bash-completion
BuildRequires: make, automake, autoconf, intltool, gettext-devel

%description
Development Kit for creating Linux stacks for mobile or single purposed
devices.

%prep
%setup -q

%build
./autogen.sh

%install
make DESTDIR=$RPM_BUILD_ROOT install
cp %_builddir/%{name}-%{version}/suse/image-creator* $RPM_BUILD_ROOT/usr/sbin/

%clean
rm -rf %{buildroot}

%files
%defattr(-,root,root)
/usr/share/pdk/*
/usr/share/applications/image-creator.desktop
/etc/bash_completion.d/image-creator-completion.bash
/etc/security/console.apps/image-creator
/etc/pam.d/image-creator
/usr/bin/image-creator
/usr/sbin/image-creator
/usr/sbin/image-creator-suse-mount
/usr/sbin/image-creator-suse-umount
/usr/sbin/image-creator-suse-start
/usr/sbin/image-creator-suse-install

%changelog
* Wed Jun 06 2007 Rusty Lynch <rusty.lynch@intel.com>
- Adding a workaround for a bug on SELinux enable systems

* Fri Jun 01 2007 Rusty Lynch <rusty.lynch@intel.com>
- Updating spec for building in a debian environment

* Sat Apr 21 2007 Rusty Lynch <rusty.lynch@intel.com>
- Initial package creation
