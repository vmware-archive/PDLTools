
    file(MAKE_DIRECTORY
        "${CMAKE_CURRENT_BINARY_DIR}/4.2/BUILD"
        "${CMAKE_CURRENT_BINARY_DIR}/4.2/SPECS"
        "${CMAKE_CURRENT_BINARY_DIR}/4.2/RPMS"
        "${CMAKE_CURRENT_BINARY_DIR}/4.2/gppkg"
    )
    set(GPDB_VERSION 4.2)
    configure_file(
        dstools.spec.in
        "${CMAKE_CURRENT_BINARY_DIR}/4.2/SPECS/dstools.spec"
    )
    configure_file(
        gppkg_spec.yml.in
        "${CMAKE_CURRENT_BINARY_DIR}/4.2/gppkg/gppkg_spec.yml"
    )
    if(GPPKG_BINARY AND RPMBUILD_BINARY)
        add_custom_target(gppkg_4_2
            COMMAND cmake -E create_symlink "${DSTOOLS_GPPKG_RPM_SOURCE_DIR}"
                "${CPACK_PACKAGE_FILE_NAME}-gppkg"
            COMMAND "${RPMBUILD_BINARY}" -bb SPECS/dstools.spec
            COMMAND cmake -E rename RPMS/${DSTOOLS_GPPKG_RPM_FILE_NAME}
                gppkg/${DSTOOLS_GPPKG_RPM_FILE_NAME}
            COMMAND "${GPPKG_BINARY}" --build gppkg
            DEPENDS "/home/pivotal/code/dstools/cmake/${CPACK_PACKAGE_FILE_NAME}.rpm"
            WORKING_DIRECTORY "${CMAKE_CURRENT_BINARY_DIR}/4.2"
            COMMENT "Generating Greenplum 4.2 gppkg installer..."
            VERBATIM
        )
    else(GPPKG_BINARY AND RPMBUILD_BINARY)
        add_custom_target(gppkg_4_2
            COMMAND cmake -E echo "Could not find gppkg and/or rpmbuild."
                "Please rerun cmake."
        )
    endif(GPPKG_BINARY AND RPMBUILD_BINARY)
    
    # Unfortunately, we cannot set a dependency to the built-in package target,
    # i.e., the following does not work:
    # add_dependencies(gppkg package)
    
    add_dependencies(gppkg gppkg_4_2)
    