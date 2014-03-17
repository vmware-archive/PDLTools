'''
Simple Python based installer of DStools. In time this will involve to become more complex
but perhaps not quite as complex as madpack :-)
Note: Large portions of this script have been copied from madpack.py
Srivatsan Ramanujam
<sramanujam@gopivotal.com>
28 Jan 2014

Usage:
======
python dspack.py [-s schema_name] -c <username>@<hostname>:<port>/<databasename>
'''

import os, sys, getpass, re, subprocess, tempfile, glob
import argparse, configyml

dstoolsdir = None
dstoolsdir_conf = None
rev = None
this = None
py_min_ver = None
con_args={}
verbose=False
testcase=None
tmpdir=None

def checkPythonVersion():
    # Required Python version
    py_min_ver = [2, 6]

    # Check python version
    if sys.version_info[:2] < py_min_ver:
        print "ERROR: python version too old (%s). You need %s or greater." \
	      % ('.'.join(str(i) for i in sys.version_info[:3]), '.'.join(str(i) for i in py_min_ver))
        exit(1)

def init():
    '''
        Initialize some variables, do some sanity testing of the environment
    '''
    global dstoolsdir, dstoolsdir_conf, rev, this, con_args, py_min_ver
    checkPythonVersion()
    dstoolsdir = os.path.abspath(os.path.dirname(os.path.realpath(__file__)) + "/..")
    dstoolsdir_conf = dstoolsdir+'/config'
    rev = configyml.get_version(dstoolsdir_conf)
    this = os.path.basename(sys.argv[0])    # name of this script
    sys.path.append(dstoolsdir + "/dspack")

init()


def __get_rev_num(rev):
    """
    Convert version string into number for comparison
        @param rev version text
    """
    try:
        num = re.findall('[0-9]', rev)
        if num:
            return num
        else:
            return ['0']
    except:
        return ['0']

def unescape(string):
    """
    Unescape separation characters in connection strings, i.e., remove first
    backslash from "\/", "\@", "\:", and "\\".
    """
    if string is None:
        return None
    else:
        return re.sub(r'\\(?P<char>[/@:\\])', '\g<char>', string)

def __run_sql_query(sql, show_error):
    """
    Runs a SQL query on the target platform DB
    using the default command-line utility.
    Very limited:
      - no text output with "new line" characters allowed
         @param sql query text to execute
         @param show_error displays the SQL error msg
    """
    return ____run_sql_query(sql, show_error)

def ____run_sql_query(sql, show_error):
        ''' Running SQL command '''
	sqlcmd = 'psql'
	delimiter = '|'

	# Test the DB cmd line utility
	std, err = subprocess.Popen(['which', sqlcmd], stdout=subprocess.PIPE,
		                    stderr=subprocess.PIPE).communicate()


	if std == '':
	    __error("Command not found: %s" % sqlcmd, True)

	# Run the query
	global con_args
	runcmd = [sqlcmd,
		  '-h', con_args['host'].split(':')[0],
		  '-d', con_args['database'],
		  '-U', con_args['user'],
		  '-F', delimiter,
		  '-Ac', "set CLIENT_MIN_MESSAGES=error; " + sql]
	runenv = os.environ
	runenv["PGPASSWORD"] = con_args['password']
	runenv["PGOPTIONS"] = '-c search_path=public'
	std, err = subprocess.Popen(runcmd, env=runenv, stdout=subprocess.PIPE,
		                    stderr=subprocess.PIPE).communicate()

	if err:
	    if show_error:
		__error("SQL command failed: \nSQL: %s \n%s" % (sql, err), False)
	    raise Exception

	# Convert the delimited output into a dictionary
	results = []  # list of rows
	i = 0
	for line in std.splitlines():
	    if i == 0:
		cols = [name for name in line.split(delimiter)]
	    else:
		row = {}  # dict of col_name:col_value pairs
		c = 0
		for val in line.split(delimiter):
		    row[cols[c]] = val
		    c += 1
		results.insert(i, row)
	    i += 1
	# Drop the last line: "(X rows)"
	try:
	    results.pop()
	except:
	    pass

	return results

def __run_sql_file(schema, maddir_mod_py, module, sqlfile,
                   tmpfile, logfile, pre_sql, upgrade=False,
                   sc=None):
    """Run SQL file
            @param schema name of the target schema
            @param maddir_mod_py name of the module dir with Python code
            @param module  name of the module
            @param sqlfile name of the file to parse
            @param tmpfile name of the temp file to run
            @param logfile name of the log file (stdout)
            @param pre_sql optional SQL to run before executing the file
            @param upgrade are we upgrading as part of this sql run
            @param sc object of ScriptCleaner
    """
    # Check if the SQL file exists
    if not os.path.isfile(sqlfile):
        __error("Missing module SQL file (%s)" % sqlfile, False)
        raise Exception

    # Prepare the file using M4
    try:
        f = open(tmpfile, 'w')

        # Add the before SQL
        if pre_sql:
            f.writelines([pre_sql, '\n\n'])
            f.flush()
        # Find the madpack dir (platform specific or generic)
        if os.path.isdir(dstoolsdir + "/ports/greenplum" + "/" + dbver + "/dspack"):
            dstoolsdir_dspack = dstoolsdir + "/ports/greenplum" + "/" + dbver + "/dspack"
        else:
            dstoolsdir_dspack = dstoolsdir + "/dspack"


        m4args = ['m4',
                  '-P',
                  '-DDSTOOLS_SCHEMA=' + schema,
                  '-DPLPYTHON_LIBDIR=' + maddir_mod_py,
                  '-DMODULE_PATHNAME=' + dstoolsdir_lib,
                  '-DMODULE_NAME=' + module,
                  '-I' + dstoolsdir_dspack,
                  sqlfile]

        __info("> ... parsing: " + " ".join(m4args), verbose)

        subprocess.call(m4args, stdout=f)
        f.close()
    except:
        __error("Failed executing m4 on %s" % sqlfile, False)
        raise Exception

    # Only update function definition
    sub_module = ''
    if upgrade:
        # get filename from complete path without the extension
        sub_module = os.path.splitext(os.path.basename(sqlfile))[0]
        __info(sub_module, False)

        # Special treatment for new module and 'svec' module
        if ((sub_module not in sc.get_change_handler().newmodule) and
                not (sub_module == 'svec' and
                     'svec' in sc.get_change_handler().udt)):
            sql = open(tmpfile).read()
            sql = sc.cleanup(sql)
            open(tmpfile, 'w').write(sql)

    # Run the SQL using DB command-line utility
    sqlcmd = 'psql'
    # Test the DB cmd line utility
    std, err = subprocess.Popen(['which', sqlcmd], stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE).communicate()
    if not std:
        __error("Command not found: %s" % sqlcmd, True)

    runcmd = [sqlcmd, '-a',
              '-v', 'ON_ERROR_STOP=1',
              '-h', con_args['host'].split(':')[0],
              '-d', con_args['database'],
              '-U', con_args['user'],
              '-f', tmpfile]
    runenv = os.environ
    runenv["PGPASSWORD"] = con_args['password']

    # Open log file
    try:
        log = open(logfile, 'w')
    except:
        __error("Cannot create log file: %s" % logfile, False)
        raise Exception

    # Run the SQL
    try:
        __info("> ... executing " + tmpfile, verbose)
        retval = subprocess.call(runcmd, env=runenv, stdout=log, stderr=log)
    except:
        __error("Failed executing %s" % tmpfile, False)
        raise Exception
    finally:
        log.close()

    return retval


def __plpy_check(py_min_ver):
    """
    Check pl/python existence and version
        @param py_min_ver min Python version to run MADlib
    """

    __info("Testing PL/Python environment...", True)

    # Check PL/Python existence
    rv = __run_sql_query("SELECT count(*) AS CNT FROM pg_language "
                         "WHERE lanname = 'plpythonu'", True)

    if int(rv[0]['cnt']) > 0:
        __info("> PL/Python already installed", verbose)
    else:
        __info("> PL/Python not installed", verbose)
        __info("> Creating language PL/Python...", True)
        try:
            __run_sql_query("CREATE LANGUAGE plpythonu;", True)
        except:
            __error('Cannot create language plpythonu. Stopping installation...', False)
            raise Exception

    # Check PL/Python version
    __run_sql_query("DROP FUNCTION IF EXISTS plpy_version_for_madlib();", False)
    __run_sql_query("""
        CREATE OR REPLACE FUNCTION plpy_version_for_madlib()
        RETURNS TEXT AS
        $$
            import sys
            # return '.'.join(str(item) for item in sys.version_info[:3])
            return str(sys.version_info[:3]).replace(',','.').replace(' ','').replace(')','').replace('(','')
        $$
        LANGUAGE plpythonu;
    """, True)
    rv = __run_sql_query("SELECT plpy_version_for_madlib() AS ver;", True)
    python = rv[0]['ver']
    py_cur_ver = [int(i) for i in python.split('.')]
    if py_cur_ver >= py_min_ver:
        __info("> PL/Python version: %s" % python, verbose)
    else:
        __error("PL/Python version too old: %s. You need %s or greater"
                % (python, '.'.join(str(i) for i in py_min_ver)), False)
        raise Exception

    __info("> PL/Python environment OK (version: %s)" % python, True)

def __error(msg, stop):
    """
    Error message wrapper
        @param msg error message
        @param stop program exit flag
    """
    # Print to stdout
    print this + ' : ERROR : ' + msg
    # Print stack trace
    if stop:
        exit(2)

def __info(msg, verbose=True):
    """
    Info message wrapper (verbose)
        @param msg info message
        @param verbose prints only if True
    """
    # Print to stdout
    if verbose:
        print this + ' : INFO : ' + msg

def __get_dbver():
    """ Read version number from database (of form X.Y) """
    try:
        versionStr = __run_sql_query("""SELECT pg_catalog.version()""",
                                     True)[0]['version']
 
        match = re.search("Greenplum[a-zA-Z\s]*(\d+\.\d+)", versionStr)

        return None if match is None else match.group(1)
    except:
        __error("Failed reading database version", True)

def __make_dir(dir):
    """
    # Create a temp dir
    # @param dir temp directory path
    """
    if not os.path.isdir(dir):
        try:
            os.makedirs(dir)
        except:
            print "ERROR: can not create directory: %s. Check permissions." % dir
            exit(1)

def __db_create_schema(schema):
    """
    Create schema
        @param from_schema name of the schema to rename
        @param to_schema new name for the schema
    """

    __info("> Creating %s schema" % schema.upper(), True)
    try:
        __run_sql_query("CREATE SCHEMA %s;" % schema, True)
    except:
        __info('Cannot create new schema. Rolling back installation...', True)
        pass


def __db_create_objects(schema, old_schema, upgrade=False, sc=None, testcase="",
                        hawq_debug=False, hawq_fresh=False):
    """
    Create MADlib DB objects in the schema
        @param schema Name of the target schema
        @param sc ScriptCleaner object
        @param testcase Command-line args for modules to install
    """
    if not upgrade and not hawq_debug:
        # Create MigrationHistory table
        try:
            __info("> Creating %s.MigrationHistory table" % schema.upper(), True)
            __run_sql_query("DROP TABLE IF EXISTS %s.migrationhistory;" % schema, True)
            sql = """CREATE TABLE %s.migrationhistory
                   (id serial, version varchar(255),
                    applied timestamp default current_timestamp);""" % schema
            __run_sql_query(sql, True)
        except:
            __error("Cannot crate MigrationHistory table", False)
            raise Exception

        # Copy MigrationHistory table for record keeping purposes
        if old_schema:
            try:
                __info("> Saving data from %s.MigrationHistory table" % old_schema.upper(), True)
                sql = """INSERT INTO %s.migrationhistory (version, applied)
                       SELECT version, applied FROM %s.migrationhistory
                       ORDER BY id;""" % (schema, old_schema)
                __run_sql_query(sql, True)
            except:
                __error("Cannot copy MigrationHistory table", False)
                raise Exception

    # Stamp the DB installation
    try:
        __info("> Writing version info in MigrationHistory table", True)
        __run_sql_query("INSERT INTO %s.migrationhistory(version) "
                        "VALUES('%s')" % (schema, rev), True)
    except:
        __error("Cannot insert data into %s.migrationhistory table" % schema, False)
        raise Exception

    # Run migration SQLs
    if upgrade:
        __info("> Creating/Updating objects for modules:", True)
    else:
        __info("> Creating objects for modules:", True)

    caseset = (set([test.strip() for test in testcase.split(',')])
               if testcase != "" else set())

    modset = {}
    for case in caseset:
        if case.find('/') > -1:
            [mod, algo] = case.split('/')
            if mod not in modset:
                modset[mod] = []
            if algo not in modset[mod]:
                modset[mod].append(algo)
        else:
            modset[case] = []

    # Loop through all modules/modules
    ## portspecs is a global variable
    for moduleinfo in portspecs['modules']:

        # Get the module name
        module = moduleinfo['name']

        # Skip if doesn't meet specified modules
        if modset is not None and len(modset) > 0 and module not in modset:
            continue

        __info("> - %s" % module, True)
 
        # Find the Python module dir (platform specific or generic)
        if os.path.isdir(dstoolsdir + "/ports/greenplum" + "/" + dbver + "/modules/" + module):
            maddir_mod_py = dstoolsdir + "/ports/greenplum" + "/" + dbver + "/modules"
        else:
            maddir_mod_py = dstoolsdir + "/modules"

        # Find the SQL module dir (platform specific or generic)
        if os.path.isdir(dstoolsdir + "/ports/greenplum" + "/modules/" + module):
            maddir_mod_sql = dstoolsdir + "/ports/greenplum" + "/modules"
        elif os.path.isdir(dstoolsdir + "/modules/" + module):
            maddir_mod_sql = dstoolsdir + "/modules"
        else:
            # This was a platform-specific module, for which no default exists.
            # We can just skip this module.
            continue

        # Make a temp dir for log files
        cur_tmpdir = tmpdir + "/" + module
        __make_dir(cur_tmpdir)

        # Loop through all SQL files for this module
        mask = maddir_mod_sql + '/' + module + '/*.sql_in'
        sql_files = glob.glob(mask)

        if not sql_files:
            __error("No files found in: %s" % mask, True)

        # Execute all SQL files for the module
        for sqlfile in sql_files:
            algoname = os.path.basename(sqlfile).split('.')[0]
            if (hawq_debug or hawq_fresh) and algoname in \
                    ('svec', 'rf'):
                continue

            if module in modset and len(modset[module]) > 0 and algoname not in modset[module]:
                continue

             # Set file names
            tmpfile = cur_tmpdir + '/' + os.path.basename(sqlfile) + '.tmp'
            logfile = cur_tmpdir + '/' + os.path.basename(sqlfile) + '.log'

            retval = __run_sql_file(schema, maddir_mod_py, module, sqlfile,
                                    tmpfile, logfile, None, upgrade,
                                    sc)
            # Check the exit status
            if retval != 0:
                __error("Failed executing %s" % tmpfile, False)
                __error("Check the log at %s" % logfile, False)
                raise Exception

def __db_rollback(drop_schema, keep_schema):
    """
    Rollback installation
        @param drop_schema name of the schema to drop
        @param keep_schema name of the schema to rename and keep
    """

    __info("Rolling back the installation...", True)

    if not drop_schema:
        __error('No schema name to drop. Stopping rollback...', True)

    # Drop the current schema
    __info("> Dropping schema %s" % drop_schema.upper(), verbose)
    try:
        __run_sql_query("DROP SCHEMA %s CASCADE;" % (drop_schema), True)
    except:
        __error("Cannot drop schema %s. Stopping rollback..." % drop_schema.upper(), True)

    # Rename old to current schema
    if keep_schema:
        __db_rename_schema(keep_schema, drop_schema)

    __info("Rollback finished successfully.", True)
    raise Exception


def __db_install(schema, dbrev, testcase):
    """
    Install MADlib
        @param schema dstools schema name
        @param dbrev DB-level dstools version
        @param testcase command-line args for a subset of modules
    """
    __info("Installing dstools into %s schema..." % schema.upper(), True)
    temp_schema = schema + '_v' + ''.join(__get_rev_num(dbrev))
    schema_writable = None

    # Test if schema is writable
    try:
        __run_sql_query("CREATE TABLE %s.__dstools_test_table (A INT);" % schema, False)
        __run_sql_query("DROP TABLE %s.__dstools_test_table;" % schema, False)
        schema_writable = True
    except:
        schema_writable = False

    if schema_writable:
       # Create dstools schema
       try:
            __db_create_schema(schema)
       except:
            __db_rollback(schema, temp_schema)

       # Create MADlib objects
       try:
            __db_create_objects(schema, temp_schema, testcase=testcase)
       except:
            __db_rollback(schema, temp_schema)

    else:
        __info("> Schema %s does not exist" % schema.upper(), verbose)

        # Create MADlib schema
        try:
            __db_create_schema(schema)
        except:
            __db_rollback(schema, None)

        # Create dstools objects
        try:
            __db_create_objects(schema, None, testcase=testcase)
        except:
            __db_rollback(schema, None)

    __info("DSTools %s installed successfully in %s schema." % (rev, schema.upper()), True)


def parseConnectionStr(connectionStr):
    """
    @brief Parse connection strings of the form
           <tt>[username[/password]@][hostname][:port][/database]</tt>

    Separation characters (/@:) and the backslash (\) need to be escaped.
    @returns A tuple (username, password, hostname, port, database). Field not
             specified will be None.
    """
    match = re.search(
        r'((?P<user>([^/@:\\]|\\/|\\@|\\:|\\\\)+)' +
        r'(/(?P<password>([^/@:\\]|\\/|\\@|\\:|\\\\)*))?@)?' +
        r'(?P<host>([^/@:\\]|\\/|\\@|\\:|\\\\)+)?' +
        r'(:(?P<port>[0-9]+))?' +
        r'(/(?P<database>([^/@:\\]|\\/|\\@|\\:|\\\\)+))?', connectionStr)
    return (
        unescape(match.group('user')),
        unescape(match.group('password')),
        unescape(match.group('host')),
        match.group('port'),
        unescape(match.group('database')))

def main():
    '''
        Fetch arguments and prepare installation of dstools in target DB
    '''
    parser = argparse.ArgumentParser(
                description='DSTools package manager (' + rev + ')',
                argument_default=False,
                formatter_class=argparse.RawTextHelpFormatter,
                epilog="""Example:

  $ dspack install -s dstools -c gpadmin@mdw:5432/testdb

  This will install DSTools objects into a Greenplum database called TESTDB
  running on server MDW:5432. Installer will try to login as GPADMIN
  and will prompt for password. The target schema will be dstools
""")

    parser.add_argument(
        'command', metavar='COMMAND', nargs=1,
        choices=['install'],
        help = "One of the following options:\n"
            + "  install        : run sql scripts to load into DB\n"
    )
    
    parser.add_argument(
        '-c', '--conn', metavar='CONNSTR', nargs=1, dest='connstr', default=None,
        help= "Connection string of the following syntax:\n"
            + "  [user[/password]@][host][:port][/database]\n"
            + "If not provided default values will be derived for PostgreSQL and Greenplum:\n"
            + "- user: PGUSER or USER env variable or OS username\n"
            + "- pass: PGPASSWORD env variable or runtime prompt\n"
            + "- host: PGHOST env variable or 'localhost'\n"
            + "- port: PGPORT env variable or '5432'\n"
            + "- db: PGDATABASE env variable or OS username\n"
            )

    parser.add_argument('-s', '--schema', nargs=1, dest='schema', metavar='SCHEMA', default='dstools',
                         help="Target schema for the database objects.")

    parser.add_argument('-v', '--verbose', dest='verbose',
                        action="store_true", help="Verbose mode.")

    parser.add_argument('-t', '--testcase', dest='testcase', default="",
                        help="Module names to test, comma separated. Effective only for install-check.")

    parser.add_argument('-d', '--tmpdir', dest='tmpdir', default='/tmp/',
                        help="Temporary directory location for installation log files.")

    args = parser.parse_args()
    global verbose, testcase, tmpdir
    verbose = args.verbose
    testcase = args.testcase

    try:
        tmpdir = tempfile.mkdtemp('', 'dstools.', args.tmpdir)
    except OSError, e:
        tmpdir = e.filename
        __error("cannot create temporary directory: '%s'." % tmpdir, True)

    '''Parse SCHEMA'''
    if len(args.schema[0]) > 1:
        schema = args.schema[0].lower()
    else:
        schema = args.schema.lower()

    '''Fetch connection params from the connection string'''
    connStr = "" if args.connstr is None else args.connstr[0]
    (c_user, c_pass, c_host, c_port, c_db) = parseConnectionStr(connStr)

    '''Read connection parameters off of Environment variables if it is not supplied in the input '''
    if(c_user is None):
        c_user = os.environ.get('PGUSER', getpass.getuser())
    if c_pass is None:
        c_pass = os.environ.get('PGPASSWORD', None)
    if  c_host is None:
        c_host = os.environ.get('PGHOST', 'localhost')
    if c_port is None:
        c_port = os.environ.get('PGPORT', '5432')
    if c_db is None:
        c_db = os.environ.get('PGDATABASE', c_user)

    '''Get password'''
    if c_pass is None:
        c_pass = getpass.getpass("Password for user %s: " % c_user)

    '''Set connection variables'''
    global con_args
    con_args['host'] = c_host + ':' + c_port
    con_args['database'] = c_db
    con_args['user'] = c_user
    con_args['password'] = c_pass

    global dbver
    dbver = __get_dbver()

    portdir = os.path.join(dstoolsdir, "ports", 'greenplum')
    supportedVersions = [dirItem for dirItem in os.listdir(portdir) if os.path.isdir(os.path.join(portdir, dirItem))
                             and re.match("^\d+\.\d+", dirItem)]
    if dbver is None:
       dbver = ".".join(map(str, max([map(int, versionStr.split('.')) for versionStr in supportedVersions])))
       __info("Could not parse version string reported by {DBMS}. Will "
              "default to newest supported version of {DBMS} "
              "({version}).".format(DBMS='greenplum', version=dbver), True)
    else:
       __info("Detected %s version %s." % ('greenplum', dbver),True)
       if not os.path.isdir(os.path.join(portdir, dbver)):
            __error("This version is not among the %s versions for which "
                    "DSTools support files have been installed (%s)." %
                   ('greenplum', ", ".join(supportedVersions)), True)


    global dstoolsdir_lib
    global dstoolsdir_conf

    if os.path.isfile(dstoolsdir + "/ports/greenplum" + "/" + dbver + "/lib/libdstools.so"):
        dstoolsdir_lib = dstoolsdir + "/ports/greenplum" + "/" + dbver + "/lib/libdstools.so"

    # Get the list of modules for this port
    global portspecs
    portspecs = configyml.get_modules(dstoolsdir_conf)

    # Run installation
    try:
        __plpy_check(py_min_ver)
        __db_install(schema, None, args.testcase)
    except:
        __error("DSTools installation failed.", True)


if(__name__=='__main__'):
    main()
