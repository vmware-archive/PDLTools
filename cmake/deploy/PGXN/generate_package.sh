#!/bin/sh

TEMPDIR=`mktemp -d -t dstools`
"/usr/bin/cmake28" -E create_symlink \
    "/home/pivotal/code/dstools" \
    "${TEMPDIR}/dstools-pgxn-1.0.0release1"
"/usr/bin/cmake28" -E create_symlink \
    "/home/pivotal/code/dstools/cmake/deploy/PGXN/zipignore" \
    "${TEMPDIR}/zipignore"
cd "${TEMPDIR}"
zip --exclude @zipignore \
    -r "/home/pivotal/code/dstools/cmake/deploy/PGXN/dstools-pgxn-1.0.0release1.zip" \
    "dstools-pgxn-1.0.0release1"
