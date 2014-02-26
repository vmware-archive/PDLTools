# This file will be configured to contain variables for CPack. These variables
# should be set in the CMake list file of the project before CPack module is
# included. The list of available CPACK_xxx variables and their associated
# documentation may be obtained using
#  cpack --help-variable-list
#
# Some variables are common to all generators (e.g. CPACK_PACKAGE_NAME)
# and some are specific to a generator
# (e.g. CPACK_NSIS_EXTRA_INSTALL_COMMANDS). The generator specific variables
# usually begin with CPACK_<GENNAME>_xxxx.


SET(CPACK_BINARY_BUNDLE "")
SET(CPACK_BINARY_CYGWIN "")
SET(CPACK_BINARY_DEB "")
SET(CPACK_BINARY_DRAGNDROP "")
SET(CPACK_BINARY_NSIS "")
SET(CPACK_BINARY_OSXX11 "")
SET(CPACK_BINARY_PACKAGEMAKER "")
SET(CPACK_BINARY_RPM "")
SET(CPACK_BINARY_STGZ "")
SET(CPACK_BINARY_TBZ2 "")
SET(CPACK_BINARY_TGZ "")
SET(CPACK_BINARY_TZ "")
SET(CPACK_BINARY_WIX "")
SET(CPACK_BINARY_ZIP "")
SET(CPACK_CMAKE_GENERATOR "Unix Makefiles")
SET(CPACK_COMPONENT_UNSPECIFIED_HIDDEN "TRUE")
SET(CPACK_COMPONENT_UNSPECIFIED_REQUIRED "TRUE")
SET(CPACK_GENERATOR "RPM")
SET(CPACK_INSTALL_CMAKE_PROJECTS "/home/pivotal/code/dstools/cmake;DSTools;ALL;/")
SET(CPACK_INSTALL_PREFIX "/usr/local/dstools")
SET(CPACK_MODULE_PATH "/home/pivotal/code/dstools/cmake")
SET(CPACK_MONOLITHIC_INSTALL "1")
SET(CPACK_NSIS_DISPLAY_NAME "dstools")
SET(CPACK_NSIS_INSTALLER_ICON_CODE "")
SET(CPACK_NSIS_INSTALLER_MUI_ICON_CODE "")
SET(CPACK_NSIS_INSTALL_ROOT "$PROGRAMFILES")
SET(CPACK_NSIS_PACKAGE_NAME "dstools")
SET(CPACK_OSX_PACKAGE_VERSION "10.5")
SET(CPACK_OUTPUT_CONFIG_FILE "/home/pivotal/code/dstools/cmake/CPackConfig.cmake")
SET(CPACK_PACKAGE_DEFAULT_LOCATION "/")
SET(CPACK_PACKAGE_DESCRIPTION_FILE "/home/pivotal/code/dstools/deploy/description.txt")
SET(CPACK_PACKAGE_DESCRIPTION_SUMMARY "DS Tools Library.")
SET(CPACK_PACKAGE_FILE_NAME "dstools-1.0-Linux")
SET(CPACK_PACKAGE_INSTALL_DIRECTORY "dstools")
SET(CPACK_PACKAGE_INSTALL_REGISTRY_KEY "dstools")
SET(CPACK_PACKAGE_NAME "DSTools")
SET(CPACK_PACKAGE_RELOCATABLE "true")
SET(CPACK_PACKAGE_VENDOR "DSTools")
SET(CPACK_PACKAGE_VERSION "1.0")
SET(CPACK_PACKAGE_VERSION_MAJOR "1")
SET(CPACK_PACKAGE_VERSION_MINOR "0")
SET(CPACK_PACKAGE_VERSION_PATCH "0")
SET(CPACK_PACKAGING_INSTALL_PREFIX "/usr/local/dstools/Versions/1.0")
SET(CPACK_POSTFLIGHT_SCRIPT "/home/pivotal/code/dstools/deploy/postflight.sh")
SET(CPACK_PREFLIGHT_SCRIPT "/home/pivotal/code/dstools/deploy/preflight.sh")
SET(CPACK_RESOURCE_FILE_LICENSE "/home/pivotal/code/dstools/license/DSTools.txt")
SET(CPACK_RESOURCE_FILE_README "/home/pivotal/code/dstools/deploy/description.txt")
SET(CPACK_RESOURCE_FILE_WELCOME "/home/pivotal/code/dstools/deploy/PackageMaker/Welcome.html")
SET(CPACK_RPM_PACKAGE_ARCHITECTURE "x86_64")
SET(CPACK_RPM_PACKAGE_GROUP "Development/Libraries")
SET(CPACK_RPM_PACKAGE_LICENSE "New BSD License")
SET(CPACK_RPM_PACKAGE_REQUIRES "python >= 2.6, m4 >= 1.4")
SET(CPACK_RPM_POST_INSTALL_SCRIPT_FILE "/home/pivotal/code/dstools/deploy/rpm_post.sh")
SET(CPACK_RPM_SPEC_MORE_DEFINE "%undefine __os_install_post")
SET(CPACK_RPM_USER_BINARY_SPECFILE "/home/pivotal/code/dstools/deploy/dstools.spec.in")
SET(CPACK_SET_DESTDIR "OFF")
SET(CPACK_SOURCE_CYGWIN "")
SET(CPACK_SOURCE_GENERATOR "TGZ;TBZ2;TZ")
SET(CPACK_SOURCE_OUTPUT_CONFIG_FILE "/home/pivotal/code/dstools/cmake/CPackSourceConfig.cmake")
SET(CPACK_SOURCE_TBZ2 "ON")
SET(CPACK_SOURCE_TGZ "ON")
SET(CPACK_SOURCE_TZ "ON")
SET(CPACK_SOURCE_ZIP "OFF")
SET(CPACK_SYSTEM_NAME "Linux")
SET(CPACK_TOPLEVEL_TAG "Linux")
SET(CPACK_WIX_SIZEOF_VOID_P "8")

# Configuration for component "doc"
set(CPACK_COMPONENT_DOC_DISPLAY_NAME "Documentation")
set(CPACK_COMPONENT_DOC_DESCRIPTION "API reference and documentation (generated with Doxygen).")

# Configuration for component "core"
set(CPACK_COMPONENT_CORE_DISPLAY_NAME "DSTools Core")
set(CPACK_COMPONENT_CORE_DESCRIPTION "DBMS-independent files installed with every DSTools installation.")
set(CPACK_COMPONENT_CORE_REQUIRED TRUE)

# Configuration for component group "ports"
set(CPACK_COMPONENT_GROUP_PORTS_DISPLAY_NAME "DBMS-Specific Components")
set(CPACK_COMPONENT_GROUP_PORTS_DESCRIPTION "DBMS-specific files and libraries.")
set(CPACK_COMPONENT_GROUP_PORTS_EXPANDED TRUE)

# Configuration for component group "Greenplum"
set(CPACK_COMPONENT_GROUP_GREENPLUM_DISPLAY_NAME "Greenplum Support")

# Configuration for component "Greenplum_any"
set(CPACK_COMPONENT_GREENPLUM_ANY_DISPLAY_NAME "All Versions")
set(CPACK_COMPONENT_GREENPLUM_ANY_DESCRIPTION "MADlib files shared by all Greenplum versions.")
set(CPACK_COMPONENT_GREENPLUM_ANY_GROUP Greenplum)

# Configuration for component "greenplum_4_2"
set(CPACK_COMPONENT_GREENPLUM_4_2_DISPLAY_NAME "4.2")
set(CPACK_COMPONENT_GREENPLUM_4_2_DESCRIPTION "MADlib files specific to Greenplum 4.2.")
set(CPACK_COMPONENT_GREENPLUM_4_2_GROUP Greenplum)
