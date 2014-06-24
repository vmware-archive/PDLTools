# ======================================================================
# -- CMake setup
# ======================================================================

project(DSTools)

cmake_minimum_required(VERSION 2.8.4 FATAL_ERROR)

include(ExternalProject)

# ======================================================================
# -- Local definitions (filenames, paths, etc.)
# ======================================================================

# The default DSTools root directory should be "/usr/local/dstools" and not
# "/usr/local" (which is the CMake default)

if(CMAKE_INSTALL_PREFIX_INITIALIZED_TO_DEFAULT)
  set(CMAKE_INSTALL_PREFIX "/usr/local/dstools" CACHE PATH
    "Install path prefix, prepended onto install directories." FORCE
    )
endif(CMAKE_INSTALL_PREFIX_INITIALIZED_TO_DEFAULT)

set(DSTOOLS_VERSION_YML ${CMAKE_CURRENT_SOURCE_DIR}/src/config/Version.yml)

set(DSTOOLS_THIRD_PARTY ${CMAKE_BINARY_DIR}/third_party)

# Set the directory for tools needed during build time
set(DSTOOLS_BUILD_TOOLS ${CMAKE_CURRENT_SOURCE_DIR}/cmake)

# Read and parse Version.yml file
message ("   ------------------------------------------------------------")
message ("   DSTOOLS VERSION INFO (${DSTOOLS_VERSION_YML})")

file(READ "${DSTOOLS_VERSION_YML}" _DSTOOLS_VERSION_CONTENTS)
string(REGEX REPLACE "^.*version:[ \t]*([^\n]*)\n.*" "\\1"    DSTOOLS_VERSION_STRING "${_DSTOOLS_VERSION_CONTENTS}")
string(REGEX REPLACE "([0-9]+).*" "\\1"                       DSTOOLS_VERSION_MAJOR  "${DSTOOLS_VERSION_STRING}")
string(REGEX REPLACE "[0-9]+\\.([0-9]+).*" "\\1"              DSTOOLS_VERSION_MINOR  "${DSTOOLS_VERSION_STRING}")

if("${DSTOOLS_VERSION_STRING}" MATCHES "[0-9]+\\.[0-9]+\\.([0-9]+).*")
  string(REGEX REPLACE "[0-9]+\\.[0-9]+\\.([0-9]+).*" "\\1" DSTOOLS_VERSION_PATCH  "${DSTOOLS_VERSION_STRING}")
else()
  set(DSTOOLS_VERSION_PATCH 0)
endif()

message ("     DSTOOLS_VERSION_STRING .. : ${DSTOOLS_VERSION_STRING}")
message ("     DSTOOLS_VERSION_MAJOR ... : ${DSTOOLS_VERSION_MAJOR}")
message ("     DSTOOLS_VERSION_MINOR ... : ${DSTOOLS_VERSION_MINOR}")
message ("     DSTOOLS_VERSION_PATCH ... : ${DSTOOLS_VERSION_PATCH}")
message ("   ------------------------------------------------------------")

# ===============================================================
# -- Install Read-me files and license directory
# ===============================================================

install(DIRECTORY "${CMAKE_CURRENT_SOURCE_DIR}/license"
    DESTINATION .
    COMPONENT core
    PATTERN ".DS_Store" EXCLUDE
)
install(
    FILES
        "${CMAKE_CURRENT_SOURCE_DIR}/README.md"
    DESTINATION doc
    COMPONENT core
)

# ======================================================================
# -- Local includes
# ======================================================================

list(APPEND CMAKE_MODULE_PATH
  "${DSTOOLS_BUILD_TOOLS}")

include(Utils)
include(LinuxUtils)
include(OSXUtils)

if(CMAKE_COMPILER_IS_GNUCC)
  # Let's store the gcc version in a variable
  execute_process(
    COMMAND ${CMAKE_C_COMPILER} -dumpversion
    OUTPUT_VARIABLE GNUCC_VERSION
    OUTPUT_STRIP_TRAILING_WHITESPACE)
  
  # A useful summary of warning options can be found here:
  # http://developer.apple.com/tools/xcode/compilercodewarnings.html
  # Note: gcc does not implicitly set _POSIX_C_SOURCE or _XOPEN_SOURCE
  # when using -std=c99.
  # http://pubs.opengroup.org/onlinepubs/9699919799/functions/V2_chap02.html#tag_15_02_01_01
  # We specify that we are POSIX.1-2001 compliant and XSI-conforming. We only
  # need to specify _XOPEN_SOURCE as _POSIX_C_SOURCE will be set implicitly.
  set(CMAKE_C_FLAGS "-std=c99 -pedantic -Wall -Wextra -D_XOPEN_SOURCE=600"
    CACHE STRING
    "Flags used by the compiler during all build types." FORCE)
endif()

# ======================================================================
# -- Add subdirectories
# ======================================================================

add_subdirectory(src)
add_subdirectory(deploy)
add_subdirectory(doc)

# ======================================================================
# -- Install path for specific dstools version
# ======================================================================

set(CMAKE_DSTOOLS_ROOT "${CMAKE_INSTALL_PREFIX}")
set(CMAKE_INSTALL_PREFIX "${CMAKE_DSTOOLS_ROOT}/Versions/${DSTOOLS_VERSION_STRING}")

# Create symlink doc
install(CODE "
    EXECUTE_PROCESS(COMMAND ln -nsf
           ${CMAKE_DSTOOLS_ROOT}/Current/doc
           ${CMAKE_DSTOOLS_ROOT}/doc
           )
")

