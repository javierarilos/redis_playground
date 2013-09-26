#!/bin/sh


if [ $1 ]
then 
    INSTANCE_NUMBER=$1
else
    INSTANCE_NUMBER=1
fi

CUR=`pwd`
PROC_NAME=master-$INSTANCE_NUMBER
PID_FILE="$CUR/$PROC_NAME.pid"
CONF_FILE="$PROC_NAME.conf"
if [ -f $CONF_FILE ] 
then
    rm $CONF_FILE
fi
echo port 333$INSTANCE_NUMBER$INSTANCE_NUMBER >> $CONF_FILE
echo daemonize yes >> $CONF_FILE
echo pidfile $PID_FILE >> $CONF_FILE
echo slave-priority 10 >> $CONF_FILE

echo "running redis-server as $PROC_NAME, using config: $CONF_FILE and pid_file: $PID_FILE"
echo "configuration:"
cat $CONF_FILE
echo
redis-server $CONF_FILE &
