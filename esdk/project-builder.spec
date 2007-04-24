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

%description
Development Kit for creating Linux stacks for mobile or single purposed
devices.

%prep
%setup -q

%build
make

%install
make install

%clean
rm -rf %{buildroot}

%files
%defattr(-,root,root)
/usr/share/pdk/*

%changelog
* Sat Apr 21 2007 Rusty Lynch <rusty.lynch@intel.com>
- Initial package creation
