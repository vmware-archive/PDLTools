#!/bin/bash

# $0 - Script Path, $1 - Package Path, $2 - Target Location, and $3 - Target Volumn

if [ -d "/usr/local/dstools/Versions" ]
then
    mv /usr/local/dstools/Versions /usr/local/dstools/Versions.bak
fi
