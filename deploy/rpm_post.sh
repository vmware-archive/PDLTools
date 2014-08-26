find $RPM_INSTALL_PREFIX/pdltools/bin -type d -exec cp -RPf {} $RPM_INSTALL_PREFIX/pdltools/old_bin \; 2>/dev/null
find $RPM_INSTALL_PREFIX/pdltools/bin -depth -type d -exec rm -r {} \; 2>/dev/null

find $RPM_INSTALL_PREFIX/pdltools/doc -type d -exec cp -RPf {} $RPM_INSTALL_PREFIX/pdltools/old_doc \; 2>/dev/null
find $RPM_INSTALL_PREFIX/pdltools/doc -depth -type d -exec rm -r {} \; 2>/dev/null

ln -nsf $RPM_INSTALL_PREFIX/pdltools/Versions/%{_pdltools_version} $RPM_INSTALL_PREFIX/pdltools/Current
ln -nsf $RPM_INSTALL_PREFIX/pdltools/Current/bin $RPM_INSTALL_PREFIX/pdltools/bin
ln -nsf $RPM_INSTALL_PREFIX/pdltools/Current/doc $RPM_INSTALL_PREFIX/pdltools/doc
