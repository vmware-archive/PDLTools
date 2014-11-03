#!/bin/bash
## ======================================================================
## ======================================================================

check_deployment() {
 	psql --pset=pager -p ${MASTER_PORT} template1 -c "select version();"
    RETURN=$?
    check_return

    psql --pset=pager -p ${MASTER_PORT} template1 -c "select * from gp_segment_configuration;"
    RETURN=$?
    check_return

    psql --pset=pager -p ${MASTER_PORT} template1 -c "\l+"
    RETURN=$?
    check_return

	createdb gptest
    RETURN=$?
    check_return

    psql --pset=pager -p ${MASTER_PORT} template1 -c "\l+"
    RETURN=$?
    check_return

    run_cmd "gpssh --version"

	run_cmd "gpstate -s"

	run_cmd "gpstate -Q"

	run_cmd "gpstate -f"

	run_cmd "gpstate -i"

    run_cmd "gpstop -a -l ${LOGDIR}"

    run_cmd "gpstart -a -l ${LOGDIR}"
}

check_return_code(){
    RETURN=$1
    check_return
}

run_cmd(){
    cmd=$1
    cat <<-EOF

		======================================================================
		Timestamp ........ : `date`
		Running command .. : ${cmd}
		======================================================================
		
	EOF
    ${cmd}
    check_return_code $?
}

check_return(){
    if [ "${RETURN}" = "0" ]; then
        cat <<-EOF

			----------------------------------------------------------------------
			Timestamp ........ : `date`
			Command returned successful code (${RETURN})
			----------------------------------------------------------------------
			
		EOF
    else
        cat <<-EOF

			######################################################################
			Timestamp ........ : `date`

			                               WARNING

			Command returned unsuccessful code (${RETURN})
			######################################################################

		EOF
        exit 1
    fi
}

install_gpdb() {
    [ -d ${GPDB_INSTALL_DIR} ] && rm -rf ${GPDB_INSTALL_DIR}

    pushd ${LOGDIR} > /dev/null
    ${BASE_DIR}/scripts/runGPDBInstaller.py \
        --pause 30 \
        --installerbin ${BASE_DIR}/product/${GPDB_INSTALLER_BIN} \
        --path ${GPDB_INSTALL_DIR}
    popd > /dev/null
}

curl_installer(){

    [ -f `basename $1` ] && rm -f `basename $1`
    [ -f `basename $1 .zip`.bin ] && rm -f `basename $1 .zip`.bin

    echo $1 | grep -q -i pulse
    if [ $? = 0 ]; then
        CURL_CREDENTIALS="-L"
    fi

    cat <<-EOF

		======================================================================
		Timestamp ........ : `date`
		Running command .. : curl $1
		======================================================================
		
	EOF
	curl ${CURL_CREDENTIALS} \
         --silent \
         --output `basename $1` \
         $1

    RETURN=$?
    check_return
}

setup_deployment() {
    echo "Removing any previous segment node data directory: ${DATA_DIR}"
    
	if [ "${ENABLE_MIRRORS}" = "false" ]; then
        echo "Creating segment node data directories: ${DATA_DIR}/gpdb-data/primary"
    else
        echo "Creating segment node data directories: ${DATA_DIR}/gpdb-data/primary ${DATA_DIR}/gpdb-data/mirror"
    fi

    for host in $( cat ${HOSTS_CONF} ); do
        COUNTER=0
        while [  $COUNTER -lt ${NUMBER_OF_SEGS_PER_NODE} ]; do
            ssh ${host} "rm -rf ${DATA_DIR}/gpdb-data/primary${COUNTER}; mkdir -p ${DATA_DIR}/gpdb-data/primary${COUNTER}"
            if [ "${ENABLE_MIRRORS}" != "false" ]; then
                ssh ${host} "rm -rf ${DATA_DIR}/gpdb-data/mirror${COUNTER}; mkdir -p ${DATA_DIR}/gpdb-data/mirror${COUNTER}"
            fi
            let COUNTER=COUNTER+1
        done
    done

	rm -f ${CLUSTER_CONF}${MIRROR_EXTENSION}

	sed -e "s|%HOSTSCONF%|${HOSTS_CONF}|" \
	    -e "s|%MASTER_HOSTNAME%|${HOSTNAME}|" \
	    -e "s|%MASTER_DATA_DIRECTORY_BASE%|${MASTER_DATA_DIRECTORY_BASE}|" \
	    -e "s|%MASTER_PORT%|${MASTER_PORT}|" \
	    -e "s|%PORT_BASE%|${PORT_BASE}|" \
	    -e "s|%MIRROR_PORT_BASE%|${MIRROR_PORT_BASE}|" \
	    -e "s|%MIRROR_REPLICATION_PORT_BASE%|${MIRROR_REPLICATION_PORT_BASE}|" \
	    -e "s|%REPLICATION_PORT_BASE%|${REPLICATION_PORT_BASE}|" \
	    -e "s|%SEG_PREFIX%|${SEG_PREFIX}|" \
	    ${CLUSTER_CONF_TEMPLATE} > ${CLUSTER_CONF}

	if [ "${GPDB_VERSION}" = "gpsql" ] || [ "${GPDB_VERSION}" = "hawq" ]; then
		
		DATE=$( date +%Y%m%dt%H%M%S )

		HDFS_HOST=${HDFS_HOST:=localhost:8020}
        if [ "${GPDB_BUILD_VERSION}" == "build-1.2" ] && [ ! -z "${PHD_20_HOST}" ]; then
            HDFS_HOST=${PHD_20_HOST}
        elif [ "${GPDB_BUILD_VERSION}" == "build-1.3" ] && [ ! -z "${PHD_22_HOST}" ]; then
            HDFS_HOST=${PHD_22_HOST}
        fi
        echo "version: ${GPDB_BUILD_VERSION}, HDFS_HOST: ${HDFS_HOST}"
		
		cat >> ${CLUSTER_CONF} <<-EOF
		        # HDFS Support 
		        DFS_NAME=hdfs
		        DFS_URL=${HDFS_HOST}/gpsql/gpdb${DATE}
		        DATABASE_NAME=hdfs
		EOF
		
	fi

	cat >> ${CLUSTER_CONF} <<-EOF

		## ======================================================================
		## File system location(s) where primary segment data directories 
		## will be created. The number of locations in the list dictate
		## the number of primary segments per physical host.
		## ======================================================================
	
		declare -a DATA_DIRECTORY=( \\
	EOF
	
	COUNTER=0
	while [  $COUNTER -lt ${NUMBER_OF_SEGS_PER_NODE} ]; do
		cat >> ${CLUSTER_CONF} <<-EOF
		                            ${DATA_DIR}/gpdb-data/primary${COUNTER} \\
		EOF
	    let COUNTER=COUNTER+1
	done

	cat >> ${CLUSTER_CONF} <<-EOF
		                          )

	EOF

	if [ "${ENABLE_MIRRORS}" = "false" ]; then
        MIRROR_EXTENSION=.mirrors
        rm -f ${CLUSTER_CONF}${MIRROR_EXTENSION}
    fi
    
	cat >> ${CLUSTER_CONF}${MIRROR_EXTENSION} <<-EOF
		################################################
		#### OPTIONAL MIRROR PARAMETERS
		################################################
		
		#### Base number by which mirror segment port numbers 
		#### are calculated.
		MIRROR_PORT_BASE=%MIRROR_PORT_BASE%
		
		#### Base number by which primary file replication port 
		#### numbers are calculated.
		REPLICATION_PORT_BASE=%REPLICATION_PORT_BASE%
		
		#### Base number by which mirror file replication port 
		#### numbers are calculated. 
		MIRROR_REPLICATION_PORT_BASE=%MIRROR_REPLICATION_PORT_BASE%
		
		## ======================================================================
		## File system location(s) where mirror segment data directories 
		## will be created. The number of locations in the list dictate
		## the number of primary segments per physical host.
		## ======================================================================
	
		declare -a MIRROR_DATA_DIRECTORY=( \\
	EOF

	sed -e "s|%MIRROR_PORT_BASE%|${MIRROR_PORT_BASE}|" \
	    -e "s|%MIRROR_REPLICATION_PORT_BASE%|${MIRROR_REPLICATION_PORT_BASE}|" \
	    -e "s|%REPLICATION_PORT_BASE%|${REPLICATION_PORT_BASE}|" \
	    -i ${CLUSTER_CONF}${MIRROR_EXTENSION}

	COUNTER=0
	while [  $COUNTER -lt ${NUMBER_OF_SEGS_PER_NODE} ]; do
		cat >> ${CLUSTER_CONF}${MIRROR_EXTENSION} <<-EOF
		                                   ${DATA_DIR}/gpdb-data/mirror${COUNTER} \\
		EOF
	    let COUNTER=COUNTER+1
	done

	cat >> ${CLUSTER_CONF}${MIRROR_EXTENSION} <<-EOF
		                                 )
	EOF

    rm -f ${CLUSTER_CONF}${MIRROR_EXTENSION}.datadirs
	
	COUNTER=0
	while [  $COUNTER -lt ${NUMBER_OF_SEGS_PER_NODE} ]; do
		cat >> ${CLUSTER_CONF}${MIRROR_EXTENSION}.datadirs <<-EOF
			${DATA_DIR}/gpdb-data/mirror${COUNTER}
		EOF
	    let COUNTER=COUNTER+1
	done
}

## ======================================================================
##
## Courtesy - http://stevemorin.blogspot.com/2007/10/bash-get-self-directory-trick.html
## Updated to run on rhel3 (kite12)
##

script_path="$(cd $(dirname $0); pwd -P)/$(basename $0)"

[[ ! -f "$script_path" ]] && script_path="$(cd $(/usr/bin/dirname "$0"); pwd -P)/$(basename "$0")"
[[ ! -f "$script_path" ]] && script_path="" && echo 'No full path to running script found!' && exit 1

script_dir="${script_path%/*}"

GPDB_VERSION=$1
GPDB_BUILD_VERSION=build-$2
GPDB_PLATFORM=$3
GPDB_INSTALLERS=$4

if [ ${GPDB_PLATFORM} = "OSX-i386" ]; then
shell
    PLATFORM=osx105_x86
elif [ ${GPDB_PLATFORM} = "RHEL5-i386" ]; then
    PLATFORM=rhel5_x86_32
elif [ ${GPDB_PLATFORM} = "RHEL5-x86_64" ]; then
    PLATFORM=rhel5_x86_64
elif [ ${GPDB_PLATFORM} = "SOL-x86_64" ]; then
    PLATFORM=sol10_x86_64
elif [ ${GPDB_PLATFORM} = "SuSE10-x86_64" ]; then
    PLATFORM=suse10_x86_64
fi

echo ${GPDB_VERSION} | grep 4 > /dev/null 2>&1
if [ $? = 0 ]; then
    CDBFASTHOME=/home/espine1/perforce/cdbfast/Release-4_0-branch
else
    CDBFASTHOME=/home/espine1/perforce/cdbfast/main
fi

USE_GPPERFMON=${USE_GPPERFMON:-false}
NUMBER_OF_SEGS_PER_NODE=${NUMBER_OF_SEGS_PER_NODE:-4}

RETRIEVE_INSTALLERS=${RETRIEVE_INSTALLERS:-true}

HOSTNAME=`hostname`
BASE_DIR=${script_dir}
PATH=${BASE_DIR}/tools/bin:${PATH}

DATA_DIR="/data/$LOGNAME/${GPDB_VERSION}-${GPDB_BUILD_VERSION}"

## PACKAGES_URL=http://intranet.greenplum.com/internal-builds/greenplum-db/rc/${GPDB_VERSION}-${GPDB_BUILD_VERSION}
PACKAGES_URL=http://build-prod.sanmateo.greenplum.com/internal-builds/greenplum-db/rc/${GPDB_VERSION}-${GPDB_BUILD_VERSION}

if [ -n "${GPDB_INSTALLER_URL}" ]; then
    CURL_CREDENTIALS="-L --user gpdb:gpreleng"
	GPDB_INSTALLER=`basename ${GPDB_INSTALLER_URL}`
    PACKAGES_URL=`dirname ${GPDB_INSTALLER_URL}`
else
    CURL_CREDENTIALS="-L --user gpreleng:c98582d61c776c288be83e3154fedee5"
    if [ "${SNE_INSTALL}" != "true" ]; then
        GPDB_INSTALLER=greenplum-db-${GPDB_VERSION}-${GPDB_BUILD_VERSION}-${GPDB_PLATFORM}.zip
    else
        GPDB_INSTALLER=greenplum-db-${GPDB_VERSION}-${GPDB_BUILD_VERSION}-SingleNodeEdition-${GPDB_PLATFORM}.zip
    fi
fi

if [ -n "${GPPERFMON_INSTALLER_URL}" ]; then
	GPPERFMON_INSTALLER=`basename ${GPPERFMON_INSTALLER_URL}`
    GPPERFMON_INSTALLER_URL=${GPPERFMON_INSTALLER_URL}
else
    GPPERFMON_INSTALLER="greenplum-perfmon-web-${GPDB_VERSION}-${GPDB_BUILD_VERSION}-${GPDB_PLATFORM}.zip"
    GPPERFMON_INSTALLER_URL="${PACKAGES_URL}/${GPPERFMON_INSTALLER}"
fi

LOGDIR=${DATA_DIR}/logs
GPDB_INSTALL_DIR=${DATA_DIR}/gpdb
GPDB_INSTALL_DATA_DIR=${DATA_DIR}/gpdb-data
GPPERFMON_INSTALL_DIR=${DATA_DIR}/gpperfmon

[ ! -d ${LOGDIR} ] && mkdir -p ${LOGDIR}

CDBUNIT_HOME=${BASE_DIR}/cdbunit

CLUSTER_CONF_TEMPLATE=${BASE_DIR}/conf/cluster.conf.template
CLUSTER_CONF=${BASE_DIR}/conf/cluster-${GPDB_VERSION}-${GPDB_BUILD_VERSION}.conf
HOSTS_CONF=${BASE_DIR}/conf/hosts.conf
BASE_PORT=${BASE_PORT:-40500}
MASTER_PORT=`expr ${BASE_PORT} + 0`
PORT_BASE=`expr ${BASE_PORT} + 200`
MIRROR_PORT_BASE=`expr ${BASE_PORT} + 400`
MIRROR_REPLICATION_PORT_BASE=`expr ${BASE_PORT} + 600`
REPLICATION_PORT_BASE=`expr ${BASE_PORT} + 800`
SEG_PREFIX=gpdbqa

GPDB_INSTALLER_BIN=`basename ${GPDB_INSTALLER} .zip`.bin
GPPERFMON_INSTALLER_BIN=`basename ${GPPERFMON_INSTALLER} .zip`.bin

if [ "${RETRIEVE_INSTALLERS}" = "true" ]; then
    [ ! -d ${BASE_DIR}/product ] && mkdir -p ${BASE_DIR}/product

    if [ "${USE_GPPERFMON}" = "true" ]; then
        if [ "${RETRIEVE_INSTALLERS}" = "true" ]; then
            pushd ${BASE_DIR}/product > /dev/null
            curl_installer ${GPPERFMON_INSTALLER_URL}
            unzip ${GPPERFMON_INSTALLER} ${GPPERFMON_INSTALLER_BIN}
            popd > /dev/null
        fi
    fi

    pushd ${BASE_DIR}/product > /dev/null
    curl_installer ${PACKAGES_URL}/${GPDB_INSTALLER}
    CURL_CREDENTIALS="-L"
    curl_installer http://pulse-releng.greenplum.com/browse/projects/GPDB-main-opt-l1/builds/success/downloads/${PLATFORM}/Build%20GPDB/QAUtils/qautils-${GPDB_PLATFORM}.tar.gz
    unzip ${GPDB_INSTALLER} ${GPDB_INSTALLER_BIN}
    popd >/dev/null

    if [ -n "${DOWNLOAD_ONLY}" ]; then
        exit 0
    fi
fi

export MASTER_DATA_DIRECTORY=${GPDB_INSTALL_DATA_DIR}/master/${SEG_PREFIX}-1
export PGPORT=${MASTER_PORT}

cat > ${BASE_DIR}/env-${GPDB_VERSION}-${GPDB_BUILD_VERSION}.sh <<-EOF
	## ======================================================================
	## created: `date`
	## ======================================================================
	
	export MASTER_DATA_DIRECTORY=${MASTER_DATA_DIRECTORY}
	export PGPORT=${PGPORT}
	export LOGDIR=${LOGDIR} 

	## --------------------

	alias gpssh="gpssh -f ${HOSTS_CONF}"
	alias sdw="sdwnodes -f ${HOSTS_CONF}"

	## --------------------

	alias gpinit="gpinitsystem -a -c ${CLUSTER_CONF} -l ${LOGDIR}"
	alias gpdel="gpdeletesystem --master-data-directory ${MASTER_DATA_DIRECTORY} -l ${LOGDIR}"
	alias rmdatadirs="sdwnodes -f ${HOSTS_CONF} rm -rf ${DATA_DIR}/gpdb-data/*/*; rm -rf ${DATA_DIR}/gpdb-data/*/*"

	alias mdd="cd ${MASTER_DATA_DIRECTORY}"
	alias gpdb="cd ${GPDB_INSTALL_DIR}"

	alias cdbfast="cd ${CDBFASTHOME}"

	alias gpsc='psql --pset=pager -c "select * from gp_segment_configuration" template1'
	alias gpch='psql --pset=pager -c "select * from gp_configuration_history" template1'
	alias gpmm='psql --pset=pager -c "select * from gp_master_mirroring" template1'
	alias pgsa='psql --pset=pager -c "select * from pg_stat_activity" template1'
	alias gpdbver='psql --pset=pager -c "select version()" template1'
	alias gpver='gpssh --version'
	alias gpsql='psql --pset=pager template1'
	alias gpmainton="export PGOPTIONS='-c gp_session_role=utility' psql"
	alias gpmaintoff="export PGOPTIONS='-c gp_session_role=utility' psql"
	alias psql='psql --pset=pager'

	alias gpchkmirrors="gpcheckmirrorseg.pl -connect \"-p $PGPORT template1\" \\
	                                        -ignore 'wet_execute.tbl' \\
	                                        -ignore 'gp_dump' \\
	                                        -ignore 'core' \\
	                                        -ignore 'pg_changetracking' \\
	                                        -ignore 'pg_xlog' \\
	                                        -parallel=true \\
	                                        -fixfile fixfile.txt"

	function generate_snapshot() {
	    
	    if [ -n "\${1}" ]; then
	        gpssh -f ${HOSTS_CONF} \\
	            rsync -az --delete \\
	                  ${DATA_DIR}/gpdb-data/ \\
	                  ${DATA_DIR}/gpdb-data.\${1}/
	    
	        gpssh -f ${HOSTS_CONF} \\
	            diff -r \\
	                  ${DATA_DIR}/gpdb-data/ \\
	                  ${DATA_DIR}/gpdb-data.\${1}/
	    
	        rsync -az --delete \\
	              ${DATA_DIR}/gpdb-data/ \\
	              ${DATA_DIR}/gpdb-data.\${1}/

	        diff -r \\
	              ${DATA_DIR}/gpdb-data/ \\
	              ${DATA_DIR}/gpdb-data.\${1}/

	        gpssh -f ${HOSTS_CONF} \\
	            rsync -az --delete \\
	                  ${DATA_DIR}/gpdb/ \\
	                  ${DATA_DIR}/gpdb.\${1}/
	    
	        gpssh -f ${HOSTS_CONF} \\
	            diff -r \\
	                  ${DATA_DIR}/gpdb/ \\
	                  ${DATA_DIR}/gpdb.\${1}/
	    
	        rsync -az --delete \\
	              ${DATA_DIR}/gpdb/ \\
	              ${DATA_DIR}/gpdb.\${1}/

	        diff -r \\
	              ${DATA_DIR}/gpdb/ \\
	              ${DATA_DIR}/gpdb.\${1}/
	    else
	        echo "Snapshot id not specified"
	    fi
	}

	function restore_snapshot() {
	    
	    if [ -n "\${1}" ]; then
	        gpssh -f ${HOSTS_CONF} \\
	            rsync -az --delete \\
	                  ${DATA_DIR}/gpdb-data.\${1}/ \\
	                  ${DATA_DIR}/gpdb-data/
	    
	        gpssh -f ${HOSTS_CONF} \\
	            diff -r  \\
	                  ${DATA_DIR}/gpdb-data.\${1}/ \\
	                  ${DATA_DIR}/gpdb-data/
	    
	        rsync -az --delete \\
	              ${DATA_DIR}/gpdb-data.\${1}/ \\
	              ${DATA_DIR}/gpdb-data/

	        diff -r \\
	              ${DATA_DIR}/gpdb-data.\${1}/ \\
	              ${DATA_DIR}/gpdb-data/

	        gpssh -f ${HOSTS_CONF} \\
	            rsync -az --delete \\
	                  ${DATA_DIR}/gpdb.\${1}/ \\
	                  ${DATA_DIR}/gpdb/
	    
	        gpssh -f ${HOSTS_CONF} \\
	            diff -r  \\
	                  ${DATA_DIR}/gpdb.\${1}/ \\
	                  ${DATA_DIR}/gpdb/
	    
	        rsync -az --delete \\
	              ${DATA_DIR}/gpdb.\${1}/ \\
	              ${DATA_DIR}/gpdb/

	        diff -r \\
	              ${DATA_DIR}/gpdb.\${1}/ \\
	              ${DATA_DIR}/gpdb/
	    else
	        echo "Snapshot id not specified"
	    fi
	}

	function gpseginfo(){
	    psql --pset pager \\
	         --dbname template1 \\
	         --command "SELECT dbid,
	                           content,
	                           role,
	                           preferred_role,
	                           mode,
	                           status,
	                           hostname,
	                           address,
	                           port,
	                           replication_port,
	                           fselocation AS datadir,
	                           san_mounts
	                      FROM gp_segment_configuration,
	                           pg_filespace_entry,
	                           pg_catalog.pg_filespace fs
	                     WHERE fsefsoid = fs.oid AND
	                           fsname='pg_system' AND
	                           gp_segment_configuration.dbid=pg_filespace_entry.fsedbid
	                  ORDER BY content,
	                           preferred_role desc"
	}

	function gpdatadirsinfo(){
	    psql --pset pager \\
	         --dbname template1 \\
	         --command 'SELECT gscp.content,
	                           gscp.hostname AS phostname,
	                           gscp.address AS paddress,
	                           fep.fselocation AS ploc,
	                           gscm.hostname AS mhostname,
	                           gscm.address AS maddress,
	                           fem.fselocation AS mloc,
	                           pfs.oid fsoid,
	                           pfs.fsname,
	                           gscp.mode,
	                           gscp.status
	                      FROM gp_segment_configuration AS gscp,
	                           pg_filespace_entry AS fep,
	                           gp_segment_configuration AS gscm,
	                           pg_filespace_entry AS fem,
	                           pg_filespace AS pfs
	                     WHERE fep.fsedbid=gscp.dbid AND
	                           fem.fsedbid=gscm.dbid AND
	                           fem.fsefsoid = fep.fsefsoid AND
	                           gscp.content = gscm.content AND
	                           gscp.role = \$q\$p\$q\$ AND
	                           gscm.role = \$q\$m\$q\$ AND
	                           pfs.oid = fep.fsefsoid
	                  ORDER BY gscp.dbid, content'
	}

	function check_config() {
	    psql --pset pager \\
	         --dbname template1 \\
	         --command "-- principle 1: primary is always up
	                    SELECT *
	                      FROM gp_segment_configuration
	                     WHERE role = 'p' AND
	                           status = 'd'"

	    psql --pset pager \\
	         --dbname template1 \\
	         --command "-- principle 2: mirror is down -> primary needs to be in change tracking
	                    SELECT p.content,
	                           p.dbid AS p_dbid,
	                           m.dbid AS m_dbid,
	                           p.role AS p_role,
	                           m.role AS m_role,
	                           p.preferred_role AS p_pref_role,
	                           m.preferred_role AS m_pref_role,
	                           p.address AS p_address,
	                           m.address AS m_address,
	                           p.status AS p_status,
	                           m.status AS m_status,
	                           p.mode AS p_mode,
	                           m.mode AS m_mode
	                      FROM gp_segment_configuration AS p,
	                           gp_segment_configuration AS m
	                     WHERE ( (p.content = m.content) AND
	                             (p.dbid <> m.dbid) ) AND
	                           p.status = 'u' AND
	                           m.status = 'd' AND
	                           p.mode <> 'c'"

	    psql --pset pager \\
	         --dbname template1 \\
	         --command "-- principle 3: primary is in resync -> mirror should be in resync
	                    SELECT p.content,
	                           p.dbid AS p_dbid,
	                           m.dbid AS m_dbid,
	                           p.role AS p_role,
	                           m.role AS m_role,
	                           p.preferred_role AS p_pref_role,
	                           m.preferred_role AS m_pref_role,
	                           p.address AS p_address,
	                           m.address AS m_address,
	                           p.status AS p_status,
	                           m.status AS m_status,
	                           p.mode AS p_mode,
	                           m.mode AS m_mode
	                      FROM gp_segment_configuration AS p,
	                           gp_segment_configuration AS m
	                     WHERE ( (p.content = m.content) AND
	                             (p.dbid <> m.dbid) ) AND
	                            p.status = 'u' AND
	                            p.mode = 'r' AND
	                            ( (m.mode <> 'r') OR
	                              (m.status = 'd') )"
	}

	function pglockinfo(){
	    psql --pset pager \\
	         --dbname template1 \\
	         --command "SELECT pgsa.datname,
	                           pgc.oid,
	                           pgl.pid,
	                           pgc.relname,
	                           pgl.transactionid,
	                           pgl.mode,
	                           pgl.granted,
	                           pgsa.usename,
	                           substr(pgsa.current_query,1,50),
	                           pgsa.query_start,
	                           age(now(), pgsa.query_start) AS "age",
	                           pgsa.procpid
	                      FROM pg_locks AS pgl
	                           LEFT OUTER JOIN pg_class AS pgc ON (pgl.relation = pgc.oid)
	                           LEFT OUTER JOIN pg_stat_activity AS pgsa ON (pgl.pid=pgsa.procpid)
	                     ORDER BY query_start"
	}

	function loadtpchsmall(){
	    (source ${BASE_DIR}/env-${GPDB_VERSION}-${GPDB_BUILD_VERSION}.sh;
	     cd ${BASE_DIR}/cdbunit/cdbfast/tpchsmall;
	     rm -f {BASE_DIR}/cdbunit/cdbfast/tpchsmall/gptest.log;
	     python TEST.py)
	}

	## --------------------

	source ${GPDB_INSTALL_DIR}/greenplum_path.sh
	export CDBFASTHOME=${CDBFASTHOME}
	export PYTHONPATH=\${PYTHONPATH}:${CDBFASTHOME}/QAUtilities:${CDBFASTHOME}

EOF

if [ "${USE_GPPERFMON}" = "true" ]; then
	cat >> ${BASE_DIR}/env-${GPDB_VERSION}-${GPDB_BUILD_VERSION}.sh <<-EOF
		source ${GPPERFMON_INSTALL_DIR}/gpperfmon_path.sh
	EOF
fi

##
##
##

if [ "${USE_GPPERFMON}" = "true" ]; then
	pushd ${DATA_DIR}/logs > /dev/null
	[ -d ${GPPERFMON_INSTALL_DIR} ] && rm -rf ${GPPERFMON_INSTALL_DIR}
	${CDBUNIT_HOME}/scripts/runGPDBInstaller.py \
	    --pause 30 \
	    --installerbin ${BASE_DIR}/product/${GPPERFMON_INSTALLER_BIN} \
	    --path ${GPPERFMON_INSTALL_DIR}
	popd > /dev/null
fi

##
##
##

TMP_PATH=${PATH}

export PATH=${TMP_PATH}
unset PYTHONPATH
unset PYTHONHOME

MASTER_DATA_DIRECTORY_BASE=${GPDB_INSTALL_DATA_DIR}/master

[ -d ${MASTER_DATA_DIRECTORY_BASE} ] && rm -rf ${MASTER_DATA_DIRECTORY_BASE}
[ ! -d ${MASTER_DATA_DIRECTORY_BASE} ] && mkdir -p ${MASTER_DATA_DIRECTORY_BASE}

if [ "${SKIP_INSTALL}" != "true" ]; then
    install_gpdb
    tar zxf ${BASE_DIR}/product/qautils-RHEL5-x86_64.tar.gz -C ${GPDB_INSTALL_DIR}
fi

if [ -n "${INSTALL_ONLY}" ]; then
    exit 0
fi

setup_deployment

if [ -f "${GPDB_INSTALL_DIR}/greenplum_path.sh" ]; then
    source ${GPDB_INSTALL_DIR}/greenplum_path.sh
else
    echo "${GPDB_INSTALL_DIR}/greenplum_path.sh does not exist"
    exit 2
fi

## gpseginstall -f ${HOSTS_CONF} --user ${LOGNAME} -c sv

echo "RSYNC gpdb install directory: ${DATA_DIR}/gpdb"

for host in `cat ${HOSTS_CONF}`; do
    echo rsync -a --delete ${DATA_DIR}/gpdb ${host}:${DATA_DIR}/
    rsync -a --delete ${DATA_DIR}/gpdb ${host}:${DATA_DIR}/
    echo rsync -a --delete ${DATA_DIR}/greenplum-db ${host}:${DATA_DIR}/
    rsync -a --delete ${DATA_DIR}/greenplum-db ${host}:${DATA_DIR}/
done

cat <<-EOF

	======================================================================

EOF

gpinitsystem -a -c ${CLUSTER_CONF} -l ${LOGDIR}

check_deployment

cat <<-EOF

	======================================================================

EOF

##
## Setup GPPerfmon
##

if [ "${USE_GPPERFMON}" = "true" ]; then
    gpperfmon_install --enable --password gpmon123 --port ${PGPORT}
    cat >> ${MASTER_DATA_DIRECTORY}/pg_hba.conf <<-EOF
		host gpperfmon gpmon 127.0.0.1/28 trust
	EOF

    cat >> ${MASTER_DATA_DIRECTORY}/gpperfmon/conf/gpperfmon.conf <<-EOF
		qamode=1
		min_query_time=0.5
		min_detailed_query_time=0.5
		harvest_interval=30
		
	EOF

    run_cmd "gpstop -r -a -l ${LOGDIR}"

    ##
    ## Check deployment
    ##

    check_deployment; \

    psql --pset=pager -U gpmon gpperfmon -c 'SELECT * FROM system_now;'
    RETURN=$?
    check_return

    ##
    ##
    ##

    ( source ${BASE_DIR}/env-${GPDB_VERSION}-${GPDB_BUILD_VERSION}.sh; \
      cd ${BASE_DIR}/cdbunit/cdbfast/tpchsmall; \
      python TEST.py > TEST.log 2>&1 & )
      
    ##
    ##
    ##

    cat > ${BASE_DIR}/conf/gpperfmon-setup-input.txt <<-EOF
		gpdbqa
		
		GPDB Quality Assurance ($( hostname -s ):${GPDB_PLATFORM})
		
		
		n
	EOF

    ( source ${BASE_DIR}/env-${GPDB_VERSION}-${GPDB_BUILD_VERSION}.sh; \
      cat ${BASE_DIR}/conf/gpperfmon-setup-input.txt | gpperfmon --setup; \
      gpperfmon --start gpdbqa )

fi

##
## gpdeletesystem
##

## run_cmd "gpdeletesystem --master-data-directory ${MASTER_DATA_DIRECTORY} -l ${LOGDIR}"
