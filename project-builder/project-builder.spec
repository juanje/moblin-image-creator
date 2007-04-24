Summary: Project Builder Mobile Linux Development Kit
Name: project-builder
Version: 0.1
Release: 0 
License: GPL
Group: Development
Source: %{name}-%{version}.tgz
Buildroot: %{_tmppath}/%{name}-root
BuildRequires: bash tcsh gzip
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

%clean
rm -rf %{buildroot}

%files
%defattr(-,root,root)
/usr/share/pdk/*
/etc/bash_completion.d/project-builder-completion.bash
/etc/security/console.apps/project-builder
/etc/pam.d/project-builder
/usr/bin/project-builder
/usr/sbin/project-builder

%changelog
* Sat Apr 21 2007 Rusty Lynch <rusty.lynch@intel.com>
- Initial package creation
