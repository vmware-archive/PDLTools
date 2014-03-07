# ------------------------------------------------------------------------------
# DSTools binary files
# ------------------------------------------------------------------------------


# -- 1. Copy files -------------------------------------------------------------

set(DSPACK_BINARIES
    dspack
)
add_files(BINARY_TARGET_FILES . "${CMAKE_CURRENT_BINARY_DIR}" ${DSPACK_BINARIES})
add_custom_target(binaryFiles ALL DEPENDS ${BINARY_TARGET_FILES})
add_dependencies(binaryFiles dspackFiles)


# -- 2. Install binary files to $DSTOOLS_ROOT/bin -------------------------------

install(PROGRAMS ${BINARY_TARGET_FILES}
    DESTINATION bin
    COMPONENT core
)
