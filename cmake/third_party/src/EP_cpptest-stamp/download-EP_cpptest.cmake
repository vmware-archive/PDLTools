message(STATUS "downloading...
     src='http://sourceforge.net/projects/cpptest/files/cpptest-1.1.2.tar.gz'
     dst='/home/pivotal/code/dstools/cmake/third_party/downloads/cpptest-1.1.2.tar.gz'
     timeout='none'")




file(DOWNLOAD
  "http://sourceforge.net/projects/cpptest/files/cpptest-1.1.2.tar.gz"
  "/home/pivotal/code/dstools/cmake/third_party/downloads/cpptest-1.1.2.tar.gz"
  SHOW_PROGRESS
  EXPECTED_HASH;MD5=79b9bff371d182f11a3235969f84ccb6
  # no TIMEOUT
  STATUS status
  LOG log)

list(GET status 0 status_code)
list(GET status 1 status_string)

if(NOT status_code EQUAL 0)
  message(FATAL_ERROR "error: downloading 'http://sourceforge.net/projects/cpptest/files/cpptest-1.1.2.tar.gz' failed
  status_code: ${status_code}
  status_string: ${status_string}
  log: ${log}
")
endif()

message(STATUS "downloading... done")
