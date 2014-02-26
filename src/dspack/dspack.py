'''
Simple Python based installer of DStools. In time this will involve to become more complex
but perhaps not quite as complex as madpack :-)
Srivatsan Ramanujam
<sramanujam@gopivotal.com>
28 Jan 2014

Usage:
======
python dspack.py [-s schema_name] -c <username>@<hostname>:<port>/<databasename>
'''
import argparse
import getpass

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
                description='MADlib package manager (' + rev + ')',
                argument_default=False,
                formatter_class=argparse.RawTextHelpFormatter,
                epilog="""Example:

  $ dspack install -s dstools -p -c gpadmin@mdw:5432/testdb

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
            + "If not provided default values will be derived for PostgerSQL and Greenplum:\n"
            + "- user: PGUSER or USER env variable or OS username\n"
            + "- pass: PGPASSWORD env variable or runtime prompt\n"
            + "- host: PGHOST env variable or 'localhost'\n"
            + "- port: PGPORT env variable or '5432'\n"
            + "- db: PGDATABASE env variable or OS username\n"
            )

    parser.add_argument('-s', '--schema', nargs=1, dest='schema',
                         metavar='SCHEMA', default='dstools',


                         help="Target schema for the database objects.")

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
    con_args = {}
    con_args['host'] = c_host + ':' + c_port
    con_args['database'] = c_db
    con_args['user'] = c_user
    con_args['password'] = c_pass

if(__name__=='__main__'):
    main()
