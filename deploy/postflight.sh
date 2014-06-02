#!/bin/bash

# $0 - Script Path, $1 - Package Path, $2 - Target Location, and $3 - Target Volumn

DSTOOLS_VERSION=1.1

find /usr/local/dstools/bin -type d -exec cp -RPf {} /usr/local/dstools/old_bin \; 2>/dev/null
find /usr/local/dstools/bin -depth -type d -exec rm -r {} \; 2>/dev/null

find /usr/local/dstools/doc -type d -exec cp -RPf {} /usr/local/dstools/old_doc \; 2>/dev/null
find /usr/local/dstools/doc -depth -type d -exec rm -r {} \; 2>/dev/null

#ln -sf $2 /usr/local/dstools/Current
ln -nsf /usr/local/dstools/Versions/$DSTOOLS_VERSION /usr/local/dstools/Current
ln -nsf /usr/local/dstools/Current/bin /usr/local/dstools/bin
ln -nsf /usr/local/dstools/Current/doc /usr/local/dstools/doc

if [ -d "/usr/local/dstools/Versions.bak" ]
then
    mv -f /usr/local/dstools/Versions.bak/* /usr/local/dstools/Versions/
    rm -rf /usr/local/dstools/Versions.bak
fi
