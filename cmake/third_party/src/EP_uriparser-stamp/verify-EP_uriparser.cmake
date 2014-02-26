set(file "/home/pivotal/code/dstools/cmake/third_party/downloads/uriparser-0.7.9.tar.bz2")
message(STATUS "verifying file...
     file='${file}'")
set(expect_value "d9189834b909df8d672ecafc34186a58")
file(MD5 "${file}" actual_value)
if("${actual_value}" STREQUAL "${expect_value}")
  message(STATUS "verifying file... done")
else()
  message(FATAL_ERROR "error: MD5 hash of
  ${file}
does not match expected value
  expected: ${expect_value}
    actual: ${actual_value}
")
endif()
