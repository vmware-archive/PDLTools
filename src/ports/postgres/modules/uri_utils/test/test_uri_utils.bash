#!/bin/bash

# This file runs the "test_uri_utils.sql" unit test script. It then compares
# the result with the expected output. A good execution is one that returns
# nothing.
# Differences between the expected and actual output will appear on stdout.

echo '\i uri_utils.sql \\ \i test_uri_utils.sql' | psql -q > test_result.txt 2> /dev/null
diff test_result_compare.txt test_result.txt
rm test_result.txt

