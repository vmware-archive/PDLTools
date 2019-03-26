PDL Tools
=========

    PDL Tools is a library of reusable tools used and developed by the Pivotal Data Science and Data Engineering teams.
    
[![Build Status](https://travis-ci.org/pivotalsoftware/PDLTools.svg?branch=master)](https://travis-ci.org/pivotalsoftware/PDLTools)

Usage docs
============

https://pivotalsoftware.github.io/PDLTools/

Binaries (Pivotal internal)
============================

[PDLTools binaries](https://drive.google.com/a/pivotal.io/folderview?id=0B43lMs8oQk7xcGJqdlN6SElWOTQ&usp=sharing)


Pre-requisites
===============

The following are the pre-requisites for building the pdltools package:

    1. The cmake compiler. (We recommend getting latest version (3.5) as older version don't seem to handle URL redirects, you can download the binary for Linux from here: https://cmake.org/files/v3.5/cmake-3.5.0-Linux-x86_64.tar.gz).
    2. g++, Flex (>= 2.5.33), Bison (>=2.4), Doxygen (1.8.7 recommended, needed only for generating docs), Latex (needed only for generating PDF docs). On CentOS this would be:

        sudo yum install gcc-c++
        sudo yum install flex
        sudo yum install bison 
        sudo yum install doxygen (we recommend version 1.8.7, follow instructions at https://www.stack.nl/~dimitri/doxygen/download.html to download and install the appropriate binaries ex: https://ftp.stack.nl/pub/users/dimitri/doxygen-1.8.7.linux.bin.tar.gz).
        sudo yum install texlive-latex

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

You can generate Doxygen docs for the project as follows:

    1. cd build
    2. cmake ..
    3. make
    4. make doc

This will create the user docs under $BUILD/doc/user/html. 
You can also generate a PDF of the user doc by running

    cd build/doc/user/latex && make pdf

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

    $GPHOME/pdltools/bin/pdlpack install [-s <schema name>] [-S <SUgAR schema name>] [-M <MADlib schema name>] -c <username>@<hostname>:<port>/<database name>

For example:

    $GPHOME/pdltools/bin/pdlpack install -s pdltools -c gpadmin@mdw:5432/testdb

The default schemas are `pdltools` for the main schema, `sugarlib` for SUgAR and `madlib` to search for MADlib objects.

Running Install Check Tests
=============================
    
Post installation, you can run the unit tests in PDL Tools with the install-check command like so:

    $GPHOME/pdltools/bin/pdlpack install-check -s pdltools -c gpadmin@mdw:5432/testdb

Parameters for `install-check` are the same as parameters for `install`.
If any of the tests fail, you will see an error message displayed on your console.

Contributing to PDLTools
========================

If you're interested in contributing to PDLTools, please refer to the instructions at [Guidelines for contributing to PDLTools](https://github.com/pivotalsoftware/PDLTools/blob/master/CONTRIBUTIONS.md)

Legal
======
Copyright (c) 2013-2016 Pivotal Software, Inc. All rights reserved.

Unauthorized use, copying or distribution of this source code via any
medium is strictly prohibited without the express written consent of
Pivotal Software, Inc.

THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND,
EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
