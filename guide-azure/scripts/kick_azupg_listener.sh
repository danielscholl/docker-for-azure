#!/bin/bash

export CUSTOM_DATA_FILE=/var/lib/waagent/CustomData

parse_export_value()
{
  expval=$(grep $1= $CUSTOM_DATA_FILE | sed -e 's/export .[A-Z|_]*\=\"\(.*\)\"/\1/')
}

PIDFILE=/var/upgrade_listener.pid
if [ -f $PIDFILE ]
then
  PID=$(cat $PIDFILE)
  ps -p $PID > /dev/null 2>&1
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
  echo $$ > $PIDFILE
  if [ $? -ne 0 ]
  then
    echo "Could not create PID file"
    exit 1
  fi
fi

parse_export_value UCP_ELB_HOSTNAME
export UCP_ELB_HOSTNAME=$expval

if [ -n "$UCP_ELB_HOSTNAME" ]; then
    parse_export_value UCP_ADMIN_PASSWORD
    export UCP_ADMIN_PASSWORD=$expval

    parse_export_value UCP_ADMIN_USER
    export UCP_ADMIN_USER=$expval

    parse_export_value UCP_LICENSE
    export UCP_LICENSE=$(echo -n  "$expval" | base64 -d)
fi

python -u /usr/bin/azupg_listener.py >> /var/log/upgrade.log