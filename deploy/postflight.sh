#!/bin/bash

# $0 - Script Path, $1 - Package Path, $2 - Target Location, and $3 - Target Volumn

PDLTOOLS_VERSION=1.7

find /usr/local/pdltools/bin -type d -exec cp -RPf {} /usr/local/pdltools/old_bin \; 2>/dev/null
find /usr/local/pdltools/bin -depth -type d -exec rm -r {} \; 2>/dev/null

find /usr/local/pdltools/doc -type d -exec cp -RPf {} /usr/local/pdltools/old_doc \; 2>/dev/null
find /usr/local/pdltools/doc -depth -type d -exec rm -r {} \; 2>/dev/null

#ln -sf $2 /usr/local/pdltools/Current
if [ -d "/usr/local/pdltools" ]
then
    ln -nsf /usr/local/pdltools/Versions/$PDLTOOLS_VERSION /usr/local/pdltools/Current
    ln -nsf /usr/local/pdltools/Current/bin /usr/local/pdltools/bin
    ln -nsf /usr/local/pdltools/Current/doc /usr/local/pdltools/doc
fi

if [ -d "/usr/local/pdltools/Versions.bak" ]
then
    mv -f /usr/local/pdltools/Versions.bak/* /usr/local/pdltools/Versions/
    rm -rf /usr/local/pdltools/Versions.bak
fi
