#!/bin/bash
## ======================================================================
## PDL Tools build script
## ----------------------------------------------------------------------
## Basic steps
##
##   o Retrieve latest 4.2 installer
##   o Deploy new cluster
##   o Perform PDL Tools build process
##   o Perform PDL Tools packaging processes (rpm & gppkg)
##   o Use gppkg to install PDL Tools
##   o Use pdlpack to install PDL Tools
##   o Execute install-check tests
##   o (optionally) Publish artifacts to:
##        http://build-prod.dh.greenplum.com/releases/dstools
## ======================================================================

BASEDIR=$(pwd)

export ENVIRONMENT_FILES="$1"

export PATH=${JAVA_HOME}/bin:$PATH
export PATH=.:~/bin:$PATH

export DBNAME=dstoolsdbtest
export PDLTOOLSUSER=dstoolsuser
export PDLTOOLSUSERPWD=123
PDLTOOLS_VERSION=$( awk '{print $2}' ${BASEDIR}/src/config/Version.yml )

if [ -n "${SCHEMA}" ]; then
    export SCHEMA_CMD="--schema ${SCHEMA}"
else
    export SCHEMA="pdltools"
    export SCHEMA_CMD=""
fi

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
	Executing: rm -rf build ~/.cmake /usr/local/greenplum-db ${LOGDIR}
	----------------------------------------------------------------------
	
EOF

rm -rf /usr/local/greenplum-db
rm -rf build ~/.cmake ${LOGDIR}

for envfile in ${ENVIRONMENT_FILES}; do
    source ${BASEDIR}/releng/${envfile}

	cat <<-EOF
		
		======================================================================
		Building PDL Tools
		----------------------------------------------------------------------
		
	EOF

    rm -rf build
    mkdir build

    pushd build
    cmake .. ${CMAKE_OPTS}
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

    make doc
    if [ $? != 0 ]; then
        echo "FATAL: make doc failed"
        exit 1
    fi
    pushd doc/user
    tar zcf pdltools-${PDLTOOLS_VERSION}-${PULSE_BUILD_NUMBER}-html.tgz html
    ln -s pdltools-${PDLTOOLS_VERSION}-${PULSE_BUILD_NUMBER}-html.tgz pdltools-html.tgz
    popd

    # pushd doc/user/latex
    # make pdf
    # if [ $? != 0 ]; then
    #     echo "FATAL: make pdf failed"
    #     exit 1
    # fi
    # popd

    GPDB_VERSION=`basename $(ls -d deploy/gppkg/4*)`
    RPM=$(ls pdltools-*.rpm)
    RPM_NEW_NAME=`echo ${RPM} | sed -e "s|pdltools-\(.*\)-Linux.rpm|pdltools-\1-gpdb${GPDB_VERSION}-Linux.rpm|g"`
    mv -v ${RPM} ${RPM_NEW_NAME}

	cat <<-EOF
		
		======================================================================
		Executing: FIRE UP THE ENGINE(s) (${PLATFORM_CONFIG})
		----------------------------------------------------------------------
		
	EOF

    set_environment

    source ${BASEDIR}/releng/${envfile}

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

	cat <<-EOF
		
		======================================================================
		Executing: psql ${DBNAME} -c "CREATE USER ${PDLTOOLSUSER} WITH PASSWORD '${PDLTOOLSUSERPWD}' CREATEUSER"
		----------------------------------------------------------------------
		
	EOF
	
	psql ${DBNAME} -c "CREATE USER ${PDLTOOLSUSER} WITH PASSWORD '${PDLTOOLSUSERPWD}' CREATEUSER"
	
	cat <<-EOF
		
		======================================================================
		Executing: psql ${DBNAME} -c "GRANT ALL PRIVILEGES ON DATABASE ${DBNAME} to ${PDLTOOLSUSER}"
		----------------------------------------------------------------------
		
	EOF
	
	psql ${DBNAME} -c "GRANT ALL PRIVILEGES ON DATABASE ${DBNAME} to ${PDLTOOLSUSER}"
	
	cat <<-EOF
		
		======================================================================
		Executing: gppkg -i deploy/gppkg/*/pdltools*.gppkg
		----------------------------------------------------------------------
		
	EOF
	
    gppkg -i deploy/gppkg/*/pdltools*.gppkg
    if [ $? != 0 ]; then
        echo "FATAL: gppkg installation failed"
        func_dbstop
        exit 1
    fi

    PDLPACK=$GPHOME/pdltools/bin/pdlpack
		
	cat <<-EOF
		
		======================================================================
		Executing: ${PDLPACK} --verbose --conn ${PDLTOOLSUSER}/${PDLTOOLSUSERPWD}@localhost:${PGPORT}/${DBNAME} ${SCHEMA_CMD} install
		----------------------------------------------------------------------
		
	EOF
		
    ${PDLPACK} --verbose --conn ${PDLTOOLSUSER}/${PDLTOOLSUSERPWD}@localhost:${PGPORT}/${DBNAME} ${SCHEMA_CMD} install 2>&1 | tee pdltools_install.out
    RETURN=${PIPESTATUS[0]}
	if [ "$RETURN" != 0 ]; then
		cat <<-EOF
			######################################################################
			FAILED Executing: pdlpack installation failed
			######################################################################
		
		EOF
    fi

	cat <<-EOF
		
		======================================================================
		Executing: ${PDLPACK} --verbose --conn ${PDLTOOLSUSER}/${PDLTOOLSUSERPWD}@localhost:${PGPORT}/${DBNAME} ${SCHEMA_CMD} --tmpdir ${BASEDIR} install-check
		----------------------------------------------------------------------
		
	EOF
		
    ${PDLPACK} --verbose --conn ${PDLTOOLSUSER}/${PDLTOOLSUSERPWD}@localhost:${PGPORT}/${DBNAME} ${SCHEMA_CMD} --tmpdir ${BASEDIR} install-check 2>&1 | tee pdltools_install-check.out
    RETURN=${PIPESTATUS[0]}
	if [ "$RETURN" != 0 ]; then
		cat <<-EOF
			######################################################################
			FAILED Executing: pdlpack install-check failed
			######################################################################
		
		EOF
    fi

	func_dbstop

    popd

done

if [ "${PUBLISH}" = "true" ]; then

    RELEASE_DIR=/var/www/html/releases/dstools/${PDLTOOLS_VERSION}-${PULSE_BUILD_NUMBER}

	cat <<-EOF
	
		======================================================================
		Executing: Publish artifacts: http://build-prod.dh.greenplum.com/releases/dstools/${PDLTOOLS_VERSION}-${PULSE_BUILD_NUMBER}
		----------------------------------------------------------------------
	
	EOF

    ssh build@build-prod.dh.greenplum.com mkdir -p ${RELEASE_DIR}
    scp ${BASEDIR}/build/deploy/gppkg/*/pdltools*.gppkg ${BASEDIR}/build/pdltools-*Linux.rpm build@build-prod.dh.greenplum.com:${RELEASE_DIR}
    scp ${BASEDIR}/build/doc/user/pdltools-${PDLTOOLS_VERSION}-${PULSE_BUILD_NUMBER}-html.tgz build@build-prod.dh.greenplum.com:${RELEASE_DIR}
    ssh build@build-prod.dh.greenplum.com ls -al ${RELEASE_DIR}

	cat <<-EOF
	
		======================================================================
	EOF
else
	cat <<-EOF
	
		======================================================================
		Publishing artifacts is disabled.
		======================================================================
	EOF
fi

exit 0
