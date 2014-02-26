set(file "/home/pivotal/code/dstools/cmake/third_party/downloads/cpptest-1.1.2.tar.gz")
message(STATUS "verifying file...
     file='${file}'")
set(expect_value "79b9bff371d182f11a3235969f84ccb6")
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
