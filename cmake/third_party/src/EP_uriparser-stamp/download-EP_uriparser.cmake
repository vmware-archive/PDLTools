message(STATUS "downloading...
     src='http://sourceforge.net/projects/uriparser/files/uriparser-0.7.9.tar.bz2'
     dst='/home/pivotal/code/dstools/cmake/third_party/downloads/uriparser-0.7.9.tar.bz2'
     timeout='none'")




file(DOWNLOAD
  "http://sourceforge.net/projects/uriparser/files/uriparser-0.7.9.tar.bz2"
  "/home/pivotal/code/dstools/cmake/third_party/downloads/uriparser-0.7.9.tar.bz2"
  SHOW_PROGRESS
  EXPECTED_HASH;MD5=d9189834b909df8d672ecafc34186a58
  # no TIMEOUT
  STATUS status
  LOG log)

list(GET status 0 status_code)
list(GET status 1 status_string)

if(NOT status_code EQUAL 0)
  message(FATAL_ERROR "error: downloading 'http://sourceforge.net/projects/uriparser/files/uriparser-0.7.9.tar.bz2' failed
  status_code: ${status_code}
  status_string: ${status_string}
  log: ${log}
")
endif()

message(STATUS "downloading... done")
