Summary: Mobline Image Creator -- Mobile & Internet Linux Development Kit
Name: moblin-image-creator
Version: 0.1
Release: 1 
License: GPL
Group: Development
Source: %{name}-%{version}.tgz
Buildroot: %{_tmppath}/%{name}-root
Requires: python >= 2.4
Requires: pam
Requires: usermode
Requires: bash-completion

%description
Development Kit for creating Linux stacks for mobile or single purposed
devices.

%prep
%setup -q

%build
make

%install
rm -rf $RPM_BUILD_ROOT/*
make DESTDIR=$RPM_BUILD_ROOT basicinstall
sed '{s/%%EXEC_CMD%%/\/usr\/bin\/image-creator/}' image-creator.desktop.template > $RPM_BUILD_ROOT/usr/share/applications/image-creator.desktop
mkdir -p $RPM_BUILD_ROOT/usr/bin
ln -f -s /usr/bin/consolehelper $RPM_BUILD_ROOT/usr/bin/image-creator
mkdir -p $RPM_BUILD_ROOT/etc/pam.d
mkdir -p $RPM_BUILD_ROOT/etc/security/console.apps
cp image-creator.pam.d $RPM_BUILD_ROOT/etc/pam.d/image-creator
cp image-creator.helperconsole $RPM_BUILD_ROOT/etc/security/console.apps/image-creator
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
