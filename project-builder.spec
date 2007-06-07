Summary: Project Builder Mobile Linux Development Kit
Name: project-builder
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
make DESTDIR=$RPM_BUILD_ROOT basicinstall
sed '{s/%%EXEC_CMD%%/\/usr\/bin\/project-builder/}' project-builder.desktop.template > $RPM_BUILD_ROOT/usr/share/applications/project-builder.desktop
mkdir -p $RPM_BUILD_ROOT/usr/bin
ln -f -s /usr/bin/consolehelper $RPM_BUILD_ROOT/usr/bin/project-builder
mkdir -p $RPM_BUILD_ROOT/etc/pam.d
mkdir -p $RPM_BUILD_ROOT/etc/security/console.apps
cp project-builder.pam.d $RPM_BUILD_ROOT/etc/pam.d/project-builder
cp project-builder.helperconsole $RPM_BUILD_ROOT/etc/security/console.apps/project-builder

%clean
rm -rf %{buildroot}

%files
%defattr(-,root,root)
/usr/share/pdk/*
/usr/share/applications/project-builder.desktop
/etc/bash_completion.d/project-builder-completion.bash
/etc/security/console.apps/project-builder
/etc/pam.d/project-builder
/usr/bin/project-builder
/usr/sbin/project-builder

%changelog
* Wed Jun 06 2007 Rusty Lynch <rusty.lynch@intel.com>
- Adding a workaround for a bug on SELinux enable systems

* Fri Jun 01 2007 Rusty Lynch <rusty.lynch@intel.com>
- Updating spec for building in a debian environment

* Sat Apr 21 2007 Rusty Lynch <rusty.lynch@intel.com>
- Initial package creation
