find $RPM_INSTALL_PREFIX/dstools/bin -type d -exec cp -RPf {} $RPM_INSTALL_PREFIX/dstools/old_bin \; 2>/dev/null
find $RPM_INSTALL_PREFIX/dstools/bin -depth -type d -exec rm -r {} \; 2>/dev/null

find $RPM_INSTALL_PREFIX/dstools/doc -type d -exec cp -RPf {} $RPM_INSTALL_PREFIX/dstools/old_doc \; 2>/dev/null
find $RPM_INSTALL_PREFIX/dstools/doc -depth -type d -exec rm -r {} \; 2>/dev/null

ln -nsf $RPM_INSTALL_PREFIX/dstools/Versions/%{_dstools_version} $RPM_INSTALL_PREFIX/dstools/Current
ln -nsf $RPM_INSTALL_PREFIX/dstools/Current/bin $RPM_INSTALL_PREFIX/dstools/bin
ln -nsf $RPM_INSTALL_PREFIX/dstools/Current/doc $RPM_INSTALL_PREFIX/dstools/doc
