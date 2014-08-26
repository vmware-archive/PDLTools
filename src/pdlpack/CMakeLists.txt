# ------------------------------------------------------------------------------
# pdlpack source files
# ------------------------------------------------------------------------------

# -- 1. Copy all *.py files ----------------------------------------------------

file(GLOB_RECURSE PDLPACK_FILES
    RELATIVE "${CMAKE_CURRENT_SOURCE_DIR}"
    "*.py"
)
add_files(PDLPACK_TARGET_FILES . "${CMAKE_CURRENT_BINARY_DIR}" ${PDLPACK_FILES})
add_custom_target(pdlpackFiles ALL DEPENDS ${PDLPACK_TARGET_FILES})


# -- 2. Install pdlpack files to $PDLTOOLS_ROOT/pdlpack, set executable flags
#       for pdlpack.py ---------------------------------------------------------

install(DIRECTORY ${CMAKE_CURRENT_BINARY_DIR}
    DESTINATION .
    USE_SOURCE_PERMISSIONS
    COMPONENT core
    FILES_MATCHING
    PATTERN "*.py"
    PATTERN ".DS_Store" EXCLUDE
)

