PDL Tools
=========

    PDL Tools is a library of reusable tools used and developed by the Pivotal Data Science and Data Engineering teams.
    
[![Build Status](https://travis-ci.org/pivotalsoftware/PDLTools.svg?branch=master)](https://travis-ci.org/pivotalsoftware/PDLTools)

Usage docs
============

http://pivotalsoftware.github.io/PDLTools/

Binaries (Pivotal internal)
============================

[PDLTools binaries](https://drive.google.com/a/pivotal.io/folderview?id=0B43lMs8oQk7xcGJqdlN6SElWOTQ&usp=sharing)


Pre-requisites
===============

The following are the pre-requisites for building PDLTools:

Required:
* Pivotal Greenplum or Apache HAWQ ([GPDB sandbox](https://network.pivotal.io/products/pivotal-gpdb), [HAWQ sandbox](https://network.pivotal.io/products/pivotal-hdb))
* Apache MADlib ([Download](http://madlib.incubator.apache.org/download.html))
* cmake (3.5 recommended)
* GNU C and C++ compilers (gcc, g++)
* Flex (>= 2.5.33)
* Bison (>= 2.4)
* rpmbuild

Optional:
* Doxygen (1.8.7 recommended, if generating HTML docs), 
* LaTeX (if generating PDF docs)


Building
=========

For CentOS or Red Hat Enterprise Linux, install the pre-requisite tools:

     sudo yum install cmake gcc gcc-c++ flex bison rpm-build

From either the Greenplum or HAWQ master node, follow these steps as the `gpadmin` user:

```bash
     curl -L -o pdltools-1.7.zip https://github.com/pivotalsoftware/PDLTools/archive/v1.7.zip
 
     unzip  pdltools-1.7.zip ; cd PDLTools-1.7
 
     source /usr/local/hawq/greenplum_path.sh
 
     mkdir build ; cd build ; cmake .. -DRPM_INSTALL_PREFIX=$GPHOME
 
     curl -L -o third_party/downloads/uriparser-0.7.9.tar.bz2 https://sourceforge.net/projects/uriparser/files/uriparser-0.7.9.tar.bz2
 
     curl -L -o third_party/downloads/cpptest-1.1.2.tar.gz https://sourceforge.net/projects/cpptest/files/cpptest-1.1.2.tar.gz
 
     make -j5 package 2> /dev/null
```

Generating Doxygen User Docs
=============================

You can generate Doxygen docs for the project as follows:

     make doc

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

Installation is a two-step process. First, you will have to install MADlib _and_ PDL Tools on either the Greenplum or HAWQ master node.
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
