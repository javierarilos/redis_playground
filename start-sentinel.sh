#!/bin/sh

if [ $1 ]
then 
    INSTANCE_NUMBER=$1
else
    INSTANCE_NUMBER=1
fi

CUR=`pwd`
PROC_NAME=sentinel-$INSTANCE_NUMBER
PID_FILE="$CUR/$PROC_NAME.pid"
CONF_FILE="$PROC_NAME.conf"
if [ -f $CONF_FILE ] 
then
    rm $CONF_FILE
fi
echo port 555$INSTANCE_NUMBER$INSTANCE_NUMBER >> $CONF_FILE
echo daemonize yes >> $CONF_FILE
echo pidfile $PID_FILE >> $CONF_FILE
echo sentinel monitor sprayer-master 127.0.0.1 33311 1 >> $CONF_FILE
echo sentinel down-after-milliseconds sprayer-master 5000 >> $CONF_FILE
echo sentinel can-failover sprayer-master yes >> $CONF_FILE
echo sentinel parallel-syncs sprayer-master 1 >> $CONF_FILE
echo sentinel failover-timeout sprayer-master 900000 >> $CONF_FILE


echo "running redis-server as $PROC_NAME, using config: $CONF_FILE and pid_file: $PID_FILE"
redis-server $CONF_FILE --sentinel &
