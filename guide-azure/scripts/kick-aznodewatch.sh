#!/bin/bash

export CUSTOM_DATA_FILE=/var/lib/waagent/CustomData

parse_export_value()
{
  expval=$(grep $1= $CUSTOM_DATA_FILE | sed -e 's/export .[A-Z|_]*\=\"\(.*\)\"/\1/')
}

PIDFILE=/var/nodewatch.pid
if [ -f $PIDFILE ]
then
  PID=$(cat $PIDFILE)
  ps -o pid | grep $PID
  if [ $? -eq 0 ]
  then
    echo "Job is already running"
    exit 0
  else
    ## Process not found assume not running
    echo $$ > $PIDFILE
    if [ $? -ne 0 ]
    then
      echo "Could not create PID file"
      exit 1
    fi
  fi
else
  ## PID file not found .. Running for the first time
  ## wait for a while the first time for things to stabilize
  sleep 600
  echo $$ > $PIDFILE
  if [ $? -ne 0 ]
  then
    echo "Could not create PID file"
    exit 1
  fi
fi

IS_LEADER=$(docker node inspect self -f '{{ .ManagerStatus.Leader }}')
## only run in current leader
if [[ "$IS_LEADER" == "true" ]]; then
    parse_export_value UCP_ELB_HOSTNAME
    export UCP_ELB_HOSTNAME=$expval

    if [ -n "$UCP_ELB_HOSTNAME" ]; then
        parse_export_value UCP_ADMIN_PASSWORD
        export UCP_ADMIN_PASSWORD=$expval

        parse_export_value UCP_ADMIN_USER
        export UCP_ADMIN_USER=$expval

        parse_export_value DTR_STORAGE_ACCOUNT
        export DTR_STORAGE_ACCOUNT=$expval

        parse_export_value DTR_ELB_HOSTNAME
        export DTR_ELB_HOSTNAME=$expval
    fi
    python -u /usr/bin/aznodewatch.py >> /var/log/nodewatch.log
fi