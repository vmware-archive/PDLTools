-- File: test_uri_utils.sql
-- Unit test for URI utility.

SELECT ds_tools.parse_uri();

SELECT ds_tools.parse_uri('unrecognized');

SELECT ds_tools.parse_uri('usage');

SELECT ds_tools.parse_uri('http://myself:password@www.goPivotal.com:80/%7ehello/to/you/index.html?who=I&whom=me&more=a%20%22''%5E%5e%41#here',false,false);

SELECT ds_tools.parse_uri('http://myself:password@www.goPivotal.com:80/%7ehello/to/you/index.html?who=I&whom=me&more=a%20%22''%5E%5e%41#here',false,true);

SELECT ds_tools.parse_uri('http://myself:password@www.goPivotal.com:80/%7ehello/to/you/index.html?who=I&whom=me&more=a%20%22''%5E%5e%41#here',true,false);

SELECT ds_tools.parse_uri('http://myself:password@www.goPivotal.com:80/%7ehello/to/you/index.html?who=I&whom=me&more=a%20%22''%5E%5e%41#here',true,true);

SELECT ds_tools.parse_uri('file:hello/world.txt',false,false);

SELECT ds_tools.parse_uri('file:/hello/world.txt',false,false);

SELECT ds_tools.parse_uri('http://MySelf@50.77.25.14:80/',true,false);

SELECT ds_tools.parse_uri('http://MySelf@[0123:4567:89ab:cdef:0123:4567:89ab:cdef]/hello.html',true,true);

SELECT ds_tools.extract_uri();

SELECT ds_tools.extract_uri('unrecognized');

SELECT ds_tools.extract_uri('usage');

SELECT ds_tools.extract_uri('First go to http://MySelf:password@[0123:4567:89ab:cdef:0123:4567:89ab:cdef]/~hello/to/you/index.html?who=I&whom=me&more=a%20%22%5E%5e%41/hello.html then go to https://goPivotal.com/ and repeat.',false);

SELECT ds_tools.extract_uri('First go to http://MySelf:password@[0123:4567:89ab:cdef:0123:4567:89ab:cdef]/~hello/to/you/index.html?who=I&whom=me&more=a%20%22%5E%5e%41/hello.html#fragment then go to https://goPivotal.com/ and repeat.',true);

SELECT ds_tools.parse_domain();

SELECT ds_tools.parse_domain('usage');

SELECT ds_tools.parse_domain('www.gopivotal.com');

