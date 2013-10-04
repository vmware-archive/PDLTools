## ======================================================================
## Sample environnent setup for OSX
## ======================================================================

KERNEL_NAME=$( uname -s )
if [ "${KERNEL_NAME}" = "Darwin" ]; then

    ## Use OSX 4.4.2 compiler built for OS X 10.6+
    source /opt/gcc_env-osx106.sh 

    ## Point to GPDB environment
    source /Users/espine1/dev/cdb2/main/greenplum-db-devel/greenplum_path.sh 
else
    ## Point to GPDB environment
    source /home/espine1/dev/cdb2/r42/greenplum-db-devel/greenplum_path.sh 
fi
