#!/bin/bash

# $0 - Script Path, $1 - Package Path, $2 - Target Location, and $3 - Target Volumn

if [ -d "/usr/local/pdltools/Versions" ]
then
    mv /usr/local/pdltools/Versions /usr/local/pdltools/Versions.bak
fi
