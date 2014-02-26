
    cpack_add_component_group(Greenplum
        DISPLAY_NAME "Greenplum Support"
        DESCRIPTION "MADlib support for Greenplum."
        PARENT_GROUP ports
    )
    cpack_add_component(Greenplum_any
        DISPLAY_NAME "All Versions"
        DESCRIPTION "MADlib files shared by all Greenplum versions."
        GROUP Greenplum
    )
    cpack_add_component(greenplum_4_2
        DISPLAY_NAME "4.2"
        DESCRIPTION "MADlib files specific to Greenplum 4.2."
        GROUP Greenplum
    )