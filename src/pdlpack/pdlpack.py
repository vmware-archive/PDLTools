'''
Simple Python based installer of PDL Tools. In time this will involve to become
more complex
but perhaps not quite as complex as madpack :-)
Note: Most of this script has been copied from madpack.py. We've removed irrelevant portions from madpack to build pdlpack.
Srivatsan Ramanujam
<sramanujam@pivotal.io>
28 Jan 2014

Usage:
======
python pdlpack.py [-s schema_name] [-S SUgAR_schema_name] [-M MADlib_schema_name] -c <username>@<hostname>:<port>/<databasename>
'''

import os, sys, datetime, getpass, re, subprocess, tempfile, glob
import argparse, configyml

pdltoolsdir = None
pdltoolsdir_conf = None
rev = None
sugar_rev = None
this = None
py_min_ver = None
perl_min_ver = 5.008
perl_max_ver = 6.0
plr_min_ver = '2.13'
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
    global pdltoolsdir, pdltoolsdir_conf, rev, sugar_rev
    global this, con_args, py_min_ver
    global perl_min_ver,perl_max_ver
    global plr_min_ver
    checkPythonVersion()
    pdltoolsdir = os.path.abspath(os.path.dirname(os.path.realpath(__file__)) + "/..")
    pdltoolsdir_conf = pdltoolsdir+'/config'
    rev = configyml.get_version(pdltoolsdir_conf)
    sugar_rev = configyml.get_sugar_version(pdltoolsdir_conf)
    this = os.path.basename(sys.argv[0])    # name of this script
    sys.path.append(pdltoolsdir + "/pdlpack")

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

def __get_rev_string(rev):
    """
    Convert version string into valid schema name suffix
        @param rev version text
    """
    return re.sub(r'\.','_',rev)

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

def __run_sql_file(schema, sugar_schema, madlib_schema, dsdir_mod_py, module,
                   sqlfile, tmpfile, logfile, pre_sql):
    """Run SQL file
            @param schema name of the target schema
            @param sugar_schema name of SUgARlib schema
            @param madlib_schema name of MADlib schema
            @param dsdir_mod_py name of the module dir with Python code
            @param module  name of the module
            @param sqlfile name of the file to parse
            @param tmpfile name of the temp file to run
            @param logfile name of the log file (stdout)
            @param pre_sql optional SQL to run before executing the file
    """
    global rev
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
        # Find the pdlpack dir (platform specific or generic)
        if os.path.isdir(pdltoolsdir + "/ports/greenplum" + "/" + dbver + "/pdlpack"):
            pdltoolsdir_pdlpack = pdltoolsdir + "/ports/greenplum" + "/" + dbver + "/pdlpack"
        else:
            pdltoolsdir_pdlpack = pdltoolsdir + "/pdlpack"

        m4args = ['m4',
                  '-P',
                  '-DPDLTOOLS_SCHEMA=' + schema,
                  '-DSUGAR_SCHEMA=' + sugar_schema,
                  '-DMADLIB_SCHEMA=' + madlib_schema,
                  '-DPDLTOOLS_VERSION=' + rev,
                  '-DSUGAR_VERSION=' + sugar_rev,
                  '-DPLPYTHON_LIBDIR=' + dsdir_mod_py,
                  '-DMODULE_PATHNAME=' + pdltoolsdir_lib,
                  '-DMODULE_NAME=' + module,
                  '-I' + pdltoolsdir_pdlpack,
                  sqlfile]

        __info("> ... parsing: " + " ".join(m4args), verbose)

        subprocess.call(m4args, stdout=f)
        f.close()
    except:
        __error("Failed executing m4 on %s" % sqlfile, False)
        raise Exception

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
        @param py_min_ver min Python version to run PDL Tools
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
    __run_sql_query("DROP FUNCTION IF EXISTS plpy_version_for_pdltools();", False)
    __run_sql_query("""
        CREATE OR REPLACE FUNCTION plpy_version_for_pdltools()
        RETURNS TEXT AS
        $$
            import sys
            # return '.'.join(str(item) for item in sys.version_info[:3])
            return str(sys.version_info[:3]).replace(',','.').replace(' ','').replace(')','').replace('(','')
        $$
        LANGUAGE plpythonu;
    """, True)
    rv = __run_sql_query("SELECT plpy_version_for_pdltools() AS ver;", True)
    python = rv[0]['ver']
    py_cur_ver = [int(i) for i in python.split('.')]
    if py_cur_ver >= py_min_ver:
        __info("> PL/Python version: %s" % python, verbose)
    else:
        __error("PL/Python version too old: %s. You need %s or greater"
                % (python, '.'.join(str(i) for i in py_min_ver)), False)
        raise Exception

    __info("> PL/Python environment OK (version: %s)" % python, True)


def __plr_check(plr_min_ver):
    """
    Check pl/r existence and version
        @param plr_min_ver min PL/R version to run PDL Tools
    """

    __info("Testing PL/R environment...", True)

    # Check PL/R existence
    rv = __run_sql_query("SELECT count(*) AS CNT FROM pg_language "
                         "WHERE lanname = 'plr'", True)

    if int(rv[0]['cnt']) > 0:
        __info("> PL/R already installed", verbose)
    else:
        __info("> PL/R not installed", verbose)
        __info("> Creating language PL/R...", True)
        try:
            __run_sql_query("CREATE LANGUAGE plr;", True)
        except:
            __error('Cannot create language plr. Stopping installation...', False)
            raise Exception

    # Check PL/R version
    __run_sql_query("DROP FUNCTION IF EXISTS plr_version_for_pdltools();", False)
    __run_sql_query("""
        CREATE OR REPLACE FUNCTION plr_version_for_pdltools()
        RETURNS TEXT AS
        $$
             return (paste(R.version$major,R.version$minor,sep="."));
        $$
        LANGUAGE plr;
    """, True)
    rv = __run_sql_query("SELECT plr_version_for_pdltools() AS ver;", True)
    plr_cur_ver = rv[0]['ver']
    if plr_cur_ver >= plr_min_ver:
        __info("> PL/R version: %s" % plr_cur_ver, verbose)
    else:
        __error("PL/R version too old: {cur_ver}. You need {min_ver} or greater".format(
                                cur_ver=plr_cur_ver,
                                min_ver=plr_min_ver
                                ), 
                                False
                )
        raise Exception

    __info("> PL/R environment OK (version: %s)" % plr_cur_ver, True)


def __plperl_check(perl_min_ver,perl_max_ver):
    """
    Check pl/perl existence and version
        @param perl_min_ver min Perl version to run PDL Tools
        @param perl_max_ver max Perl version to run PDL Tools
    """

    __info("Testing PL/Perl environment...", True)

    # Check PL/Perl existence
    rv = __run_sql_query("SELECT count(*) AS CNT FROM pg_language "
                         "WHERE lanname = 'plperl'", True)

    if int(rv[0]['cnt']) > 0:
        __info("> PL/Perl already installed", verbose)
    else:
        __info("> PL/Perl not installed", verbose)
        __info("> Creating language PL/Perl...", True)
        try:
            __run_sql_query("CREATE LANGUAGE plperl;", True)
        except:
            __error('Cannot create language plperl. Stopping installation...', False)
            raise Exception

    # Check PL/Perl version
    __run_sql_query("DROP FUNCTION IF EXISTS plperl_version_for_pdltools();", False)
    __run_sql_query("""
        CREATE OR REPLACE FUNCTION plperl_version_for_pdltools()
        RETURNS TEXT STABLE AS
        $$
          $];
        $$
        LANGUAGE plperl;
    """, True)
    rv = __run_sql_query("SELECT plperl_version_for_pdltools() AS ver;", True)
    perl_cur_ver = float(rv[0]['ver'])
    if perl_cur_ver <= perl_min_ver:
        __error("PL/Perl version too old: %s. You need %s or greater"
                % (str(perl_cur_ver),str(perl_min_ver)), False)
        raise Exception
    elif perl_cur_ver >= perl_max_ver:
        __error("PL/Perl version too new: %s. You need %s or less"
                % (str(perl_cur_ver),str(perl_max_ver)), False)
        raise Exception
    else:
        __info("> PL/Perl version: %s" % str(perl_cur_ver), verbose)

    __info("> PL/Perl environment OK (version: %s)" % str(perl_cur_ver), True)

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

def __print_revs(rev, dbrev, sugar_dbrev, con_args, schema, sugar_schema):
    """
    Print version information
        @param rev OS-level PDL Tools version
        @param dbrev PDL Tools version installed in DB
        @param sugar_dbrev SUgAR version installed in DB
        @param con_args database connection arguments
        @param schema PDL Tools schema name
    """
    __info("PDL Tools version    = %s (%s)" % (rev, sys.argv[0]), True)
    __info("SUgAR version    = %s" % sugar_rev, True)
    if con_args:
        try:
            __info("PDL Tools database version = %s (host=%s, db=%s, schema=%s)"
                   % (dbrev, con_args['host'], con_args['database'], schema), True)
        except:
            __info("PDL Tools database version = [Unknown] (host=%s, db=%s, schema=%s)"
                   % (con_args['host'], con_args['database'], schema), True)
        try:
            __info("SUgAR database version = %s (host=%s, db=%s, schema=%s)"
                   % (sugar_dbrev, con_args['host'], con_args['database'], schema), True)
        except:
            __info("SUgAR database version = [Unknown] (host=%s, db=%s, schema=%s)"
                   % (con_args['host'], con_args['database'], schema), True)
    return


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
        @param schema name of the schema to create
    """

    __info("> Creating %s schema" % schema.upper(), True)
    try:
        __run_sql_query("CREATE SCHEMA %s;" % schema, True)
    except:
        __Error('Cannot create new schema. Rolling back installation...', False)
        raise Exception

def __db_grant_usage(schema):
    """
    Grant usage
        @param schema name of the schema to grant permissions to
    """

    __info("> Granting usage on %s schema" % schema.upper(), True)
    try:
        __run_sql_query("GRANT USAGE ON SCHEMA %s TO PUBLIC;" % schema, True)
    except:
        __Error('Cannot grant permissions on schema. Rolling back installation...', False)
        raise Exception

def __db_update_migration_history(schema,backup_schema,curr_rev,
                                  old_sugar=False):
    """
    Create MigrationTable
        @param schema Name of the target schema
        @param backup_schema Name of backup schema
    """
    # Create MigrationHistory table
    try:
        __info("> Creating %s.MigrationHistory table" % schema.upper(), True)
        sql = """CREATE TABLE %s.migrationhistory
               (id serial, version varchar(255),
                applied timestamp default current_timestamp);""" % schema
        __run_sql_query(sql, True)
    except:
        __error("Cannot create MigrationHistory table in schema %s."
                % schema.upper(), False)
        raise Exception

    # Copy MigrationHistory table for record keeping purposes
    if old_sugar:
      __info("> Old version of SUgAR does not have a MigrationHistory table.",verbose)
      try:
        sql = """INSERT INTO %s.migrationhistory (version,applied)
                 VALUES ('0.4',NULL);""" % schema
        __run_sql_query(sql,True)
      except:
        __error("Cannot insert data into MigrationHistory table.", False)
        raise Exception
    elif backup_schema:
        try:
            __info("> Saving data from %s.MigrationHistory table" % backup_schema.upper(), True)
            sql = """INSERT INTO %s.migrationhistory (version, applied)
                   SELECT version, applied FROM %s.migrationhistory
                   ORDER BY id;""" % (schema, backup_schema)
            __run_sql_query(sql, True)
        except:
              __error("Cannot copy MigrationHistory table", False)
              raise Exception

    # Stamp the DB installation
    try:
        __info("> Writing version info in %s.MigrationHistory table"
               % schema.upper(), True)
        __run_sql_query("INSERT INTO %s.migrationhistory(version) "
                        "VALUES('%s')" % (schema, curr_rev), True)
    except:
        __error("Cannot insert data into %s.migrationhistory table"
                % schema.upper(), False)
        raise Exception

def __db_create_objects(schema, sugar_schema, madlib_schema,
                        backup_schema, backup_sugar_schema,old_sugar):
    """
    Create PDL Tools DB objects in the schema
        @param schema Name of the target PDL Tools schema
        @param sugar_schema Name of the target SUgARlib schema
        @param backup_schema Name of backup schema of latest PDL Tools
        @param backup_sugar_schema Name of backup schema of latest SUgAR
    """
    __info("> Updating PDL Tools migration history.",True)
    __db_update_migration_history(schema,backup_schema,rev)
    __info("> Updating SUgAR migration history.",True)
    __db_update_migration_history(sugar_schema,backup_sugar_schema,
                                  sugar_rev,old_sugar)


    __info("> Creating objects for modules:", True)

#     caseset = (set([test.strip() for test in testcase.split(',')])
#                if testcase != "" else set())
# 
#     modset = {}
#     for case in caseset:
#         if case.find('/') > -1:
#             [mod, algo] = case.split('/')
#             if mod not in modset:
#                 modset[mod] = []
#             if algo not in modset[mod]:
#                 modset[mod].append(algo)
#         else:
#             modset[case] = []

    # Loop through all modules/modules
    ## portspecs is a global variable

    for moduleinfo in portspecs['modules']:

        # Get the module name
        module = moduleinfo['name']

        # Skip if doesn't meet specified modules
#         if modset is not None and len(modset) > 0 and module not in modset:
#             continue

        __info("> - %s" % module, True)
 
        # Find the Python module dir (platform specific or generic)
        if os.path.isdir(pdltoolsdir + "/ports/greenplum" + "/" + dbver + "/modules/" + module):
            dsdir_mod_py = pdltoolsdir + "/ports/greenplum" + "/" + dbver + "/modules"
        else:
            dsdir_mod_py = pdltoolsdir + "/modules"

        # Find the SQL module dir (platform specific or generic)
        if os.path.isdir(pdltoolsdir + "/ports/greenplum" + "/modules/" + module):
            dsdir_mod_sql = pdltoolsdir + "/ports/greenplum" + "/modules"
        elif os.path.isdir(pdltoolsdir + "/modules/" + module):
            dsdir_mod_sql = pdltoolsdir + "/modules"
        else:
            # This was a platform-specific module, for which no default exists.
            # We can just skip this module.
            continue

        # Make a temp dir for log files
        cur_tmpdir = tmpdir + "/" + module
        __make_dir(cur_tmpdir)

        # Loop through all SQL files for this module
        mask = dsdir_mod_sql + '/' + module + '/*.sql_in'
        sql_files = glob.glob(mask)

        if not sql_files:
            __error("No files found in: %s" % mask, True)

        # Execute all SQL files for the module
        for sqlfile in sql_files:
            algoname = os.path.basename(sqlfile).split('.')[0]

#             if module in modset and len(modset[module]) > 0 and algoname not in modset[module]:
#                 continue

             # Set file names
            tmpfile = cur_tmpdir + '/' + os.path.basename(sqlfile) + '.tmp'
            logfile = cur_tmpdir + '/' + os.path.basename(sqlfile) + '.log'

            retval = __run_sql_file(schema, sugar_schema, madlib_schema,
                                    dsdir_mod_py, module,
                                    sqlfile, tmpfile, logfile, None)
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

## # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# Read version from MigrationHistory table in database
# @param schema schema-name in which to look for table
## # # # # # # # # # # # # # # # # # # # # # # # # # # # #
def __get_installed_ver(schema):
    try:
        row = __run_sql_query("""SELECT count(*) AS cnt FROM pg_tables
            WHERE schemaname='%s' AND tablename='migrationhistory'""" % (schema), True)
        if int(row[0]['cnt']) > 0:
            row = __run_sql_query("""SELECT version FROM %s.migrationhistory
                WHERE applied IS NOT NULL
                ORDER BY applied DESC LIMIT 1""" % schema, True)
            if row:
                return row[0]['version']
    except:
        pass

    return None

## # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# Rename schema
# @param from_schema name of the schema to rename
# @param to_schema new name for the schema
## # # # # # # # # # # # # # # # # # # # # # # # # # # # #
def __db_rename_schema(from_schema, to_schema):

    __info("> Renaming schema %s to %s" % (from_schema.upper(), to_schema.upper()), True)
    try:
        __run_sql_query("ALTER SCHEMA %s RENAME TO %s;" % (from_schema, to_schema), True)
    except:
        __error('Cannot rename schema. Stopping installation...', False)
        raise Exception

def __cmp_versions(ver_a,ver_b):
  a_list=[int(x) for x in ver_a.split('.')]
  b_list=[int(x) for x in ver_b.split('.')]
  return cmp(a_list,b_list)

def __check_prev_install(schema,current_rev,is_sugar=False):
    # is_newer can take the following values:
    # -1 -- current version is older than db version
    # 0 -- current version is the same as db version
    # 1 -- current version is newer than db version
    # 2 -- schema for current version exists, but library not installed
    # 3 -- current installation is for an old version of SUgAR that did not
    #      have a migration table and is older than the current version.
    backup_schema = None
    is_newer = 1

    schema_writable = None
    # Test if schema is writable
    try:
        __run_sql_query("CREATE TABLE %s.__pdltools_test_table (A INT);" % schema, False)
        __run_sql_query("DROP TABLE %s.__pdltools_test_table;" % schema, False)
        schema_writable = True
    except:
        schema_writable = False

    ##
    # CASE #1: Target schema exists with library objects:
    ##
    rc=0
    if schema_writable:
      dbrev=__get_installed_ver(schema)
      if is_sugar and dbrev==None:
        try:
          rc=__run_sql_query("select count(*) AS cnt from pg_catalog.pg_proc p, pg_catalog.pg_namespace ns where ns.nspname='%s' and pronamespace=ns.oid and p.proname='sugar_version';" % schema.lower(),True)[0]['cnt']
        except:
          rc=0
        if rc>0:
          dbrev='0.4' # SUgAR's v0.4 came without a migration table.
      if dbrev!=None:
        dbrev_string=__get_rev_string(dbrev)
        backup_schema = schema + '_v' + dbrev_string
        is_newer = __cmp_versions(current_rev,dbrev)
        if is_newer==1:
          if rc>0:
            is_newer=3
          __info("***************************************************************************", True)
          __info("* Schema %s already exists and includes library objects." % schema.upper(), True)
          __info("* Installed version is %s." % dbrev, True)
          __info("* Installer will rename it to %s and will upgrade to version %s." % (backup_schema.upper(),current_rev), True)
          __info("***************************************************************************", True)
        elif is_newer==0:
          __info("> Schema %s already exists and includes latst version of the library (%s)." % (schema.upper(),dbrev), verbose)
          __info("> Installer will rename it temporarily to %s, will reinstall," % backup_schema.upper(),verbose)
          __info("> and will remove old copy upon successfully re-install.", verbose)
        else:
          __info("> Schema %s already exists and is at newer version." % schema.upper(), True)
          __info("> Installed version is %s." % dbrev, True)
          __info("> Installer version is %s." % current_rev, True)
          __info("> Halting installation.",True)
          __info("Before retrying: drop %s schema OR install into a different schema." % schema.upper(), True)
        return (backup_schema,is_newer)

    ##
    # CASE #2: Target schema exists w/o library objects:
    ##
      else:
        __info("> Schema %s already exists but does not include library objects." % schema.upper(), True)
        __info("> Installation stopped.", True)
        __info("> Before retrying: drop %s schema OR install into a different schema." % schema.upper(), True)
        is_newer=2
        return (backup_schema,is_newer)

    ##
    # CASE #3: Target schema does not exist:
    ##
    else:
      __info("> Schema %s does not exist." % schema.upper(), verbose)

    return (backup_schema,is_newer)

def __db_drop_backup_schema(backup_schema,is_newer):
  if (is_newer==1 or is_newer==3) and backup_schema!=None:
    __info("Keep old schema %s? [Y/N]" % backup_schema.upper(), True)
    go = raw_input('>>> ').upper()
    while go =='' or go[0] not in 'YN':
        go = raw_input('Yes or No >>> ').upper()
    if go[0] == 'Y':
        return
  if backup_schema!=None:
    __info("> Dropping old schema %s." % backup_schema.upper(),verbose)
    try:
      __run_sql_query("DROP SCHEMA %s CASCADE;" % backup_schema, True)
    except:
      __info("Unable to drop schema %s." % backup_schema.upper(),True)

def __db_install(schema, sugar_schema, madlib_schema):
    """
    Install PDL Tools
        @param schema pdltools schema name
        @param sugar_schema name of SUgARlib schema
        @param madlib_schema name of MADlib schema
    """
    __info("Installing pdltools into %s schema and SUgAR into %s schema..."
           % (schema.upper(),sugar_schema.upper()), True)

    __info("Looking for MADlib installation in %s schema..."
           % (madlib_schema.upper()), True)

    (backup_schema,pdltools_newer)=__check_prev_install(schema,rev)
    if pdltools_newer==-1 or pdltools_newer==2:
      return

    (backup_sugar_schema,sugar_newer)=__check_prev_install(sugar_schema,sugar_rev,True)
    if sugar_newer==-1 or sugar_newer==2:
      return

    if pdltools_newer==0 and sugar_newer==0:
      __info("**********************************************************************",True)
      __info("* NOTE:",True)
      __info("* Both PDL Tools and SUgAR installations are already at latest version.",True)
      __info("**********************************************************************",True)
  
    if backup_schema or backup_sugar_schema or (pdltools_newer==0 and suger_newer==0):
          __info("Would you like to continue?", True)
          go = raw_input('>>> ').upper()
          while go =='' or go[0] not in 'YN':
              go = raw_input('Yes or No >>> ').upper()
          if go[0] == 'N':
              __info('Installation stopped.', True)
              return
  
    if backup_schema:
          # Rename PDL Tools schema
          __db_rename_schema(schema, backup_schema)
  
    if backup_sugar_schema:
          # Rename SUgAR schema
          __db_rename_schema(sugar_schema, backup_sugar_schema)

    # Create PDL Tools schema
    try:
        __db_create_schema(schema)
    except:
        __db_rollback(schema, backup_schema)
        raise Exception

    # Create SUgARlib schema
    try:
        __db_create_schema(sugar_schema)
    except:
        __db_rollback(sugar_schema, backup_sugar_schema)
        __db_rollback(schema, backup_schema)
        raise Exception

    # Granting Usage on Schemas
    try:
        __db_grant_usage(schema)
        __db_grant_usage(sugar_schema)
    except:
        __db_rollback(sugar_schema, backup_sugar_schema)
        __db_rollback(schema, backup_schema)
        raise Exception

    # Create pdltools objects
    try:
        __db_create_objects(schema, sugar_schema, madlib_schema,
                            backup_schema, backup_sugar_schema,sugar_newer==3)
    except:
        __db_rollback(sugar_schema, backup_sugar_schema)
        __db_rollback(schema, backup_schema)
        raise Exception

    __info("PDL Tools %s installed successfully in %s schema." % (rev, schema.upper()), True)
    __db_drop_backup_schema(backup_schema,pdltools_newer)

    __info("SUgAR %s installed successfully in %s schema." % (sugar_rev, sugar_schema.upper()), True)
    __db_drop_backup_schema(backup_sugar_schema,sugar_newer)

    __info("Installation completed successfully.",True)

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
        Fetch arguments and prepare installation of pdltools in target DB
    '''
    parser = argparse.ArgumentParser(
                description='PDL Tools package manager (' + rev + ')',
                argument_default=False,
                formatter_class=argparse.RawTextHelpFormatter,
                epilog="""Example:

  $ pdlpack install -s pdltools -S SUgARlib -M MADlib -c gpadmin@mdw:5432/testdb

  This will install PDL Tools objects into a Greenplum database called TESTDB
  running on server MDW:5432. Installer will try to login as GPADMIN
  and will prompt for password. The target schema will be "SUgARlib" for
  the SUgAR library and "pdltools" for all else. Functionality borrowed from
  MADlib will assume that MADlib is (or will be) installed in the "MADlib"
  schema.
""")

    parser.add_argument(
        'command', metavar='COMMAND', nargs=1,
        choices=['install', 'install-check'],
        help = "One of the following options:\n"
            + "  install        : run sql scripts to load into DB\n"
            + "  install-check  : Run test scripts"
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

    parser.add_argument('-s', '--schema', nargs=1, dest='schema', metavar='SCHEMA', default='pdltools',
                         help="Target schema for the database objects.")

    parser.add_argument('-S', '--sugar_schema', nargs=1, dest='sugar_schema', metavar='SUGAR_SCHEMA', default='SUgARlib',
                         help="Target schema for the SUgAR objects.")

    parser.add_argument('-M', '--madlib_schema', nargs=1, dest='madlib_schema', metavar='MADLIB_SCHEMA', default='MADlib',
                         help="Schema to search for MADlib objects.")

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
        tmpdir = tempfile.mkdtemp('', 'pdltools.', args.tmpdir)
    except OSError, e:
        tmpdir = e.filename
        __error("cannot create temporary directory: '%s'." % tmpdir, True)

    '''Parse SCHEMA'''
    if len(args.schema[0]) > 1:
        schema = args.schema[0].lower()
    else:
        schema = args.schema.lower()

    '''Parse SUGAR_SCHEMA'''
    if len(args.sugar_schema[0]) > 1:
        sugar_schema = args.sugar_schema[0].lower()
    else:
        sugar_schema = args.sugar_schema.lower()

    '''Parse MADLIB_SCHEMA'''
    if len(args.madlib_schema[0]) > 1:
        madlib_schema = args.madlib_schema[0].lower()
    else:
        madlib_schema = args.madlib_schema.lower()

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

    portdir = os.path.join(pdltoolsdir, "ports", 'greenplum')
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
                    "PDL Tools support files have been installed (%s)." %
                   ('greenplum', ", ".join(supportedVersions)), True)

    global pdltoolsdir_lib
    global pdltoolsdir_conf

    if os.path.isfile(pdltoolsdir + "/ports/greenplum" + "/" + dbver + "/lib/libpdltools.so"):
        pdltoolsdir_lib = pdltoolsdir + "/ports/greenplum" + "/" + dbver + "/lib/libpdltools.so"

    # Get the list of modules for this port
    global portspecs
    portspecs = configyml.get_modules(pdltoolsdir_conf)

    if(args.command[0]=='install'):
        install(py_min_ver, perl_min_ver, perl_max_ver, plr_min_ver, schema,
                sugar_schema, madlib_schema)
    elif(args.command[0]=='install-check'):
        install_check(schema, sugar_schema, madlib_schema, args)

def install(py_min_ver, perl_min_ver, perl_max_ver, plr_min_ver, schema,
            sugar_schema, madlib_schema):
    '''
        Install pdlpack
    '''
    # Run installation
    try:
        __plpy_check(py_min_ver)
        __plperl_check(perl_min_ver,perl_max_ver)
        #__plr_check(plr_min_ver)
        __db_install(schema, sugar_schema, madlib_schema)
    except:
        __error("PDL Tools installation failed.", True)


def install_check(schema, sugar_schema, madlib_schema, args):
	'''
	Run install checks
	'''
	global con_args, portspecs
	# 0) First check if PDL Tools schema exists, if not we'll exit (install-check should only be called post installation of pdltools)
	pdltools_schema_exists = __run_sql_query("select schema_name from information_schema.schemata where schema_name='{pdltools_schema}';".format(pdltools_schema=schema), False)
	if(not pdltools_schema_exists):
	    __info("{pdltools_schema} schema does not exist. Please run install-check after installing PDL Tools. Install-check stopped.".format(pdltools_schema=schema), True)
            return
	# Now check if SUgARlib schema exists.
	sugar_schema_exists = __run_sql_query("select schema_name from information_schema.schemata where schema_name='{sugarlib_schema}';".format(sugarlib_schema=sugar_schema), False)
	if(not sugar_schema_exists):
	    __info("{sugarlib_schema} schema does not exist. Please run install-check after installing PDL Tools. Install-check stopped.".format(sugarlib_schema=sugar_schema), True)
            return

	# Create install-check user
	test_user = 'pdltools_installcheck'
	try:
	    __run_sql_query("DROP USER IF EXISTS %s;" % (test_user), False)
	except:
	    __run_sql_query("DROP OWNED BY %s CASCADE;" % (test_user), True)
	    __run_sql_query("DROP USER IF EXISTS %s;" % (test_user), True)
	__run_sql_query("CREATE USER %s;" % (test_user), True)
	__run_sql_query("GRANT ALL ON SCHEMA %s TO %s;" %(schema, test_user), True)
	__run_sql_query("GRANT ALL ON SCHEMA %s TO %s;" %(sugar_schema, test_user), True)

	# 2) Run test SQLs
	__info("> Running test scripts for:", verbose)

	caseset = (set([test.strip() for test in args.testcase.split(',')])
		   if args.testcase != "" else set())

	# Loop through all modules
	for moduleinfo in portspecs['modules']:

	    # Get module name
	    module = moduleinfo['name']

	    # Skip if doesn't meet specified modules
	    if len(caseset) > 0 and module not in caseset:
		continue

	    __info("> - %s" % module, verbose)

	    # Make a temp dir for this module (if doesn't exist)
	    cur_tmpdir = tmpdir + '/' + module + '/test'  # tmpdir is a global variable
	    __make_dir(cur_tmpdir)

	    # Find the Python module dir (platform specific or generic)
	    if os.path.isdir(pdltoolsdir + "/ports/greenplum" + "/" + dbver + "/modules/" + module):
		dsdir_mod_py = pdltoolsdir + "/ports/greenplum" + "/" + dbver + "/modules"
	    else:
		dsdir_mod_py = pdltoolsdir + "/modules"

	    # Find the SQL module dir (platform specific or generic)
	    if os.path.isdir(pdltoolsdir + "/ports/greenplum" + "/modules/" + module):
		dsdir_mod_sql = pdltoolsdir + "/ports/greenplum" + "/modules"
	    else:
		dsdir_mod_sql = pdltoolsdir + "/modules"

	    # Prepare test schema
	    test_schema = "pdltools_installcheck_%s" % (module)
	    __run_sql_query("DROP SCHEMA IF EXISTS %s CASCADE; CREATE SCHEMA %s;"
			    % (test_schema, test_schema), True)
	    __run_sql_query("GRANT ALL ON SCHEMA %s TO %s;"
			    % (test_schema, test_user), True)

	    # Switch to test user and prepare the search_path
	    pre_sql = '-- Switch to test user:\n' \
		      'SET ROLE %s;\n' \
		      '-- Set SEARCH_PATH for install-check:\n' \
		      'SET search_path=%s,%s,%s;\n' \
		      % (test_user, test_schema, schema, sugar_schema)

	    # Loop through all test SQL files for this module
	    sql_files = dsdir_mod_sql + '/' + module + '/test/*.sql_in'
	    for sqlfile in sorted(glob.glob(sql_files), reverse=True):
		# Set file names
		tmpfile = cur_tmpdir + '/' + os.path.basename(sqlfile) + '.tmp'
		logfile = cur_tmpdir + '/' + os.path.basename(sqlfile) + '.log'

		# If there is no problem with the SQL file
		milliseconds = 0

		# Run the SQL
		run_start = datetime.datetime.now()
		retval = __run_sql_file(schema, sugar_schema, madlib_schema,
                                        dsdir_mod_py, module,
					sqlfile, tmpfile, logfile, pre_sql)
		# Runtime evaluation
		run_end = datetime.datetime.now()
		milliseconds = round((run_end - run_start).seconds * 1000 +
				     (run_end - run_start).microseconds / 1000)

		# Check the exit status
		if retval != 0:
		    __error("Failed executing %s" % tmpfile, False)
		    __error("Check the log at %s" % logfile, False)
		    result = 'FAIL'
		    keeplogs = True
		# Since every single statement in the test file gets logged,
		# an empty log file indicates an empty or a failed test
		elif os.path.isfile(logfile) and os.path.getsize(logfile) > 0:
		    result = 'PASS'
		# Otherwise
		else:
		    result = 'ERROR'

		# Spit the line
		print "TEST CASE RESULT|Module: " + module + \
		    "|" + os.path.basename(sqlfile) + "|" + result + \
		    "|Time: %d milliseconds" % (milliseconds)

	    # Cleanup test schema for the module
	    __run_sql_query("DROP SCHEMA IF EXISTS %s CASCADE;" % (test_schema), True)

	# Drop install-check user
	__run_sql_query("DROP OWNED BY %s CASCADE;" % (test_user), True)
	__run_sql_query("DROP USER %s;" % (test_user), True)


if(__name__=='__main__'):
    main()
