'''
Simple Python based installer of PDL Tools. In time this will involve to become
more complex
but perhaps not quite as complex as madpack :-)
Note: Most of this script has been copied from madpack.py. We've removed irrelevant portions from madpack to build pdlpack.
Srivatsan Ramanujam
<sramanujam@pivotal.io>
28 Jan 2014

Major rewrite by
Michael Brand
<mbrand@pivotal.io>
13 Feb 2015

Usage:
======
python pdlpack.py [-s schema_name] -p platform [-S SUgAR_schema_name] [-M MADlib_schema_name] -c <username>@<hostname>:<port>/<databasename>

'platform' should be either 'greenplum' or 'hawq'.
'''

import os, sys, datetime, getpass, re, subprocess, tempfile, glob
import argparse, configyml, yaml

platform = 'greenplum'
pdltoolsdir = None
pdltoolsdir_conf = None
pdltoolsdir_lib = None
rev = None
portid_list = []
sugar_rev = None
this = None
py_min_ver = None
perl_min_ver = 5.008
perl_max_ver = 6.0
plr_min_ver = '2.13'
con_args={}
verbose=False
testcase=None
tmpdir_arg=None

class session_manager:
  def __init__(self,schema,platform,sugar_schema,madlib_schema,pre_sql=None):
    self.name=None
    self.schema=schema
    self.platform=platform
    self.sugar_schema=sugar_schema
    self.madlib_schema=madlib_schema
    self.pre_sql=pre_sql
    self.session_content=[]
    self.dsdir_mod_py_re=re.compile("PLPYTHON_LIBDIR")
    self.module_re=re.compile("MODULE_NAME")
    self.logfile=''
    try:
      self.tmpdir = tempfile.mkdtemp('', 'pdltools.', tmpdir_arg)
    except OSError, e:
      self.tmpdir = e.filename
      _error("cannot create temporary directory: '%s'." % self.tmpdir, False)
      raise
  def logname(self):
    return self.logfile
  def set_pre_sql(self,pre_sql):
    self.pre_sql=pre_sql
  def begin(self,name):
    if self.name!=None:
      _error("Unexpected: BEGIN while already in transaction.", False)
      raise Exception
    self.name=name
    self.session_content=["BEGIN;"]
    if self.pre_sql:
      self.session_content.append(self.pre_sql+";\n")
  def rollback(self):
    self.session_content=[]
    self.name=None
  def commit(self):
    global rev, sugar_rev, pdltoolsdir_lib
    if self.name == None:
      _error("Unexpected: COMMIT instruction issued while not in transaction.",
             False)
      raise Exception
    self.session_content.append("COMMIT;")
    sqlfile = self.tmpdir + '/' + self.name + '.sql_in'
    tmpfile = self.tmpdir + '/' + self.name + '.tmp'
    self.logfile = self.tmpdir + '/' + self.name + '.log'
    try:
      sqlf = open(sqlfile, 'w')
    except:
      _error("Unable to open "+sqlfile+" for writing.", False)
      raise
    sqlf.write('\n'.join(self.session_content))
    sqlf.close()
    self.name=None
    self.session_content=[]

    # Prepare the file using M4
    try:
        f = open(tmpfile, 'w')

        # Find the pdlpack dir (platform specific or generic)
        if os.path.isdir(pdltoolsdir + "/ports/{platform}".format(platform=self.platform) + "/" + dbver + "/pdlpack"):
            pdltoolsdir_pdlpack = pdltoolsdir + "/ports/{platform}".format(platform=self.platform) + "/" + dbver + "/pdlpack"
        else:
            pdltoolsdir_pdlpack = pdltoolsdir + "/pdlpack"

        m4args = ['m4',
                  '-P',
                  '-DPDLTOOLS_SCHEMA=' + self.schema,
                  '-DSUGAR_SCHEMA=' + self.sugar_schema,
                  '-DMADLIB_SCHEMA=' + self.madlib_schema,
                  '-DPDLTOOLS_VERSION=' + rev,
                  '-DSUGAR_VERSION=' + sugar_rev,
                  '-DMODULE_PATHNAME=' + pdltoolsdir_lib,
                  '-I' + pdltoolsdir_pdlpack,
                  sqlfile]

        _info("> ... parsing: " + " ".join(m4args), verbose)

        subprocess.call(m4args, stdout=f)
        f.close()
    except:
        _error("Failed executing m4 on %s" % sqlfile, False)
        raise Exception

    # Run the SQL using DB command-line utility
    sqlcmd = 'psql'
    # Test the DB cmd line utility
    std, err = subprocess.Popen(['which', sqlcmd], stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE).communicate()
    if not std:
        _error("Command not found: %s" % sqlcmd, True)

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
        log = open(self.logfile, 'w')
    except:
        _error("Cannot create log file: %s" % self.logfile, False)
        raise Exception

    # Run the SQL
    try:
        _info("> ... executing " + tmpfile, verbose)
        retval = subprocess.call(runcmd, env=runenv, stdout=log, stderr=log)
    except:
        _error("Failed executing %s" % tmpfile, False)
        raise Exception
    finally:
        log.close()

    if retval!=0:
      _error("Failed executing %s" % tmpfile, False)
      _error("Check the log at %s" % self.logfile, False)
    return retval

  def exec_query(self,sql,show_error):
    if self.name==None:
      return _raw_run_sql_query(sql,show_error)
    else:
      self.session_content.append(sql+";\n")
      return []
  def exec_file(self, dsdir_mod_py, module, sqlfile, subdir=None):
    if self.name==None:
      if subdir==None:
        tmpfile = self.tmpdir + '/' + os.path.basename(sqlfile) + '.tmp'
        self.logfile = self.tmpdir + '/' + os.path.basename(sqlfile) + '.log'
      else:
        cur_tmpdir = self.tmpdir + "/" + subdir
        _make_dir(cur_tmpdir)
        tmpfile = cur_tmpdir + '/' + os.path.basename(sqlfile) + '.tmp'
        self.logfile = cur_tmpdir + '/' + os.path.basename(sqlfile) + '.log'
      retval=_raw_run_sql_file(self.schema, self.platform, self.sugar_schema,
        self.madlib_schema, dsdir_mod_py, module, sqlfile, tmpfile,
        self.logfile, self.pre_sql)
      if retval!=0:
        _error("Failed executing %s" % tmpfile, False)
        _error("Check the log at %s" % self.logfile, False)
      return retval
    else:
      for l in open(sqlfile).readlines():
        self.session_content.append(
          self.dsdir_mod_py_re.sub(dsdir_mod_py,
            self.module_re.sub(module,l.rstrip('\n'))))
      self.session_content.append(";\n")
      return 0
      
  def __del__(self):
    if self.name!=None:
      self.rollback()

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
    global portid_list
    checkPythonVersion()
    pdltoolsdir = os.path.abspath(os.path.dirname(os.path.realpath(__file__)) + "/..")
    pdltoolsdir_conf = pdltoolsdir+'/config'
    ports = configyml.get_ports(pdltoolsdir_conf)
    for p in ports:
        portid_list.append(p)

    rev = configyml.get_version(pdltoolsdir_conf)
    sugar_rev = configyml.get_sugar_version(pdltoolsdir_conf)
    this = os.path.basename(sys.argv[0])    # name of this script
    sys.path.append(pdltoolsdir + "/pdlpack")

init()


def _get_rev_num(rev):
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

def _get_rev_string(rev):
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

def _raw_run_sql_query(sql, show_error):
	"""
	Runs a SQL query on the target platform DB
	using the default command-line utility.
	Very limited:
	  - no text output with "new line" characters allowed
	     @param sql query text to execute
	     @param show_error displays the SQL error msg
	"""
	sqlcmd = 'psql'
	delimiter = '|'

	# Test the DB cmd line utility
	std, err = subprocess.Popen(['which', sqlcmd], stdout=subprocess.PIPE,
		                    stderr=subprocess.PIPE).communicate()

	if std == '':
	    _error("Command not found: %s" % sqlcmd, True)

	# Run the query
	global con_args
	runcmd = [sqlcmd,
		  '-h', con_args['host'].split(':')[0],
		  '-d', con_args['database'],
		  '-U', con_args['user'],
		  '-F', delimiter,
                  '-x',
		  '-Ac', "set CLIENT_MIN_MESSAGES=error; " + sql]
	runenv = os.environ
	runenv["PGPASSWORD"] = con_args['password']
	runenv["PGOPTIONS"] = '-c search_path=public'
	std, err = subprocess.Popen(runcmd, env=runenv, stdout=subprocess.PIPE,
		                    stderr=subprocess.PIPE).communicate()

	if err:
	    if show_error:
		_error("SQL command failed: \nSQL: %s \n%s" % (sql, err), False)
	    raise Exception

	# Convert the delimited output into a dictionary
	results = []  # list of rows
	row = {}
	for line in std.splitlines():
		if len(line)==0:
			if len(row)!=0:
				results.append(row)
				row={}
		else:
			val = line.split(delimiter,1)
			if len(val)==2:
				row[val[0]] = val[1]

	if len(row)!=0:
		results.append(row)
	return results

def _raw_run_sql_file(schema, platform, sugar_schema, madlib_schema, dsdir_mod_py, module,
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
    global rev, pdltoolsdir_lib
    # Check if the SQL file exists
    if not os.path.isfile(sqlfile):
        _error("Missing module SQL file (%s)" % sqlfile, False)
        raise Exception

    # Prepare the file using M4
    try:
        f = open(tmpfile, 'w')

        # Add the before SQL
        if pre_sql:
            f.writelines([pre_sql, '\n\n'])
            f.flush()
        # Find the pdlpack dir (platform specific or generic)
        if os.path.isdir(pdltoolsdir + "/ports/{platform}".format(platform=platform) + "/" + dbver + "/pdlpack"):
            pdltoolsdir_pdlpack = pdltoolsdir + "/ports/{platform}".format(platform=platform) + "/" + dbver + "/pdlpack"
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

        _info("> ... parsing: " + " ".join(m4args), verbose)

        subprocess.call(m4args, stdout=f)
        f.close()
    except:
        _error("Failed executing m4 on %s" % sqlfile, False)
        raise Exception

    # Run the SQL using DB command-line utility
    sqlcmd = 'psql'
    # Test the DB cmd line utility
    std, err = subprocess.Popen(['which', sqlcmd], stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE).communicate()
    if not std:
        _error("Command not found: %s" % sqlcmd, True)

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
        _error("Cannot create log file: %s" % logfile, False)
        raise Exception

    # Run the SQL
    try:
        _info("> ... executing " + tmpfile, verbose)
        retval = subprocess.call(runcmd, env=runenv, stdout=log, stderr=log)
    except:
        _error("Failed executing %s" % tmpfile, False)
        raise Exception
    finally:
        log.close()

    return retval


def _plpy_check(py_min_ver):
    """
    Check pl/python existence and version
        @param py_min_ver min Python version to run PDL Tools
    """

    _info("Testing PL/Python environment...", True)

    # Check PL/Python existence
    rv = _raw_run_sql_query("SELECT count(*) AS CNT FROM pg_language "
                         "WHERE lanname = 'plpythonu'", True)

    if int(rv[0]['cnt']) > 0:
        _info("> PL/Python already installed", verbose)
    else:
        _info("> PL/Python not installed", verbose)
        _info("> Creating language PL/Python...", True)
        try:
            _raw_run_sql_query("CREATE LANGUAGE plpythonu;", True)
        except:
            _error('Cannot create language plpythonu. Stopping installation...', False)
            raise Exception

    # Check PL/Python version
    _raw_run_sql_query("DROP FUNCTION IF EXISTS plpy_version_for_pdltools();", False)
    _raw_run_sql_query("""
        CREATE OR REPLACE FUNCTION plpy_version_for_pdltools()
        RETURNS TEXT AS
        $$
            import sys
            # return '.'.join(str(item) for item in sys.version_info[:3])
            return str(sys.version_info[:3]).replace(',','.').replace(' ','').replace(')','').replace('(','')
        $$
        LANGUAGE plpythonu;
    """, True)
    rv = _raw_run_sql_query("SELECT plpy_version_for_pdltools() AS ver;", True)
    python = rv[0]['ver']
    py_cur_ver = [int(i) for i in python.split('.')]
    if py_cur_ver >= py_min_ver:
        _info("> PL/Python version: %s" % python, verbose)
    else:
        _error("PL/Python version too old: %s. You need %s or greater"
                % (python, '.'.join(str(i) for i in py_min_ver)), False)
        raise Exception

    _info("> PL/Python environment OK (version: %s)" % python, True)


def _plr_check(plr_min_ver):
    """
    Check pl/r existence and version
        @param plr_min_ver min PL/R version to run PDL Tools
    """

    _info("Testing PL/R environment...", True)

    # Check PL/R existence
    rv = _raw_run_sql_query("SELECT count(*) AS CNT FROM pg_language "
                         "WHERE lanname = 'plr'", True)

    if int(rv[0]['cnt']) > 0:
        _info("> PL/R already installed", verbose)
    else:
        _info("> PL/R not installed", verbose)
        _info("> Creating language PL/R...", True)
        try:
            _raw_run_sql_query("CREATE LANGUAGE plr;", True)
        except:
            _error('Cannot create language plr. Stopping installation...', False)
            raise Exception

    # Check PL/R version
    _raw_run_sql_query("DROP FUNCTION IF EXISTS plr_version_for_pdltools();", False)
    _raw_run_sql_query("""
        CREATE OR REPLACE FUNCTION plr_version_for_pdltools()
        RETURNS TEXT AS
        $$
             return (paste(R.version$major,R.version$minor,sep="."));
        $$
        LANGUAGE plr;
    """, True)
    rv = _raw_run_sql_query("SELECT plr_version_for_pdltools() AS ver;", True)
    plr_cur_ver = rv[0]['ver']
    if plr_cur_ver >= plr_min_ver:
        _info("> PL/R version: %s" % plr_cur_ver, verbose)
    else:
        _error("PL/R version too old: {cur_ver}. You need {min_ver} or greater".format(
                                cur_ver=plr_cur_ver,
                                min_ver=plr_min_ver
                                ), 
                                False
                )
        raise Exception

    _info("> PL/R environment OK (version: %s)" % plr_cur_ver, True)


def _plperl_check(perl_min_ver,perl_max_ver):
    """
    Check pl/perl existence and version
        @param perl_min_ver min Perl version to run PDL Tools
        @param perl_max_ver max Perl version to run PDL Tools
    """

    _info("Testing PL/Perl environment...", True)

    # Check PL/Perl existence
    rv = _raw_run_sql_query("SELECT count(*) AS CNT FROM pg_language "
                         "WHERE lanname = 'plperl'", True)

    if int(rv[0]['cnt']) > 0:
        _info("> PL/Perl already installed", verbose)
    else:
        _info("> PL/Perl not installed", verbose)
        _info("> Creating language PL/Perl...", True)
        try:
            _raw_run_sql_query("CREATE LANGUAGE plperl;", True)
        except:
            _error('Cannot create language plperl. Stopping installation...', False)
            raise Exception

    # Check PL/Perl version
    _raw_run_sql_query("DROP FUNCTION IF EXISTS plperl_version_for_pdltools();", False)
    _raw_run_sql_query("""
        CREATE OR REPLACE FUNCTION plperl_version_for_pdltools()
        RETURNS TEXT STABLE AS
        $$
          $];
        $$
        LANGUAGE plperl;
    """, True)
    rv = _raw_run_sql_query("SELECT plperl_version_for_pdltools() AS ver;", True)
    perl_cur_ver = float(rv[0]['ver'])
    if perl_cur_ver <= perl_min_ver:
        _error("PL/Perl version too old: %s. You need %s or greater"
                % (str(perl_cur_ver),str(perl_min_ver)), False)
        raise Exception
    elif perl_cur_ver >= perl_max_ver:
        _error("PL/Perl version too new: %s. You need %s or less"
                % (str(perl_cur_ver),str(perl_max_ver)), False)
        raise Exception
    else:
        _info("> PL/Perl version: %s" % str(perl_cur_ver), verbose)

    _info("> PL/Perl environment OK (version: %s)" % str(perl_cur_ver), True)

def _error(msg, stop):
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

def _info(msg, verbose=True):
    """
    Info message wrapper (verbose)
        @param msg info message
        @param verbose prints only if True
    """
    # Print to stdout
    if verbose:
        print this + ' : INFO : ' + msg

def _print_revs(rev, dbrev, sugar_dbrev, con_args, schema, sugar_schema):
    """
    Print version information
        @param rev OS-level PDL Tools version
        @param dbrev PDL Tools version installed in DB
        @param sugar_dbrev SUgAR version installed in DB
        @param con_args database connection arguments
        @param schema PDL Tools schema name
    """
    _info("PDL Tools version    = %s (%s)" % (rev, sys.argv[0]), True)
    _info("SUgAR version    = %s" % sugar_rev, True)
    if con_args:
        try:
            _info("PDL Tools database version = %s (host=%s, db=%s, schema=%s)"
                   % (dbrev, con_args['host'], con_args['database'], schema), True)
        except:
            _info("PDL Tools database version = [Unknown] (host=%s, db=%s, schema=%s)"
                   % (con_args['host'], con_args['database'], schema), True)
        try:
            _info("SUgAR database version = %s (host=%s, db=%s, schema=%s)"
                   % (sugar_dbrev, con_args['host'], con_args['database'], schema), True)
        except:
            _info("SUgAR database version = [Unknown] (host=%s, db=%s, schema=%s)"
                   % (con_args['host'], con_args['database'], schema), True)
    return


def _get_dbver(platform):
    """ Read version number from database (of form X.Y) """
    try:
        versionStr = _raw_run_sql_query("""SELECT pg_catalog.version()""",
                                     True)[0]['version']
        if(platform=='hawq'):
            match = re.search("HAWQ[a-zA-Z\s]*(\d+\.\d+)", versionStr)
        else:
	    match = re.search("Greenplum[a-zA-Z\s]*(\d+\.\d+)", versionStr) 
	    if match and match.group(1) == '4.3':
	        match_details = re.search("Greenplum[a-zA-Z\s]*(\d+\.\d+.\d+)", versionStr)
                if __get_rev_num(match_details.group(1)) >= __get_rev_num('4.3.5'):
	            return '4.3ORCA'
        return None if match is None else match.group(1)
    except:
        _error("Failed reading database version", True)

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

def _make_dir(dir):
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

def _db_create_schema(schema,session):
    """
    Create schema
        @param schema name of the schema to create
    """

    _info("> Creating %s schema" % schema.upper(), True)
    try:
        session.exec_query("CREATE SCHEMA %s;" % schema, True)
    except:
        _Error('Cannot create new schema.', False)
        raise Exception

def _db_grant_usage(schema,session):
    """
    Grant usage
        @param schema name of the schema to grant permissions to
    """

    _info("> Granting usage on %s schema" % schema.upper(), True)
    try:
        session.exec_query("GRANT USAGE ON SCHEMA %s TO PUBLIC;" % schema, True)
    except:
        _Error('Cannot grant permissions on schema.', False)
        raise Exception

def _db_update_migration_history(schema, curr_rev, session):
    """
    Create/update MigrationTable
        @param schema Name of the target schema
        @param curr_rev Revision number to add.
    """
    # Create MigrationHistory table if it does not already exist.
    # history table without recreating it.
    results = _raw_run_sql_query("""SELECT * FROM pg_catalog.pg_tables
                 WHERE schemaname='%s' AND tablename='migrationhistory';"""
                 % schema,True)
    if len(results)==0:
        _info("> %s.MigrationHistory table does not exist. Creating." % schema.upper(), verbose)
        sql = """CREATE TABLE %s.migrationhistory
               (id serial, version varchar(255),
               applied timestamp default current_timestamp);""" % schema
        session.exec_query(sql, True)
        _info("> %s.MigrationHistory table created." % schema.upper(), True)
    else:
        _info("> %s.MigrationHistory table exists." % schema.upper(), True)

    # Stamp the DB installation
    try:
        _info("> Writing version info in %s.MigrationHistory table"
               % schema.upper(), True)
        session.exec_query("INSERT INTO %s.migrationhistory(version) "
                        "VALUES('%s')" % (schema, curr_rev), True)
    except:
        _error("Cannot insert data into %s.migrationhistory table"
                % schema.upper(), False)
        raise Exception

def _db_install_module(module, platform, session):
    """
    Create module objects in the schema
        @param module Name of module to install
        @param platform Type of target DB
        @param session Name of transaction manager
    """
    # Find the Python module dir (platform specific or generic)
    if os.path.isdir(pdltoolsdir + "/ports/{platform}".format(platform=platform) + "/" + dbver + "/modules/" + module):
        dsdir_mod_py = pdltoolsdir + "/ports/{platform}".format(platform=platform) + "/" + dbver + "/modules"
    else:
        dsdir_mod_py = pdltoolsdir + "/modules"

    # Find the SQL module dir (platform specific or generic)
    if os.path.isdir(pdltoolsdir + "/ports/{platform}".format(platform=platform) + "/modules/" + module):
        dsdir_mod_sql = pdltoolsdir + "/ports/{platform}".format(platform=platform) + "/modules"
        rel_path = "/ports/"+platform+"/modules/"+module
    elif os.path.isdir(pdltoolsdir + "/modules/" + module):
        dsdir_mod_sql = pdltoolsdir + "/modules"
        rel_path = "/modules/"+module
    else:
        # This was a platform-specific module, for which no default exists.
        # We can just skip this module.
        rel_path = None
        return rel_path

    # Loop through all SQL files for this module
    mask = dsdir_mod_sql + '/' + module + '/*.sql_in'
    sql_files = glob.glob(mask)

    if not sql_files:
        _info("No files found in: %s" % mask, True)
        raise Exception

    # Execute all SQL files for the module
    for sqlfile in sql_files:
        retval = session.exec_file(dsdir_mod_py, module, sqlfile, module)
        # Check the exit status
        if retval != 0:
            raise Exception

    return rel_path

class install_monitor:
    def __init__(self, schema, sugar_schema, madlib_schema):
      self.schema=schema
      self.sugar_schema=sugar_schema
      self.objects=set()
      self.schema_re=re.compile(r"\b"+schema.lower()+r"\b")
      self.sugar_schema_re=re.compile(r"\b"+sugar_schema.lower()+r"\b")
      self.madlib_schema_re=re.compile(r"\b"+madlib_schema.lower()+r"\b")
    def post_install_printout(self,module,session):
      current=set(_multi_format_schema_objects(self.schema,session).keys()
                   ).union(set(_multi_format_schema_objects(
                             self.sugar_schema,session).keys()))
      newobj=current.difference(self.objects)
      self.objects=current
      for x in newobj:
        obj=self.madlib_schema_re.sub("MADLIB_SCHEMA",
              self.sugar_schema_re.sub("SUGAR_SCHEMA",
                self.schema_re.sub("PDLTOOLS_SCHEMA",x)))
        _info("MODULE(%s): %s" % (module,obj), True)

def _db_clean_create_objects(schema, platform, sugar_schema, madlib_schema,
                             output, session):
    """
    Create PDL Tools DB objects in the schema and print objects belonging
    to each module.
        @param schema Name of the target PDL Tools schema
        @param platform Type of target DB
        @param sugar_schema Name of the target SUgARlib schema
        @param madlib_schema Name of schema where MADlib resides
        @param output Enable per-module-function printing
    """
    if output:
      monitor=install_monitor(schema,sugar_schema, madlib_schema)
    _info("> Updating PDL Tools migration history.", True)
    _db_update_migration_history(schema, rev, session)
    _info("> Updating SUgAR migration history.", True)
    _db_update_migration_history(sugar_schema, sugar_rev, session)
    if output:
      monitor.post_install_printout("/ports/greenplum/modules/common",session)
    # We're annexing the update history table et al. to the "common" module.

    _info("> Creating objects for modules:", True)

    # Loop through all modules/modules
    ## portspecs is a global variable

    for moduleinfo in portspecs['modules']:
        # Get the module name
        module = moduleinfo['name']
        _info("> - %s" % module, True)
        rel_path=_db_install_module(module, platform, session) 
        if output and rel_path:
          monitor.post_install_printout(rel_path,session)

def _drop_schema(schema, session):
    # Drop the schema
    _info("> Dropping schema %s" % schema.upper(), verbose)
    try:
        session.exec_query("DROP SCHEMA %s CASCADE;" % schema, True)
    except:
        _error("Cannot drop schema %s. Stopping." % schema.upper(), True)

## # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# Read version from MigrationHistory table in database
# @param schema schema-name in which to look for table
## # # # # # # # # # # # # # # # # # # # # # # # # # # # #
def _get_installed_ver(schema,session):
    try:
        row = _raw_run_sql_query("""SELECT count(*) AS cnt FROM pg_tables
            WHERE schemaname='%s' AND tablename='migrationhistory'""" % (schema), True)
        if int(row[0]['cnt']) > 0:
            row = _raw_run_sql_query("""SELECT version FROM %s.migrationhistory
                WHERE applied IS NOT NULL
                ORDER BY applied DESC LIMIT 1""" % schema, True)
            if row:
                return row[0]['version']
    except:
        pass

    return None

def _schema_exists(schema, session):
    # Test if schema exists
    result=_raw_run_sql_query("SELECT schema_name FROM information_schema.schemata WHERE schema_name='%s';" % schema, True)
    return len(result)!=0

def _schema_writable(schema,session):
    # Test if schema is writable
    try:
        session.exec_query("CREATE TABLE %s.__pdltools_test_table (A INT);" % schema, False)
        session.exec_query("DROP TABLE %s.__pdltools_test_table;" % schema, False)
        schema_writable = True
    except:
        schema_writable = False
    return schema_writable

def _cmp_versions(ver_a, ver_b):
  a_list = ver_a.split('.')
  b_list = ver_b.split('.')
  return cmp(a_list,b_list)

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

def _find_schema_objects(schema, session):
    '''
       Return all objects in a given schema.
    '''
    # For PostgreSQL, replace "opcamid" by "opcmethod".
    iam_results=_raw_run_sql_query("""
SELECT
                opcname,
                amname AS index,
                oc.oid AS objid
            FROM
                pg_namespace AS ns,
                pg_opclass AS oc,
                pg_am AS am
            WHERE
                ns.nspname = '{schema}'
                AND oc.opcnamespace = ns.oid
                AND am.oid = oc.opcamid;
                     """.format(schema=schema), True)
    udo_results=_raw_run_sql_query("""
SELECT
                oprname,
                oprleft::regtype AS lefttype,
                oprright::regtype AS righttype,
                o.oid AS objid
            FROM
                pg_operator AS o,
                pg_namespace AS ns
            WHERE
                ns.nspname = '{schema}'
                AND o.oprnamespace = ns.oid;
                   """.format(schema=schema), True)
    for i in range(len(udo_results)):
      if udo_results[i]['lefttype']=='-':
        udo_results[i]['lefttype']='NONE'
      if udo_results[i]['righttype']=='-':
        udo_results[i]['righttype']='NONE'
    udt_results=_raw_run_sql_query("""
SELECT
		t.typname AS typname,
                CASE WHEN t.typtype='b' THEN 'BASE'
		WHEN t.typtype='d' THEN 'DOMAIN'
		WHEN t.typtype='e' THEN 'ENUM'
		WHEN t.typtype='r' THEN 'RANGE'
		ELSE 'UNRECOGNIZED' END AS kind,
                t.oid AS objid
            FROM
                pg_namespace AS nsp,
                pg_type AS t
            WHERE
                nsp.nspname = '{schema}'
                AND t.typnamespace = nsp.oid
		AND t.typtype NOT IN ('c','p');
          """.format(schema=schema), True)
    for i in range(len(udt_results)):
      if udt_results[i]['kind'] in ['BASE', 'ENUM', 'RANGE']:
        udt_results[i]['kind']='TYPE'
      if udt_results[i]['kind']=='UNRECOGNIZED':
        _error("Found UDT "+udt_results[i]['typname']
               +" of unexpected type. Stopping.",True)
    rel_results=_raw_run_sql_query("""
SELECT
                c.relname AS relation,
                CASE WHEN c.relkind='r' THEN 'TABLE'
                     WHEN c.relkind='v' THEN 'VIEW'
                     WHEN c.relkind='i' THEN 'INDEX'
                     WHEN c.relkind='S' THEN 'SEQUENCE'
                     WHEN c.relkind='c' THEN 'TYPE'
                     WHEN c.relkind='t' THEN 'TOAST'
                     ELSE 'UNRECOGNIZED' END AS kind,
                c.oid AS objid
            FROM
                pg_namespace nsp,
                pg_class c
            WHERE
                nsp.nspname = '{schema}'
                AND c.relnamespace = nsp.oid;
          """.format(schema=schema), True)
    for i in range(len(rel_results)):
      if rel_results[i]['kind'] in ['TOAST','UNRECOGNIZED']:
        _error("Found relation "+rel_results[i]['relation']
               +" of unexpected type. Stopping.",True)
    udf_results=_raw_run_sql_query("""
SELECT
        proctyp || ' ' || procnamespace || '.' || procname || '(' ||
            string_agg(argnamespace || '.' || argtypname, ', '
                     ORDER BY rn)
            || ')' AS signature,
        procname,
        procoid AS objid
   FROM (
        SELECT
                procnamespace,
                procname,
                num_args,
                procoid,
                CASE WHEN proisagg THEN 'AGGREGATE' ELSE 'FUNCTION'
                  END AS proctyp,
                arg_oids[rn] AS elem,
                nsp1.nspname AS argnamespace,
                t.typname argtypname,
                rn
             FROM (
                SELECT *, generate_series(array_lower(arg_oids,1),
                                          array_upper(arg_oids,1)) AS rn
                    FROM (
                        SELECT
                        nsp.nspname AS procnamespace,
                        p.proname AS procname,
                        p.pronargs AS num_args,
                        p.proargtypes AS arg_oids,
                        p.oid AS procoid,
                        p.proisagg AS proisagg
                    FROM
                        pg_namespace AS nsp,
                        pg_proc AS p
                    WHERE
                        nsp.nspname = '{schema}'
                        AND p.pronamespace = nsp.oid
                    ) x
              ) y,
                  pg_type t,
                  pg_namespace AS nsp1
              WHERE
                t.oid=arg_oids[rn]
                AND nsp1.oid=t.typnamespace
  ) z
      GROUP BY (procoid,procnamespace,procname,num_args,proctyp)
UNION
SELECT
        proctyp || ' ' || procnamespace || '.' || procname || '()' AS signature,
        procname,
        procoid AS objid
                   FROM (
                        SELECT
                        nsp.nspname AS procnamespace,
                        p.proname AS procname,
                        p.pronargs AS num_args,
                        p.oid AS procoid,
                        CASE WHEN p.proisagg THEN 'AGGREGATE' ELSE 'FUNCTION'
                          END AS proctyp
                    FROM
                        pg_namespace AS nsp,
                        pg_proc AS p
                    WHERE
                        nsp.nspname = '{schema}'
                        AND p.pronamespace = nsp.oid
                        AND p.pronargs = 0
                    ) x;
          """.format(schema=schema), True);
    # Note, a more user-friendly output can be generated by use of
    # "textin(regtypeout(elem:regtype))" instead of "argnamespace.argtypname",
    # but this is less machine-friendly. It uses "[]" and spaces
    # (e.g. "character varying") in type names, and outputs them without
    # schema names if they are on the path (thus creating a dependence on the
    # currently-set search_path).
    return (iam_results, udo_results, udt_results, rel_results, udf_results)

def _multi_format_schema_objects(schema, session):
    '''
       Reformat a listing of all objects for multiple uses.
    '''
    (iam_results, udo_results, udt_results, rel_results, udf_results)= \
      _find_schema_objects(schema, session)
    results={}
    for result in iam_results:
      results["IAM: OPERATOR_CLASS {schema}.{opcname} USING {index}"
             .format(schema=schema, opcname=result['opcname'],
                     index=result['index'])]=('pg_opclass',result['objid'],
                      result['opcname'],schema)
    for result in udo_results:
      results["UDO: OPERATOR {schema}.{opname}({left},{right})".format(
          schema=schema,opname=result['oprname'],
          left=result['lefttype'],right=result['righttype'])]=('pg_operator',
                      result['objid'],result['oprname'],schema)
    for result in udt_results:
      results["UDT: {kind} {schema}.{typname}".format(
          schema=schema,typname=result['typname'],kind=result['kind'])]=(
                      'pg_type',result['objid'],result['typname'],schema)
    for result in rel_results:
      results["REL: {kind} {schema}.{relation}".format(
         schema=schema, kind=result['kind'], relation=result['relation'])]=(
                      'pg_class',result['objid'],result['relation'],schema)
    for result in udf_results:
      results["UDF: {signature}".format(signature=result['signature'])]=(
                      'pg_proc',result['objid'],result['procname'],schema)
    return results

def _list_schema_objects(schema, session):
    '''
       Print a listing of all objects in a given schema.
    '''
    results=_multi_format_schema_objects(schema, session).keys()
    _info("\nUser-defined operator classes:", True)
    _info("Format: OPERATOR CLASS schema.operator_class USING index_access_method", True)
    for result in results:
      if result[:3]=='IAM':
        x=result
        x[13]=' '
        _info(x, True)
    _info("\nUser-defined operators:", True)
    _info("Format: OPERATOR schema.oper_name(left_type,right_type)", True)
    for result in results:
      if result[:3]=='UDO':
        _info(result, True)
    _info("\nUser-defined non-composite types:", True)
    _info("Format: TYPE/DOMAIN schema.type_name", True)
    for result in results:
      if result[:3]=='UDT':
        _info(result, True)
    _info("\nTables and table-like objects (e.g., composite types):", True)
    _info("Format: TABLE/VIEW/INDEX/SEQUENCE/TYPE schema.relation", True)
    for result in results:
      if result[:3]=='REL':
        _info(result, True)
    _info("\nUser-defined functions and aggregates:", True)
    _info("Format: FUNCTION/AGGREGATE schema.procname(schema.argtype,...)",
           True)
    for result in results:
      if result[:3]=='UDF':
        _info(result, True)

def main():
    '''
        Fetch arguments and prepare installation of pdltools in target DB
    '''

    global session

    parser = argparse.ArgumentParser(
                description='PDL Tools package manager (' + rev + ')',
                argument_default=False,
                formatter_class=argparse.RawTextHelpFormatter,
                epilog="""Example:

  $ pdlpack install -s pdltools -p greenplum -S SUgARlib -M MADlib -c gpadmin@mdw:5432/testdb

  This will install PDL Tools objects into a Greenplum database called TESTDB
  running on server MDW:5432. Installer will try to login as GPADMIN
  and will prompt for password. The target schema will be "SUgARlib" for
  the SUgAR library and "pdltools" for all else. Functionality borrowed from
  MADlib will assume that MADlib is (or will be) installed in the "MADlib"
  schema.
""")

    parser.add_argument(
        'command', metavar='COMMAND', nargs=1,
        choices=['install', 'install-check', 'reinstall', 'uninstall',
                 'check-dep', 'list-lib', 'list-db',
                 'clean-install'],
        help = "One of the following options:\n"
            + "  install         : Install or upgrade library\n"
            + "  install-check   : Run test scripts\n"
            + "  reinstall       : Overwrite an existing installation\n"
            + "  uninstall       : Remove an existing installation\n"
            + "  check-dep       : Show DB dependencies on library\n"
            + "  list-lib        : List objects in library modules\n"
            + "  list-db         : List objects installed in DB schema\n"
            + "  clean-install : Clean installation, output which objects\n"
            + "                    belong to which  sub-module"
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

    parser.add_argument('-p', '--platform', nargs=1, dest='platform', required=True,
                        metavar='PLATFORM', choices=portid_list,
                        help="Target database platform, current choices: " + str(portid_list))


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
    global platform, verbose, testcase, tmpdir_arg
    verbose = args.verbose
    testcase = args.testcase
    platform = args.platform[0]
    tmpdir_arg = args.tmpdir

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
    dbver = _get_dbver(platform)

    portdir = os.path.join(pdltoolsdir, "ports", platform)
    supportedVersions = [dirItem for dirItem in os.listdir(portdir) if os.path.isdir(os.path.join(portdir, dirItem))
                             and re.match("^\d+\.\d+", dirItem)]
    if dbver is None:
       dbver = ".".join(map(str, max([map(int, versionStr.split('.')) for versionStr in supportedVersions])))
       _info("Could not parse version string reported by {DBMS}. Will "
              "default to newest supported version of {DBMS} "
              "({version}).".format(DBMS=platform, version=dbver), True)
    else:
       _info("Detected %s version %s." % (platform, dbver),True)
       if not os.path.isdir(os.path.join(portdir, dbver)):
            _error("This version is not among the %s versions for which "
                    "PDL Tools support files have been installed (%s)." %
                   (platform, ", ".join(supportedVersions)), True)

    global pdltoolsdir_lib
    global pdltoolsdir_conf

    #Adjust paths to the lib and config directories for this port (if they exist)
    if os.path.isfile(pdltoolsdir + "/ports/{platform}".format(platform=platform) + "/" + dbver + "/lib/libpdltools.so"):
        pdltoolsdir_lib = pdltoolsdir + "/ports/{platform}".format(platform=platform) + "/" + dbver + "/lib/libpdltools.so"

    if os.path.isdir(pdltoolsdir + "/ports/{platform}".format(platform=platform) + "/" + dbver + "/config"):
        pdltoolsdir_conf = pdltoolsdir + "/ports/{platform}".format(platform=platform) + "/" + dbver + "/config"

    # Get the list of modules for this port
    global portspecs
    portspecs = configyml.get_modules(pdltoolsdir_conf)

    if(args.command[0]=='install'):
        install(schema, platform, sugar_schema, madlib_schema)
    elif(args.command[0]=='install-check'):
        install_check(schema, platform, sugar_schema, madlib_schema, args)
    elif(args.command[0]=='reinstall'):
        reinstall(schema, platform, sugar_schema, madlib_schema)
    elif(args.command[0]=='uninstall'):
        uninstall(schema, sugar_schema)
    elif(args.command[0]=='check-dep'):
        check_dep(schema, sugar_schema)
    elif(args.command[0]=='list-lib'):
        list_lib(schema, platform, sugar_schema)
    elif(args.command[0]=='list-db'):
        list_db(schema, sugar_schema)
    elif(args.command[0]=='clean-install'):
        clean_install(schema, platform, sugar_schema, madlib_schema, verbose)
    else:
        _info("Command not recognized.", True)

def install_check(schema, platform, sugar_schema, madlib_schema, args):
	'''
	Run install checks
	'''
	global con_args, portspecs
        session=session_manager(schema,platform,sugar_schema,madlib_schema)
	# 0) First check if PDL Tools schema exists, if not we'll exit (install-check should only be called post installation of pdltools)
	pdltools_schema_exists = _raw_run_sql_query("select schema_name from information_schema.schemata where schema_name='{pdltools_schema}';".format(pdltools_schema=schema), False)
	if(not pdltools_schema_exists):
	    _info("{pdltools_schema} schema does not exist. Please run install-check after installing PDL Tools. Install-check stopped.".format(pdltools_schema=schema), True)
            return
	# Now check if SUgARlib schema exists.
	sugar_schema_exists = _raw_run_sql_query("select schema_name from information_schema.schemata where schema_name='{sugarlib_schema}';".format(sugarlib_schema=sugar_schema), False)
	if(not sugar_schema_exists):
	    _info("{sugarlib_schema} schema does not exist. Please run install-check after installing PDL Tools. Install-check stopped.".format(sugarlib_schema=sugar_schema), True)
            return

        # Create install-check user
	test_user = 'pdltools_installcheck'
	try:
	    session.exec_query("DROP USER IF EXISTS %s;" % (test_user), False)
	except:
	    session.exec_query("DROP OWNED BY %s CASCADE;" % (test_user), True)
	    session.exec_query("DROP USER IF EXISTS %s;" % (test_user), True)
	session.exec_query("CREATE USER %s;" % (test_user), True)
	session.exec_query("GRANT ALL ON SCHEMA %s TO %s;" %(schema, test_user), True)
	session.exec_query("GRANT ALL ON SCHEMA %s TO %s;" %(sugar_schema, test_user), True)
        session.exec_query("GRANT USAGE ON SCHEMA %s TO %s;" %(madlib_schema, test_user),True)
	# 2) Run test SQLs
	_info("> Running test scripts for:", verbose)

	caseset = (set([test.strip() for test in args.testcase.split(',')])
		   if args.testcase != "" else set())

	# Loop through all modules
	for moduleinfo in portspecs['modules']:

	    # Get module name
	    module = moduleinfo['name']

	    # Skip if doesn't meet specified modules
	    if len(caseset) > 0 and module not in caseset:
		continue

	    _info("> - %s" % module, verbose)

	    # Find the Python module dir (platform specific or generic)
	    if os.path.isdir(pdltoolsdir + "/ports/{platform}".format(platform=platform) + "/" + dbver + "/modules/" + module):
		dsdir_mod_py = pdltoolsdir + "/ports/{platform}".format(platform=platform) + "/" + dbver + "/modules"
	    else:
		dsdir_mod_py = pdltoolsdir + "/modules"

	    # Find the SQL module dir (platform specific or generic)
	    if os.path.isdir(pdltoolsdir + "/ports/{platform}".format(platform=platform) + "/modules/" + module):
		dsdir_mod_sql = pdltoolsdir + "/ports/{platform}".format(platform=platform) + "/modules"
	    else:
		dsdir_mod_sql = pdltoolsdir + "/modules"

	    # Prepare test schema
	    test_schema = "pdltools_installcheck_%s" % (module)
	    session.exec_query("DROP SCHEMA IF EXISTS %s CASCADE; CREATE SCHEMA %s;"
			    % (test_schema, test_schema), True)
	    session.exec_query("GRANT ALL ON SCHEMA %s TO %s;"
			    % (test_schema, test_user), True)

	    # Switch to test user and prepare the search_path
	    pre_sql = '-- Switch to test user:\n' \
		      'SET ROLE %s;\n' \
		      '-- Set SEARCH_PATH for install-check:\n' \
		      'SET search_path=%s,%s,%s;\n' \
		      % (test_user, test_schema, schema, sugar_schema)
            session.set_pre_sql(pre_sql)

	    # Loop through all test SQL files for this module
	    sql_files = dsdir_mod_sql + '/' + module + '/test/*.sql_in'
	    for sqlfile in sorted(glob.glob(sql_files), reverse=True):
		# If there is no problem with the SQL file
		milliseconds = 0

		# Run the SQL
		run_start = datetime.datetime.now()
		retval = session.exec_file(dsdir_mod_py, module,
					sqlfile, module+'/test')
		# Runtime evaluation
		run_end = datetime.datetime.now()
		milliseconds = round((run_end - run_start).seconds * 1000 +
				     (run_end - run_start).microseconds / 1000)

		# Check the exit status
		if retval != 0:
		    result = 'FAIL'
		    keeplogs = True
		# Since every single statement in the test file gets logged,
		# an empty log file indicates an empty or a failed test
		elif os.path.isfile(session.logname()) and \
                     os.path.getsize(session.logname()) > 0:
		    result = 'PASS'
		# Otherwise
		else:
		    result = 'ERROR'

		# Spit the line
		print "TEST CASE RESULT|Module: " + module + \
		    "|" + os.path.basename(sqlfile) + "|" + result + \
		    "|Time: %d milliseconds" % (milliseconds)

	    # Cleanup test schema for the module
	    session.exec_query("DROP SCHEMA IF EXISTS %s CASCADE;" % (test_schema), True)

	# Drop install-check user
	session.exec_query("DROP OWNED BY %s CASCADE;" % (test_user), True)
	session.exec_query("DROP USER %s;" % (test_user), True)

def _dep_graph(schema,sugar_schema,session):
  # Build dependence graph
  namemap={'class':'rel','constraint':'con','conversion':'con','opclass':'opc',
           'operator':'opr','proc':'pro','type':'typ'}
  query_template='''
SELECT
                 p.relname AS kind,
                 d.{obj}objid   AS objid,
                 x.{pfx}name AS name,
                 n.nspname AS namespace
               FROM
                 pg_depend d,
                 pg_class p,
                 pg_{table} x,
                 pg_namespace n
               WHERE
                 p.oid=d.{obj}classid AND
                 p.relname='pg_{table}' AND
                 x.oid=d.{obj}objid AND
                 n.oid=x.{pfx}namespace
    '''
  query=" UNION ".join([query_template.format(obj='',pfx=namemap[x],table=x)
                          for x in namemap.keys()]+
                       [query_template.format(obj='ref',pfx=namemap[x],table=x)
                          for x in namemap.keys()])+";"
  known_list=_raw_run_sql_query(query, True)
  known_map={}
  for x in known_list:
    known_map[(x['kind'],x['objid'],None,None)]=(x['kind'],x['objid'],
                                               x['name'],x['namespace'])

  dependencies=_raw_run_sql_query('''
SELECT
                 p.relname AS depender_kind,
                 d.objid   AS depender_oid,
                 p1.relname AS dependee_kind,
                 d.refobjid AS dependee_oid
              FROM
                pg_depend d,
                pg_class p,
                pg_class p1
              WHERE
                d.classid=p.oid AND d.refclassid=p1.oid
UNION
SELECT
                'pg_class' AS depender_kind,
                r.ev_class AS depender_oid,
                'pg_rewrite' AS dependee_kind,
                r.oid AS dependee_oid
              FROM
                pg_rewrite r
UNION
SELECT
                'pg_class' AS depender_kind,
                a.attrelid AS depender_oid,
                'pg_type' AS dependee_kind,
                a.atttypid AS dependee_oid
              FROM
                pg_attribute a;
    ''', True)
  dependence_graph={}
  for d in dependencies:
    depender=(d['depender_kind'],d['depender_oid'],None,None)
    dependee=(d['dependee_kind'],d['dependee_oid'],None,None)
    if depender in known_map:
      depender=known_map[depender]
    if dependee in known_map:
      dependee=known_map[dependee]
    if depender not in dependence_graph:
      dependence_graph[depender]=set()
    if dependee not in dependence_graph:
      dependence_graph[dependee]=set()
    dependence_graph[dependee].add(depender)

  return dependence_graph

def _find_deps(schema,sugar_schema,base_objects,dependence_graph):
  # Find dependencies from base_objects in dependence_graph
  # That are neither in schema nor in sugar_schema.

  new_depender=base_objects.values()

  recursive_depender={}
  for x in base_objects:
    recursive_depender[base_objects[x]]=set([x])

  while len(new_depender)!=0:
    old_depender=new_depender
    new_depender=set()
    for dependee in old_depender:
      if dependee in dependence_graph:
        for depender in dependence_graph[dependee]:
          if depender not in recursive_depender:
            recursive_depender[depender]=set()
          old_len=len(recursive_depender[depender])
          recursive_depender[depender] |= recursive_depender[dependee]
          new_len=len(recursive_depender[depender])
          if old_len!=new_len:
            new_depender.add(depender)

  # Workaround for the bug that in versions [1.2, 1.4) of the library the
  # module "complex" mistakenly create "OPERATOR public.=(complex,complex)".
  complex_oid=None
  for x in dependence_graph:
    if x[0]=='pg_type' and x[2]=='complex' and x[3]==schema:
      complex_oid=x[1]
  if complex_oid!=None:
    rc= _raw_run_sql_query("""
      SELECT o.oid
      FROM pg_operator o,
           pg_namespace n
      WHERE o.oprname='='
      AND o.oprnamespace=n.oid
      AND n.nspname='public'
      AND o.oprleft='{complex}'
      AND o.oprright='{complex}';
      """.format(complex=complex_oid),True)
    if len(rc)>0:
      complex_eq_oid=rc[0]['oid']
      unwanted_keys = [x for x in recursive_depender if x[1]==complex_eq_oid]
      for key in unwanted_keys:
        del recursive_depender[key]

  # Consider only dependencies not in schema.
  # Disregard toast tables.
  unwanted_keys = [x for x in recursive_depender
                      if x[3] in [None,schema,sugar_schema,'pg_toast']]
  for key in unwanted_keys:
    del recursive_depender[key]

  # Disregard type names that relate to already-printed table types.
  oid_map=dict([((x[0],x[2],x[3]),x) for x in recursive_depender.keys()])
  unwanted_keys = [oid_map[('pg_type',x[1],x[2])] for x in oid_map if
                   x[0]=='pg_class' and ('pg_type',x[1],x[2]) in oid_map]
  for key in unwanted_keys:
    del recursive_depender[key]

  return recursive_depender

def _print_deps(deps):
  for dep in deps:
    _info("\n",True)
    if dep[2]!=None and dep[3]!=None:
      _info("Object "+dep[3]+"."+dep[2]+"(oid="+str(dep[1])+") listed in "+dep[0]+" depends on:",True)
    else:
      _info("Object oid="+str(dep[1])+" listed in "+dep[0]+" depends on:",True)
    for dependee in deps[dep]:
      _info(_pretty(dependee),True)

def uninstall(schema, sugar_schema):
    '''
    Uninstall library
    '''
    _info("Uninstalling PDL Tools.", True)
    session=session_manager(schema,'',sugar_schema,'')
    try:
      session.exec_query("SELECT "+schema+".pdltools_version(), "+
                     sugar_schema+".sugar_version();", False)
    except:
      _error("PDL Tools installation not found in given schemata or is too old to be uninstalled. (To brute-force uninstall, drop the pdltools and SUgARlib schemas.) Aborting.", True)
    # load existing installation information
    db_objects={}
    db_objects.update(_multi_format_schema_objects(schema, session))
    db_objects.update(_multi_format_schema_objects(sugar_schema, session))

    # Find dependencies
    dependence_graph=_dep_graph(schema,sugar_schema, session)
    deps=_find_deps(schema,sugar_schema,db_objects,dependence_graph)
    if len(deps)==0:
      _info("No dependencies detected.", verbose)
    else:
      _info("Cannot uninstall PDL Tools, because the following objects depend on it.", True)
      _print_deps(deps)
      _info("Please resolve dependencies before trying again.", True)
      exit(0)
    _info("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!", True)
    _info("Proceeding with uninstall will drop all schema objects.", True)
    _info("While no direct DB dependence exists on these objects, it is still possible that UDFs/views/etc. rely on the library.", True)
    _info("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!", True)
    _info("Are you sure you want to proceed?", True)
    go = raw_input('>>> ').upper()
    while go =='' or go[0] not in 'YN':
      go = raw_input('Yes or No >>> ').upper()
    if go[0] == 'N':
      _info("Stopping uninstallation.", True)
      exit(0)
    _drop_schema(schema, session)
    _drop_schema(sugar_schema, session)
    _info("Library successfully uninstalled.", True)

def check_dep(schema, sugar_schema):
    '''
    Find objects that depend on currently-installed version.
    '''
    session=session_manager(schema,'',sugar_schema,'')
    # load existing installation information
    db_objects={}
    db_objects.update(_multi_format_schema_objects(schema, session))
    db_objects.update(_multi_format_schema_objects(sugar_schema, session))

    # Find dependencies
    dependence_graph=_dep_graph(schema,sugar_schema, session)
    deps=_find_deps(schema,sugar_schema,db_objects,dependence_graph)
    if len(deps)==0:
      _info("No dependencies detected.", verbose)
    else:
      _print_deps(deps)

def _find_lib_objects(schema, platform, sugar_schema):
  '''
  Find objects in library modules and lib compatibility status.
  '''
  # Loop through all modules
  ## portspecs is a global variable

  lib_objects={}
  lib_comp={}

  try:
    for moduleinfo in portspecs['modules']:
      # Get the module name
      module = moduleinfo['name']
  
      # Find the SQL module dir (platform specific or generic)
      if os.path.isdir(pdltoolsdir + "/ports/{platform}".format(platform=platform) + "/modules/" + module):
        dsdir_mod_sql = pdltoolsdir + "/ports/{platform}".format(platform=platform) + "/modules/" + module + "/"
      elif os.path.isdir(pdltoolsdir + "/modules/" + module):
        dsdir_mod_sql = pdltoolsdir + "/modules/" + module + "/"
      else:
        _info("Directory not found for module "+module, True)
        raise Exception

      filename=dsdir_mod_sql+module+".content"
      if not os.path.isfile(filename):
        _info("File not found: "+filename+".",True)
        raise Exception
      lib_objects[module]=[x.strip() for x in file(filename).readlines()]
      filename=dsdir_mod_sql+module+".yml"
      if not os.path.isfile(filename):
        _info("File not found: "+filename+".",True)
        raise Exception
      lib_comp[module]=yaml.load(file(filename))
      for x in lib_comp[module]:
        lib_comp[module][x]=str(lib_comp[module][x])
  except:
    _info("Aborting on errors.",True)
    exit(2)
  return (lib_objects,lib_comp)

def list_lib(schema, platform, sugar_schema):
  '''
  Print objects in library modules.
  '''

  _info("Objects in present version of the library.",True)

  lib_objects=_find_lib_objects(schema, platform, sugar_schema)[0]

  for module in lib_objects:
    _info("> - %s" % module, True)
    for o in lib_objects[module]:
      print "MODULE("+module+"): "+o

def list_db(schema, sugar_schema):
	'''
	List library objects installed in schemas.
	'''
	session=session_manager(schema,'',sugar_schema,'')
        _info("Objects in PDL Tools schema:", True)
        _list_schema_objects(schema, session)
        _info("\nObjects in SUgAR library schema:", True)
        _list_schema_objects(sugar_schema, session)

def clean_install(schema, platform, sugar_schema, madlib_schema, output=True, session=None):
    '''
    Fresh install. Report which objects belong to each module.
    May be slow compared to regular installation. For internal uses.
    '''
    if session==None:
        session=session_manager(schema,platform,sugar_schema,madlib_schema)
    try:
        _plpy_check(py_min_ver)
        '''PL/Perl installer is currently only available for GPDB, so we won't check this for HAWQ'''
        if(platform != 'hawq'):
            _plperl_check(perl_min_ver,perl_max_ver)

        if _schema_exists(schema, session):
          _error("PDL Tools schema already exists. Cannot proceed with clean installation.", False)
          raise Exception
        if _schema_exists(sugar_schema, session):
          _error("SUgAR schema already exists. Cannot proceed with clean installation.", False)
          raise Exception

        if not _schema_exists(madlib_schema, session):
          _error("{madlib_schema} schema does not exists. Please install MADlib first.".format(madlib_schema=madlib_schema), False)
          raise Exception

        # Create schemata
        _db_create_schema(schema, session)
        try:
            _db_create_schema(sugar_schema, session)
        except:
            _error("Rolling back installation.", False)
            _drop_schema(schema, session)
            raise Exception
        try:
            if not _schema_writable(schema, session):
              _error("PDL Tools schema not writable. Aborting installation.", False)
              raise Exception
            if not _schema_writable(sugar_schema,session):
              _error("SUgAR schema not writable. Aborting installation.", False)
              raise Exception
    
            # Granting Usage on Schemas
            _db_grant_usage(schema, session)
            _db_grant_usage(sugar_schema, session)
        
            # Create pdltools objects
            try:
                _db_clean_create_objects(schema, platform, sugar_schema, madlib_schema,output,session)
            except:
                _error("Object creation failed. Aborting installation.", False)
                raise
        
            _info("PDL Tools %s installed successfully in %s schema." % (rev, schema.upper()), True)
            _info("SUgAR %s installed successfully in %s schema." % (sugar_rev, sugar_schema.upper()), True)
            _info("Installation completed successfully.",True)

        except:
            _error("Rolling back installation.", False)
            _drop_schema(schema, session)
            _drop_schema(sugar_schema, session)
            raise Exception
    
    except:
        _error("PDL Tools installation failed. Installation aborted.", True)

def reinstall(schema, platform, sugar_schema, madlib_schema):
    '''
        Re-install pdlpack
    '''
    # Run re-installation
    _info("Preparing for PDL Tools re-installation.", True)
    uninstall(schema, sugar_schema)
    clean_install(schema, platform, sugar_schema, madlib_schema, False)

def _pretty(objdef):
  '''
  Pretty-print object definition.
  '''
  if len(objdef)<5:
    _info("Unexpected object definition: "+objdef+". Aborting.", True)
    raise Exception
  rc=objdef[5:]
  prefix="OPERATOR_CLASS"
  if len(rc)>=len(prefix):
    if rc[:len(prefix)]==prefix:
      rc[8]=' '
  return rc

def _run_drop_command(objdef, session):
  '''
  Drop object.
  '''
  if len(objdef)<5:
    _info("Unexpected object definition: "+objdef+". Aborting.", True)
    raise Exception
  rc=objdef[5:]
  rc=rc.split(' ',1)
  if len(rc)!=2:
    _info("Malformed object definition: "+objdef+". Aborting.", True)
    raise Exception
  prefix="OPERATOR_CLASS"
  if rc[0]==prefix:
    rc[0]="OPERATOR CLASS"
  _info("Dropping "+objdef+".", verbose)
  session.exec_query("DROP "+rc[0]+" IF EXISTS "+rc[1]+" CASCADE;", True)

def _safe_drop(obj, session, db_objects, dependence_graph):
  if obj not in db_objects or db_objects[obj] not in dependence_graph:
    _info("Object "+obj+" no longer exists. No need to drop.", verbose)
    return
  _run_drop_command(obj, session)
  drop_list=[db_objects[obj]]
  while len(drop_list)!=0:
    x=drop_list[0]
    drop_list=drop_list[1:]
    if x in dependence_graph:
      drop_list.extend(dependence_graph[x])
      del dependence_graph[x]

def _db_create_objects(schema, platform, sugar_schema, madlib_schema,
                       dbrev, dbsugarrev, session):
    """
    Create PDL Tools DB objects in the schema
        @param schema Name of the target PDL Tools schema
        @param platform Type of target DB
        @param sugar_schema Name of the target SUgARlib schema
        @param madlib_schema Name of schema where MADlib resides
        @param dbrev Database version of pdltools
        @param dbsugarrev Database version of sugarlib
    """

    # load library information
    (lib_objects,lib_comp)=_find_lib_objects(schema, platform, sugar_schema)

    schema_re=re.compile("PDLTOOLS_SCHEMA")
    sugar_schema_re=re.compile("SUGAR_SCHEMA")
    madlib_schema_re=re.compile("MADLIB_SCHEMA")
    for module in lib_objects:
      lib_objects[module]=set([madlib_schema_re.sub(madlib_schema,
                   sugar_schema_re.sub(sugar_schema,
                   schema_re.sub(schema,x))) for x in lib_objects[module]])

    # load existing installation information

    db_objects={}
    db_objects.update(_multi_format_schema_objects(schema, session))
    db_objects.update(_multi_format_schema_objects(sugar_schema, session))

    # Build dependence graph

    dependence_graph=_dep_graph(schema, sugar_schema, session)

    # Find objects that will need to be removed

    _info("Finding objects to be removed and their dependencies.",verbose)

    defunct_objects=db_objects.copy()
    module_objects={}
    for module in lib_objects:
      module_objects[module]={}
      for x in lib_objects[module]:
        if x in db_objects:
          module_objects[module][x]=db_objects[x]
          if x in defunct_objects:
            del defunct_objects[x]

    # Find their dependencies

    defunct_deps=_find_deps(schema,sugar_schema,defunct_objects,
                            dependence_graph)

    # Per module checks

    _info("Checking per-module upgrade needs and dependencies.",verbose)

    module_status={}
    module_deps={}
    upgrade_issues=0
    
    for moduleinfo in portspecs['modules']:
        # Get the module name
        module = moduleinfo['name']
        _info("> - %s" % module, verbose)
        mod_comp=lib_comp[module]
        if mod_comp['libpart']=='pdltools':
          installed_rev=dbrev
        elif mod_comp['libpart']=='sugar':
          installed_rev=dbsugarrev
        else:
          _error("Unable to determine library part from yml file for module "+module+". Should be one of 'pdltools' or 'sugar'. Actual value: "+mod_comp['libpart']+". Aborting",True)
        ident_cmp=_cmp_versions(mod_comp['identical'],installed_rev)
        compat_cmp=_cmp_versions(mod_comp['compatible'],installed_rev)
        if compat_cmp>0:
          module_status[module]=2 # incompatible
          _info("Module's installed version not compatible with new version.", verbose)
        elif ident_cmp>0:
          module_status[module]=1 # non-identical
          _info("Module's installed version compatible with but not identical to new version.", verbose)
        else:
          module_status[module]=0 # no need to upgrade.
          _info("Module's installed version is identical to new version. Module will not be upgraded", verbose)

        if module_status[module]>0:
          if module=="common": # Ignoring migration history, etc.
            non_udfs=[x for x in module_objects[module].keys() if len(x)<13 or
                  x[:13]!="UDF: FUNCTION"]
            for non_udf in non_udfs:
              del module_objects[module][non_udf]
          if module_status[module]==1: # If compatible, ignore UDFs.
            udfs=[x for x in module_objects[module].keys() if len(x)>=13 and
                  x[:13]=="UDF: FUNCTION"]
            for udf in udfs:
              del module_objects[module][udf]
          else:
            upgrade_issues=max(upgrade_issues,1) # warning needed
          module_deps[module]=_find_deps(schema,sugar_schema,
                            module_objects[module],dependence_graph)
          if len(module_deps[module])>0:
            module_status[module]+=2
            _info("Module has outside dependencies and cannot be upgraded.", verbose)
            upgrade_issues=max(upgrade_issues,2) # Cannot upgrade.
          else:
            _info("No outside dependencies detected for module.", verbose)

    if upgrade_issues==0 and len(defunct_deps)==0:
      _info("No upgrade issues detected. Proceeding.", verbose)
    elif upgrade_issues==2 or len(defunct_deps)>0:
      _info("Library cannot be upgraded, because existing modules that need replacing have objects that depend on them.", True)
      if len(defunct_deps)>0:
        _info("The following are dependencies on objects that no longer exist in the present version.", True)
        _print_deps(defunct_deps)
      if upgrade_issues==2:
        _info("The following are dependencies on objects that have changed and will need to be dropped to be upgraded.", True)
      for module in module_status.keys():
        if module_status[module]>2:
          _info("> - %s:" % module, True)
          _print_deps(module_deps[module])
      _info("Cannot upgrade library because this will drop dependent objects.", True)
      _info("Please resolve these dependencies before re-attempting upgrade.", True)
      _error("Aborting.",True)
    else: # upgrade issues==1:
      _info("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!", True)
      _info("WARNING: Upgrading PDL Tools will cause the following existing modules to be rewritten by new versions.", True)
      _info("No direct dependence has been detected to existing code, but other dependence types may still exist.", True)
      _info("The new code is incompatible with the old code, changing either interface or behavior. Code depending on it may not function properly after an upgrade.", True)
      _info("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!", True)
      for module in module_status.keys():
        if module_status[module]==2:
          _info("> - %s:" % module, True)
          for obj in module_objects[module]:
            _info(_pretty(obj), True)
      _info("Are you sure you wish to proceed with installation? [Y/N]", True)
      go = raw_input('>>> ').upper()
      while go =='' or go[0] not in 'YN':
        go = raw_input('Yes or No >>> ').upper()
      if go[0] == 'N':
        _info("Stopping installation.", True)
        exit(0)

    session.begin("install")
    try:
      _info("> Building upgrade plan.", True)
      _info("[Plan:] Updating PDL Tools migration history.", True)
      _db_update_migration_history(schema, rev, session)
      _info("[Plan:] Updating SUgAR migration history.", True)
      _db_update_migration_history(sugar_schema, sugar_rev, session)
      _info("[Plan:] Dropping old objects.", True)
      for obj in defunct_objects:
        _safe_drop(obj, session, db_objects, dependence_graph)
  
      _info("[Plan:] Creating objects for modules:", True)
  
      for module in module_status:
        _info("> - %s" % module, True)
        session.exec_query("-- Begin of module installation: "+module, True)
        if module_status[module]!=0:
          _info("[Plan:] Upgrading module.", verbose)
          _info("[Plan:] Dropping old module objects.", verbose)
          for object in module_objects[module]:
            _safe_drop(object, session, db_objects, dependence_graph)
          _info("[Plan:] Installing new module objects.", verbose)
          _db_install_module(module, platform, session) 
        else:
          _info("[Plan:] Module already up to date.", verbose)

      _info("Executing plan on database.", True)
      retval=session.commit()
      if retval!=0:
        _error("Errors encountered while executing plan.", False)
        raise Exception
    except:
      _info("> Rolling back installation.", True)
      session.rollback()
      _error("> Installation rolled back. Stopping.", True)
    _info("Installation successful.", True)

def install(schema, platform, sugar_schema, madlib_schema):
    '''
    Library installation and upgrade.
    '''
    session=session_manager(schema,platform,sugar_schema,madlib_schema)
    _info("Installing PDL Tools.", True)
    try:
      if not _schema_exists(schema, session):
        if not _schema_exists(sugar_schema, session):
          _info("Schemas not found. Proceeding with fresh installation.", True)
          clean_install(schema, platform, sugar_schema, madlib_schema, False, session)
          exit(0)
        else:
          _info("Schema "+schema+" exists but schema "+sugar_schema+" does not exist.", True)
          _error("Library not properly installed and cannot be upgraded. Use 'reinstall' instead.",False)
          raise Exception

      if not _schema_exists(sugar_schema, session):
        _info("Schema "+sugar_schema+" exists but schema "+schema+" does not exist.", True)
        _error("Library not properly installed and cannot be upgraded. Use 'reinstall' instead.",False)
        raise Exception

      if not _schema_exists(madlib_schema, session):
        _info("Schema "+madlib_schema+" does not exist.", True)
        _error("Please install MADlib first before installing PDLTools.", False)
 
      # Get DB version
      dbrev = _get_installed_ver(schema, session)
      dbsugarrev = _get_installed_ver(sugar_schema, session)
      if dbsugarrev == None:
          try:
              rc = _raw_run_sql_query("""
                         select count(*) AS cnt 
                         from pg_catalog.pg_proc p, pg_catalog.pg_namespace ns 
                         where ns.nspname='%s' and 
                               pronamespace=ns.oid and 
                               p.proname='sugar_version';
                        """ % sugar_schema.lower(),
                        False
                   )[0]['cnt']
          except:
              rc = 0
          if rc > 0:
              dbsugarrev = '0.4' # SUgAR's v0.4 came without a migration table.

      # Existing installation
      if dbrev==None or dbsugarrev==None:
        _error("Library not properly installed and cannot be upgraded. Use 'reinstall' instead.",False)
        raise Exception

      # version compare.
      rev_cmp=_cmp_versions(rev,dbrev)
      sugarrev_cmp=_cmp_versions(sugar_rev,dbsugarrev)
      if rev_cmp==0 and sugarrev_cmp==0:
        _info("Library already up-to-date. Use 'reinstall' for a fresh installation.", True)
        exit(0)
      if rev_cmp<0 or sugarrev_cmp<0:
        _info("DB version is newer than library version. Use 'reinstall' for a fresh install.", True)
        exit(0)

      # Language check
      _plpy_check(py_min_ver)
      '''PL/Perl installer is currently only available for GPDB, so we won't check this for HAWQ'''
      if(platform != 'hawq'):
          _plperl_check(perl_min_ver,perl_max_ver)

      # Write permission
      if not _schema_writable(schema, session):
        _error("PDL Tools schema not writable. Aborting installation.", False)
        raise Exception
      if not _schema_writable(sugar_schema, session):
        _error("SUgAR schema not writable. Aborting installation.", False)
        raise Exception
  
      # Granting Usage on Schemas
      _db_grant_usage(schema, session)
      _db_grant_usage(sugar_schema, session)
      
      # Create pdltools objects
      try:
          _db_create_objects(schema, platform, sugar_schema, madlib_schema,
                             dbrev,dbsugarrev, session)
      except SystemExit:
          raise
      except Exception, e:
          print e
          _error("Object creation failed. Aborting installation", False)
          raise Exception
      
      _info("PDL Tools %s installed successfully in %s schema." % (rev, schema.upper()), True)
      _info("SUgAR %s installed successfully in %s schema." % (sugar_rev, sugar_schema.upper()), True)
      _info("Installation completed successfully.",True)

    except SystemExit:
        raise
    except Exception, e:
        print "MSG:",e
        _error("PDL Tools installation failed. Installation aborted.", True)

if(__name__=='__main__'):
    main()
