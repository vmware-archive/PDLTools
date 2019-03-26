# ======================================================================
# -- CMake setup
# ======================================================================

project(PDLTools)

cmake_minimum_required(VERSION 2.8.4 FATAL_ERROR)

include(ExternalProject)

# ======================================================================
# -- Local definitions (filenames, paths, etc.)
# ======================================================================

# The default PDL Tools root directory should be "/usr/local/pdltools" and not
# "/usr/local" (which is the CMake default)

if(CMAKE_INSTALL_PREFIX_INITIALIZED_TO_DEFAULT)
  set(CMAKE_INSTALL_PREFIX "/usr/local/pdltools" CACHE PATH
    "Install path prefix, prepended onto install directories." FORCE
    )
endif(CMAKE_INSTALL_PREFIX_INITIALIZED_TO_DEFAULT)

set(PDLTOOLS_VERSION_YML ${CMAKE_CURRENT_SOURCE_DIR}/src/config/Version.yml)

set(PDLTOOLS_THIRD_PARTY ${CMAKE_BINARY_DIR}/third_party)

# Set the directory for tools needed during build time
set(PDLTOOLS_BUILD_TOOLS ${CMAKE_CURRENT_SOURCE_DIR}/cmake)

# Read and parse Version.yml file
message ("   ------------------------------------------------------------")
message ("   PDLTOOLS VERSION INFO (${PDLTOOLS_VERSION_YML})")

file(READ "${PDLTOOLS_VERSION_YML}" _PDLTOOLS_VERSION_CONTENTS)
string(REGEX REPLACE "^.*version:[ \t]*([^\n]*)\n.*" "\\1"    PDLTOOLS_VERSION_STRING "${_PDLTOOLS_VERSION_CONTENTS}")
string(REGEX REPLACE "([0-9]+).*" "\\1"                       PDLTOOLS_VERSION_MAJOR  "${PDLTOOLS_VERSION_STRING}")
string(REGEX REPLACE "[0-9]+\\.([0-9]+).*" "\\1"              PDLTOOLS_VERSION_MINOR  "${PDLTOOLS_VERSION_STRING}")

if("${PDLTOOLS_VERSION_STRING}" MATCHES "[0-9]+\\.[0-9]+\\.([0-9]+).*")
  string(REGEX REPLACE "[0-9]+\\.[0-9]+\\.([0-9]+).*" "\\1" PDLTOOLS_VERSION_PATCH  "${PDLTOOLS_VERSION_STRING}")
else()
  set(PDLTOOLS_VERSION_PATCH 0)
endif()

message ("     PDLTOOLS_VERSION_STRING .. : ${PDLTOOLS_VERSION_STRING}")
message ("     PDLTOOLS_VERSION_MAJOR ... : ${PDLTOOLS_VERSION_MAJOR}")
message ("     PDLTOOLS_VERSION_MINOR ... : ${PDLTOOLS_VERSION_MINOR}")
message ("     PDLTOOLS_VERSION_PATCH ... : ${PDLTOOLS_VERSION_PATCH}")
message ("   ------------------------------------------------------------")


# ------------------------------------------------------------------
# Find M4 binary (we need this for  doxygen docs pre-processing)
# ------------------------------------------------------------------
if(SOLARIS)
    # Solaris ships GNU m4 as gm4, so we want to use that
    find_program(M4_BINARY gm4
        PATHS /usr/sfw/bin
        DOC "Path to the GNU m4 preprocessor."
    )
else()
    find_program(M4_BINARY m4
        PATHS /usr/local/bin /usr/bin /bin /opt/local/bin
        DOC "Path to the GNU m4 preprocessor."
    )
endif()

if(NOT M4_BINARY)
    message(FATAL_ERROR "Cannot find the m4 preprocessor.")
endif(NOT M4_BINARY)



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
  "${PDLTOOLS_BUILD_TOOLS}")

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
  # https://developer.apple.com/tools/xcode/compilercodewarnings.html
  # Note: gcc does not implicitly set _POSIX_C_SOURCE or _XOPEN_SOURCE
  # when using -std=c99.
  # https://pubs.opengroup.org/onlinepubs/9699919799/functions/V2_chap02.html#tag_15_02_01_01
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
# -- Install path for specific pdltools version
# ======================================================================

set(CMAKE_PDLTOOLS_ROOT "${CMAKE_INSTALL_PREFIX}")
set(CMAKE_INSTALL_PREFIX "${CMAKE_PDLTOOLS_ROOT}/Versions/${PDLTOOLS_VERSION_STRING}")

# Create symlink doc
install(CODE "
    EXECUTE_PROCESS(COMMAND ln -nsf
           ${CMAKE_PDLTOOLS_ROOT}/Current/doc
           ${CMAKE_PDLTOOLS_ROOT}/doc
           )
")

