# ------------------------------------------------------------------------------
# Packaging for the PostgreSQL Extension Network (PGXN), http://pgxn.org
# ------------------------------------------------------------------------------

set(PDLTOOLS_PGXN_RELEASE_NUMBER 1)
set(PDLTOOLS_PGXN_VERSION_STR
    "${PDLTOOLS_VERSION_MAJOR}.${PDLTOOLS_VERSION_MINOR}.${PDLTOOLS_VERSION_PATCH}release${PDLTOOLS_PGXN_RELEASE_NUMBER}")
set(PDLTOOLS_PGXN_NAME "pdltools-pgxn-${PDLTOOLS_PGXN_VERSION_STR}")

configure_file(META.json.in META.json)
configure_file(generate_package.sh.in generate_package.sh @ONLY)
configure_file(zipignore.in zipignore)
add_custom_command(
    OUTPUT pdltools.zip
    COMMAND "${CMAKE_COMMAND}" -E create_symlink
        "${CMAKE_CURRENT_BINARY_DIR}/META.json"
        "${CMAKE_SOURCE_DIR}/META.json"
    COMMAND "${CMAKE_CURRENT_BINARY_DIR}/generate_package.sh"
    COMMAND "${CMAKE_COMMAND}" -E remove
        "${CMAKE_SOURCE_DIR}/META.json"
    COMMENT "Creating PGXN zip file."
    VERBATIM
)
add_custom_target(pgxn DEPENDS pdltools.zip)
