# ------------------------------------------------------------------------------
# PDL Tools binary files
# ------------------------------------------------------------------------------


# -- 1. Copy files -------------------------------------------------------------

set(PDLPACK_BINARIES
    pdlpack
)
add_files(BINARY_TARGET_FILES . "${CMAKE_CURRENT_BINARY_DIR}" ${PDLPACK_BINARIES})
add_custom_target(binaryFiles ALL DEPENDS ${BINARY_TARGET_FILES})
add_dependencies(binaryFiles pdlpackFiles)


# -- 2. Install binary files to $PDLTOOLS_ROOT/bin -------------------------------

install(PROGRAMS ${BINARY_TARGET_FILES}
    DESTINATION bin
    COMPONENT core
)
