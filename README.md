PDL Tools
=========

    PDL Tools is a library of reusable tools used and developed by Pivotal
Data Labs.

Pre-requisites
===============

   The following are the pre-requisites for building the pdltools package:
        1. The cmake compiler (version >= 2.8)
        2. g++, Flex, Bison, Doxygen ( `sudo yum install gcc-c++`, `sudo yum install flex`, `sudo yum install bison`, `sudo yum install doxygen`)
        3. Greenplum Database (GPDB 4.2 or higher) and/or HAWQ (1.2.x and higher)
        4. rpmbuild package if you want to create rpm packages of the installer (`sudo yum install rpm-build`)

Building
=========

    To build outside the source tree, follow these steps:
        1. mkdir build
        2. cd build
        3. cmake ..
        4. make

Generating Doxygen User Docs
=============================

    You can generated Doxygen docs for the project as follows:
        1. cd build
        2. cmake ..
        3. make
        4. make doc
    This will create the user docs under $BUILD/doc/user/html. You can then rsync this folder to our internal Linux box which automatically serves the documentation
    at [pdl-tools-userdocs](http://pdl-tools.pa.pivotal.io/)
 
    For example:
        rsync $PDLTOOLS/build/doc/user/html/* pdltools@pdl-tools.pa.pivotal.io:/home/dstools/hosting/dstools/doc/user/html/

    You can also generate a PDF of the user doc by running
         * cd build/doc/user/latex && make pdf
    This will generate a PDF titled `refman.pdf` in $PDLTOOLS/build/doc/user/latex


Packaging
==========

    To create an rpm package which you can ship for installation into other machines, run the following (from the build directory):
        make package

    To create a gppkg installer, run the following (from the build directory):
        make gppkg

Installation
=============

    Installation is a two-step process. First, you will have to install PDL Tools on the target machine where GPDB is running.
    To do this, you will run the following:
        
         gppkg -i <pdltools gppkg file>
    This will place all the relevant binaries & SQL files at the appropriate location (usually `$GPHOME/pdltools`).
    Next, you will have to install the SQL UDFs in the target database.

    To install pdltools into a database of your choice, run the following (consider adding `pdlpack` in your PATH):
        `$GPHOME/pdltools/bin/pdlpack install [-s <schema name>] [-S <SUgAR schema name>] [-M <MADlib schema name>] -c <username>@<hostname>:<port>/<database name>`
    
    For example:
        `$GPHOME/pdltools/bin/pdlpack install -s pdltools -c gpadmin@mdw:5432/testdb`

    The default schemas are `pdltools` for the main schema, `sugarlib` for SUgAR and `madlib` to search for MADlib objects.

Running Install Check Tests
=============================
    
    Post installation, you can run the unit tests in PDL Tools with the install-check command like so:
        `$GPHOME/pdltools/bin/pdlpack install-check -s pdltools -c gpadmin@mdw:5432/testdb`

    Parameters for `install-check` are the same as parameters for `install`.

    If any of the tests fail, you will see an error message displayed on your console.
