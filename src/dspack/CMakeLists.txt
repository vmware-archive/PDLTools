# ------------------------------------------------------------------------------
# dspack source files
# ------------------------------------------------------------------------------

# -- 1. Copy all *.py files ----------------------------------------------------

file(GLOB_RECURSE DSPACK_FILES
    RELATIVE "${CMAKE_CURRENT_SOURCE_DIR}"
    "*.py"
)
add_files(DSPACK_TARGET_FILES . "${CMAKE_CURRENT_BINARY_DIR}" ${DSPACK_FILES})
add_custom_target(dspackFiles ALL DEPENDS ${DSPACK_TARGET_FILES})


# -- 2. Install dspack files to $DSTOOLS_ROOT/dspack, set executable flags
#       for dspack.py ---------------------------------------------------------

install(DIRECTORY ${CMAKE_CURRENT_BINARY_DIR}
    DESTINATION .
    USE_SOURCE_PERMISSIONS
    COMPONENT core
    FILES_MATCHING
    PATTERN "*.py"
    PATTERN ".DS_Store" EXCLUDE
)

