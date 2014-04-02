#!/bin/bash
## ======================================================================
##
## ======================================================================

BASEDIR=$(pwd)

export ENVIRONMENT_FILES="$1"

export PATH=${JAVA_HOME}/bin:$PATH
export PATH=.:~/bin:$PATH

export DBNAME=dstoolsdbtest
export DSTOOLSUSER=dstoolsuser
export DSTOOLSUSERPWD=123

if [ -n "${SCHEMA}" ]; then
    export SCHEMA_CMD="--schema ${SCHEMA}"
else
    export SCHEMA="madlib"
    export SCHEMA_CMD=""
fi

## ======================================================================
## 
## ======================================================================

cat > ${BASEDIR}/releng/conf/hosts.conf <<-EOF
	$(hostname -f)
EOF

## ======================================================================
## Function(s)
## ======================================================================

func_dbstop () {
	cat <<-EOF
	
		======================================================================
		Executing: Stopping DB (${PLATFORM_CONFIG})
		----------------------------------------------------------------------
		
	EOF
	
    gpstop -a
}

function set_environment () {

    export PLATFORM="greenplum"
    export PGPORT=60000

    export PLATFORM_CONFIG=$( basename ${envfile} .sh )
}

## ======================================================================
## Main script
## ======================================================================

echo "${ENVIRONMENT_FILES}" | grep GREENPLUM_4_2_X > /dev/null
if [ $? = 0 ]; then

    pushd ${BASEDIR}/releng
    
    export ENVIRONMENT_FILE=GREENPLUM_4_2_X.sh

    GPDB_INSTALLER_URL=${GPDB_INSTALLER_URL:=http://pulse.greenplum.com/browse/projects/GPDB-4_2-opt-l1/builds/success/downloads/rhel5_x86_64/Build%20GPDB/GPDB%20installer/greenplum-db-4.2-RHEL5-x86_64.zip} \
    RETRIEVE_INSTALLERS=true \
    SKIP_INSTALL=false \
    BASE_PORT=60000 \
    NUMBER_OF_SEGS_PER_NODE=2 \
    USE_GPPERFMON=false \
    ./test_gpdb.sh 4.2.X dev RHEL5-x86_64;

    cat >> /data/gpdbchina/4.2.X-build-dev/gpdb-data/master/gpdbqa-1/pg_hba.conf <<-EOF
		
		local    all         madlibuser      ident
		host     all         madlibuser      127.0.0.1/28    trust
		local    all         dstoolsuser     ident
		host     all         dstoolsuser     127.0.0.1/28    trust
		
	EOF

    (source ${BASEDIR}/releng/${ENVIRONMENT_FILE}; \
        gpstop -a; \
        generate_snapshot 1; \
    )

    popd
fi

##
## Ensure the environment file(s) exist
##

for envfile in ${ENVIRONMENT_FILES}; do
	if [ ! -f ${BASEDIR}/releng/${envfile} ]; then
	    echo "FATAL: environment file does not exist (${BASEDIR}/releng/${envfile})"
	    exit 1
	fi
done

for envfile in ${ENVIRONMENT_FILES}; do

    set_environment

    (
        source ${BASEDIR}/releng/${envfile}; 
	
		cat <<-EOF
		
			======================================================================
			Timestamp ........... : $( date )
			----------------------------------------------------------------------
			SCRIPT_OPTIONS ...... : $@
			PLATFORM ............ : ${PLATFORM}
			GPHOME .............. : ${GPHOME}
			PGPORT .............. : ${PGPORT}
			ENVIRONMENT FILE .... : ${envfile}
			SCHEMA .............. : ${SCHEMA}
			PYTHON .............. : $( python -V 2>&1 ) ($( which python ))
			PATH ................ : ${PATH}
			LD_LIBRARY_PATH ..... : ${LD_LIBRARY_PATH}
			======================================================================
		
		EOF
	)

done

cat <<-EOF
	
	======================================================================
	Executing: rm -rf build /tmp/madlib ~/.cmake /usr/local/greenplum-db ${LOGDIR}
	----------------------------------------------------------------------
	
EOF

rm -rf /usr/local/greenplum-db
rm -rf build ~/.cmake ${LOGDIR}

cat <<-EOF
	
	======================================================================
	Executing: func_dbstop
	----------------------------------------------------------------------
	
EOF

for envfile in ${ENVIRONMENT_FILES}; do

    set_environment

    (
        source ${BASEDIR}/releng/${envfile}

        rm -rf ${LOGDIR}
        mkdir -p ${LOGDIR}

        func_dbstop
    )

    sleep 5
    ps uxww | grep postgres | grep -v grep | grep -v bash

done

for envfile in ${ENVIRONMENT_FILES}; do

    set_environment

    (
        source ${BASEDIR}/releng/${envfile}

		cat <<-EOF
			
			======================================================================
			Executing: RESTORE from snapshot (${PLATFORM_CONFIG})
			----------------------------------------------------------------------
			
		EOF
		
		restore_snapshot 1

		cat <<-EOF
			
			======================================================================
			Executing: GPSTART or GPINITSYSTEM (${PLATFORM_CONFIG})
			----------------------------------------------------------------------
			
		EOF
		
		cat >> ${MASTER_DATA_DIRECTORY}/pg_hba.conf <<-EOF
		
			local    all         madlibuser      ident
			host     all         madlibuser      127.0.0.1/28    trust
			local    all         dstoolsuser     ident
			host     all         dstoolsuser     127.0.0.1/28    trust
		
		EOF

		gpstart -a
		
		sleep 5

		ps uxww | grep postgres | grep -v grep | grep -v bash

		cat <<-EOF
			
			======================================================================
			Executing: CREATEDB ${DBNAME}
			----------------------------------------------------------------------
			
		EOF
		
		createdb ${DBNAME}
		
		cat <<-EOF
			
			======================================================================
			Executing: select * from pg_database
			----------------------------------------------------------------------
			
		EOF
		
		psql ${DBNAME} -c 'select * from pg_database'
		
		cat <<-EOF
			
			======================================================================
			Executing: select version()
			----------------------------------------------------------------------
			
		EOF
		
		psql ${DBNAME} -c 'select version()'
		
		cat <<-EOF
			
			======================================================================
			Executing: psql ${DBNAME} -c 'CREATE LANGUAGE plpythonu'
			----------------------------------------------------------------------
			
		EOF
		
		psql ${DBNAME} -c 'CREATE LANGUAGE plpythonu'
		
		if [ "${PLATFORM}" = "postgres" ]; then
			cat <<-EOF
				
				======================================================================
				Executing: psql ${DBNAME} -c 'CREATE LANGUAGE plpgsql'
				----------------------------------------------------------------------
				
			EOF
			
			psql ${DBNAME} -c 'CREATE LANGUAGE plpgsql'
		fi
		
        func_dbstop
    )

done

for envfile in ${ENVIRONMENT_FILES}; do
    source ${BASEDIR}/releng/${envfile}
    echo "======================================================================"
    echo "Building DSTools"
    echo "======================================================================"
    mkdir build
    cd build
    cmake ..
    if [ $? != 0 ]; then
        echo "FATAL: cmake failed"
        exit 1
    fi
    make package
    if [ $? != 0 ]; then
        echo "FATAL: make package failed"
        exit 1
    fi
    make gppkg
    if [ $? != 0 ]; then
        echo "FATAL: make gppkg failed"
        exit 1
    fi

	cat <<-EOF
		
		======================================================================
		Executing: FIRE UP THE ENGINE(s) (${PLATFORM_CONFIG})
		----------------------------------------------------------------------
		
	EOF
	
	gpstart -a
	
	sleep 5

	ps uxww | grep postgres | grep -v grep | grep -v bash


	cat <<-EOF
		
		======================================================================
		Executing: psql ${DBNAME} -c "CREATE USER ${DSTOOLSUSER} WITH PASSWORD '${DSTOOLSUSERPWD}' CREATEUSER"
		----------------------------------------------------------------------
		
	EOF
	
	psql ${DBNAME} -c "CREATE USER ${DSTOOLSUSER} WITH PASSWORD '${DSTOOLSUSERPWD}' CREATEUSER"
	
	cat <<-EOF
		
		======================================================================
		Executing: psql ${DBNAME} -c "GRANT ALL PRIVILEGES ON DATABASE ${DBNAME} to ${DSTOOLSUSER}"
		----------------------------------------------------------------------
		
	EOF
	
	psql ${DBNAME} -c "GRANT ALL PRIVILEGES ON DATABASE ${DBNAME} to ${DSTOOLSUSER}"
	
	cat <<-EOF
		
		======================================================================
		Executing: gppkg -i deploy/gppkg/4.2/dstools*.gppkg
		----------------------------------------------------------------------
		
	EOF
	
    gppkg -i deploy/gppkg/4.2/dstools*.gppkg
    if [ $? != 0 ]; then
        echo "FATAL: gppkg installation failed"
        func_dbstop
        exit 1
    fi

    DSPACK=$GPHOME/dstools/bin/dspack
		
	cat <<-EOF
		
		======================================================================
		Executing: ${DSPACK} --verbose --conn ${DSTOOLSUSER}/${DSTOOLSUSERPWD}@localhost:${PGPORT}/${DBNAME} ${SCHEMA_CMD} install
		----------------------------------------------------------------------
		
	EOF
		
    ${DSPACK} --verbose --conn ${DSTOOLSUSER}/${DSTOOLSUSERPWD}@localhost:${PGPORT}/${DBNAME} ${SCHEMA_CMD} install 2>&1 | tee dstools_install.out
    RETURN=${PIPESTATUS[0]}
	if [ "$RETURN" != 0 ]; then
		cat <<-EOF
			######################################################################
			FAILED Executing: dspack installation failed
			######################################################################
		
		EOF
    fi

	cat <<-EOF
		
		======================================================================
		Executing: ${DSPACK} --verbose --conn ${DSTOOLSUSER}/${DSTOOLSUSERPWD}@localhost:${PGPORT}/${DBNAME} ${SCHEMA_CMD} install-check
		----------------------------------------------------------------------
		
	EOF
		
    ${DSPACK} --verbose --conn ${DSTOOLSUSER}/${DSTOOLSUSERPWD}@localhost:${PGPORT}/${DBNAME} ${SCHEMA_CMD} install-check 2>&1 | tee dstools_install-check.out
    RETURN=${PIPESTATUS[0]}
	if [ "$RETURN" != 0 ]; then
		cat <<-EOF
			######################################################################
			FAILED Executing: dspack install-check failed
			######################################################################
		
		EOF
    fi

	cat <<-EOF
	
	======================================================================
	Executing: func_dbstop
	----------------------------------------------------------------------
	
	EOF
	func_dbstop

done
