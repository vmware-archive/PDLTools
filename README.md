DSTools
========

    DSTools is an a collection of functions to supplement the Data Science capabilities of MADlib.

Pre-requisites
===============

   The following are the pre-requisites to building the dstools package.

   1) The cmake compiler (version >= 2.8)
   2) Greenplum Database (GPDB 4.2 or higher)
   3) rpmbuild package if you want to create rpm packages of the installer

Building
=========

    To build outside the source tree, follow these steps:
       1) mkdir build
       2) cd build
       3) cmake ..
       4) make

Packaging
==========

    To create an rpm package which you can ship for installation into other machines, run the following (from the build directory):

    `make package`

    To create a gppkg installer, run the following (from the build directory):

    `make gppkg`

Installation
=============

    Installation is a two-step process. First, you will have to install DSTools on the target machine where GPDB is running.
    To do this, you will run the following:

        `gppkg -i <dstools-version.gppkg file>`

    This will place all the relevant binaries & SQL files at the appropriate location (usually `$GPHOME/dstools`).
    Next, you will have to install the SQL UDFs in the target database.

    To install dstools into a database of your choice, run the following (consider adding `dspack` in your PATH):
        `$GPHOME/dstools/bin/dspack install -s <schema name> -c <username>@<hostname>:<port>/<database name>`
    
    For example:
        `$GPHOME/dstools/bin/dspack install -s dstools -c gpadmin@mdw:5432/testdb`

