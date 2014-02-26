%define _topdir           /home/pivotal/code/dstools/cmake/deploy/gppkg/4.2
%define __os_install_post %{nil}
%define _rpmfilename      dstools-1.0-1.x86_64.rpm
%define _unpackaged_files_terminate_build 0
%define _dstools_version  1.0

BuildRoot:      /home/pivotal/code/dstools/cmake/_CPack_Packages/Linux/RPM/dstools-1.0-Linux
Summary:        DSTools for Greenplum Database
License:        New BSD License
Name:           dstools
Version:        1.0
Release:        1
Group:          Development/Libraries
Prefix:         /usr/local
AutoReq:        no
AutoProv:       no
BuildArch:      x86_64
Provides:       /bin/sh

%description
This is a library of toolkits to supplement the capabilities offered by
MADlib.


%prep
:

%install

%post
ln -nsf $RPM_INSTALL_PREFIX/dstools/Versions/%{_dstools_version} $RPM_INSTALL_PREFIX/dstools/Current
ln -nsf $RPM_INSTALL_PREFIX/dstools/Current/bin $RPM_INSTALL_PREFIX/dstools/bin
ln -nsf $RPM_INSTALL_PREFIX/dstools/Current/doc $RPM_INSTALL_PREFIX/dstools/doc
# creating symlink for madpack (does not work at present)
# find $RPM_INSTALL_PREFIX/bin/madpack -type f -exec mv {} $RPM_INSTALL_PREFIX/bin/old_madpack \; 2>/dev/null
# ln -nsf $RPM_INSTALL_PREFIX/dstools/Current/bin/madpack $RPM_INSTALL_PREFIX/bin/madpack

%files
%((cd "/home/pivotal/code/dstools/cmake/_CPack_Packages/Linux/RPM/dstools-1.0-Linux/usr/local/dstools/Versions/1.0" && find . \( -type f -or -type l \) | grep -E -v "^\./ports/.*" && find ./ports/greenplum \( -type f -or -type l \) | grep -E -v "^\./ports/greenplum/[[:digit:]]+\.[[:digit:]]+/.*" && find ./ports/greenplum/4.2 \( -type f -or -type l \)) | cut -c 2- | awk '{ print "\"/usr/local/dstools/Versions/1.0" $0 "\""}')
