# ======================================================================
# -- DSTools CMake Build Script
# ======================================================================

# ======================================================================
# -- Paths and MD5 hashes of third-party downloadable source code
# ======================================================================

# For in-house testing, we might want to change the base URLs of code-hosting
# sites to something local
# "-DSOURCEFORGE_BASE_URL=http://test.local/projects"

set(SOURCEFORGE_BASE_URL
  "http://sourceforge.net/projects"
  CACHE STRING
  "Base URL for Sourceforge projects. May be overridden for testing purposes.")

# ======================================================================
# -- CPPTest (third_party)
# ======================================================================

set(CPPTEST_TAR_VERSION "1.1.2")
set(CPPTEST_TAR_MD5 79b9bff371d182f11a3235969f84ccb6)

set(CPPTEST_TAR "cpptest-${CPPTEST_TAR_VERSION}.tar.gz")
set(CPPTEST_URL "${SOURCEFORGE_BASE_URL}/cpptest/files/${CPPTEST_TAR}")

if(NOT CPPTEST_TAR_SOURCE)
  find_file(CPPTEST_TAR_SOURCE ${CPPTEST_TAR}
    PATHS ${DSTOOLS_THIRD_PARTY}/downloads)
endif(NOT CPPTEST_TAR_SOURCE)

if(NOT CPPTEST_TAR_SOURCE)
  set(CPPTEST_TAR_SOURCE ${CPPTEST_URL})
endif (NOT CPPTEST_TAR_SOURCE)

ExternalProject_Add(EP_cpptest
  PREFIX ${DSTOOLS_THIRD_PARTY}
  DOWNLOAD_DIR ${DSTOOLS_THIRD_PARTY}/downloads
  URL ${CPPTEST_TAR_SOURCE}
  URL_MD5 ${CPPTEST_TAR_MD5}
  CONFIGURE_COMMAND ./configure --disable-doc --prefix=${DSTOOLS_THIRD_PARTY}/install
  BUILD_COMMAND make
  INSTALL_COMMAND make install
  BINARY_DIR ${DSTOOLS_THIRD_PARTY}/src/EP_cpptest)

# ======================================================================
# -- URIParser (third_party)
# ======================================================================

set(URIPARSER_TAR_VERSION "0.7.9")
set(URIPARSER_TAR_MD5 d9189834b909df8d672ecafc34186a58)

set(URIPARSER_TAR "uriparser-${URIPARSER_TAR_VERSION}.tar.bz2")
set(URIPARSER_URL "${SOURCEFORGE_BASE_URL}/uriparser/files/${URIPARSER_TAR}")

if(NOT URIPARSER_TAR_SOURCE)
  find_file(URIPARSER_TAR_SOURCE ${URIPARSER_TAR}
    PATHS ${DSTOOLS_THIRD_PARTY}/downloads)
endif(NOT URIPARSER_TAR_SOURCE)

if(NOT URIPARSER_TAR_SOURCE)
  set(URIPARSER_TAR_SOURCE ${URIPARSER_URL})
endif (NOT URIPARSER_TAR_SOURCE)

ExternalProject_Add(EP_uriparser
  PREFIX ${DSTOOLS_THIRD_PARTY}
  DOWNLOAD_DIR ${DSTOOLS_THIRD_PARTY}/downloads
  URL ${URIPARSER_TAR_SOURCE}
  URL_MD5 ${URIPARSER_TAR_MD5}
  CONFIGURE_COMMAND ./configure --disable-doc CPPTEST_CFLAGS=-I${DSTOOLS_THIRD_PARTY}/install CPPTEST_LIBS=${DSTOOLS_THIRD_PARTY}/install/lib --prefix=${DSTOOLS_THIRD_PARTY}/install
  BUILD_COMMAND make
  INSTALL_COMMAND make install
  BINARY_DIR ${DSTOOLS_THIRD_PARTY}/src/EP_uriparser)

include_directories(${DSTOOLS_THIRD_PARTY}/install/include)
link_directories(${DSTOOLS_THIRD_PARTY}/install/lib)

# ======================================================================
# -- Macros to be used by ports
# ======================================================================

# Get the architectures in a Mac OS X binary
macro(osx_archs FILENAME OUT_ARCHS)
  execute_process(
    COMMAND /usr/bin/lipo -info ${FILENAME}
    OUTPUT_VARIABLE _LIPO_OUTPUT)
  string(REPLACE "\n" "" _LIPO_OUTPUT ${_LIPO_OUTPUT})
  string(REGEX REPLACE ".*:[ ]*([^ ].*[^ ])[ ]*\$" "\\1" ${OUT_ARCHS} "${_LIPO_OUTPUT}")
  string(REPLACE " " ";" ${OUT_ARCHS} ${${OUT_ARCHS}})
endmacro(osx_archs)

# Add Python files to be preprocessed with m4
macro(add_python_files OUT_PYTHON_TARGET_FILES IN_SOURCE_DIR IN_TARGET_DIR)
  set(IN_M4_ARGUMENTS ${ARGN})
  
  get_filename_component(SOURCE_DIR_ABS "${IN_SOURCE_DIR}" ABSOLUTE)
  get_filename_component(TARGET_DIR_ABS "${IN_TARGET_DIR}" ABSOLUTE)
  file(GLOB_RECURSE PYTHON_FILES
    RELATIVE "${SOURCE_DIR_ABS}"
    "${SOURCE_DIR_ABS}/*.py_in")
  set(DSTOOLS_PYTHON_M4_PREPROCESSING
    COMMAND ${CMAKE_COMMAND} -E make_directory "\"\${OUTDIR}\""
    COMMAND ${M4_BINARY} ${M4_ARGUMENTS} ${IN_M4_ARGUMENTS}
    "\"\${CURRENT_PATH}\"" > "\"\${OUTFILE}\"")
  batch_add_command(
    TARGET_PREFIX "${TARGET_DIR_ABS}/"
    SOURCE_PREFIX "${SOURCE_DIR_ABS}/"
    TARGET_SUFFIX ".py"
    SOURCE_SUFFIX "[.]py_in"
    RUN "${DSTOOLS_PYTHON_M4_PREPROCESSING}"
    COMMENT "Preprocessing \${CURRENT_FILE} with m4."
    TARGET_FILE_LIST_REF ${OUT_PYTHON_TARGET_FILES}
    SOURCE_FILE_LIST ${PYTHON_FILES})
endmacro(add_python_files)

# Add sql files to be copied
macro(add_sql_files OUT_SQL_TARGET_FILES IN_SOURCE_DIR IN_TARGET_DIR)
  get_filename_component(SOURCE_DIR_ABS "${IN_SOURCE_DIR}" ABSOLUTE)
  get_filename_component(TARGET_DIR_ABS "${IN_TARGET_DIR}" ABSOLUTE)
  file(GLOB_RECURSE SQL_FILES
    RELATIVE "${SOURCE_DIR_ABS}"
    "${SOURCE_DIR_ABS}/*.sql_in")
 
    # psql of PostgreSQL < 9 does not like byte-order marks
    # TBD: This chunk has been copied & edited from MADlib cmake. Will need to
    # revisit this later to see if it is even required for DStools
    set(_DSTOOLS_VERIFY_AND_COPY_COMMAND
        COMMAND "${CMAKE_COMMAND}" -E copy "\"\${CURRENT_PATH}\"""\"\${OUTFILE}\"")

  batch_add_command(
    TARGET_PREFIX "${TARGET_DIR_ABS}/"
    SOURCE_PREFIX "${SOURCE_DIR_ABS}/"
    TARGET_SUFFIX ""
    SOURCE_SUFFIX ""
    RUN "${_DSTOOLS_VERIFY_AND_COPY_COMMAND}"
    COMMENT "Validating and copying \${CURRENT_FILE}."
    TARGET_FILE_LIST_REF ${OUT_SQL_TARGET_FILES}
    SOURCE_FILE_LIST ${SQL_FILES})
endmacro(add_sql_files)

# Add a connector library for a specific DBMS port
macro(add_dstools_connector_library IN_TARGET_NAME IN_LIB_DIR IN_LIB_LOADER)
  set(IN_LIBRARY_SOURCES ${ARGN})
 
  add_library(
    ${IN_TARGET_NAME}
    MODULE
    ${IN_LIBRARY_SOURCES})
  add_dependencies(${IN_TARGET_NAME} EP_uriparser)
  set_target_properties(${IN_TARGET_NAME} PROPERTIES
    LIBRARY_OUTPUT_DIRECTORY "${IN_LIB_DIR}"
    OUTPUT_NAME "dstools"
    BUILD_WITH_INSTALL_RPATH YES)
  
  if(APPLE)
    set_target_properties(${IN_TARGET_NAME} PROPERTIES
      LINK_FLAGS
      "-Wl -bundle_loader \"${IN_LIB_LOADER}\" -luriparser")
  endif(APPLE)
  
  if((NOT APPLE)) 
    set_target_properties(${IN_TARGET_NAME} PROPERTIES
      LINK_FLAGS
      "-Wl")
  endif((NOT APPLE))
endmacro(add_dstools_connector_library)

# ======================================================================
# -- Speciy files that will be compiled into DSTools core library
# ======================================================================

file(GLOB_RECURSE DSTOOLS_C_SOURCES
  modules/*.c modules/*.h)

list(APPEND DSTOOLS_SOURCES
  ${DSTOOLS_C_SOURCES})

add_subdirectory(ports)
