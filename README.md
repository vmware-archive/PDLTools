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
=========

To create an rpm package which you can ship for installation into other machines, run the following (from the build directory):

* make package

To create a gppkg installer, run the following (from the build directory):

* make gppkg

Installation (TBD)
===================

To install dstools into a database of your choice, run the following (assuming "dspack" is in your PATH):
dspack install -s <schema name> -c <username>@<hostname>:<port>/<database name>
For example:
dspack install -s dstools -c gpadmin@mdw:5432/vastandb

