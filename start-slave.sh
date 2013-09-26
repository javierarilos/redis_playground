#!/bin/sh

if [ $1 ]
then 
    INSTANCE_NUMBER=$1
else
    INSTANCE_NUMBER=1
fi

CUR=`pwd`
PROC_NAME=slave-$INSTANCE_NUMBER
PID_FILE="$CUR/$PROC_NAME.pid"
CONF_FILE="$PROC_NAME.conf"

if [ -f $CONF_FILE ] 
then
    rm $CONF_FILE
fi

echo daemonize no >> $CONF_FILE
echo pidfile $PID_FILE >> $CONF_FILE
echo port 444$INSTANCE_NUMBER$INSTANCE_NUMBER >> $CONF_FILE
echo slaveof localhost 33311 >> $CONF_FILE
echo slave-priority 100 >> $CONF_FILE
echo appendonly yes >> $CONF_FILE
echo appendfsync everysec >> $CONF_FILE

echo "running redis-server as $PROC_NAME, using config: $CONF_FILE and pid_file: $PID_FILE"
echo "configuration:"
cat $CONF_FILE
echo

redis-server $CONF_FILE &

echo ===
echo === the following command forces the master to be the default one
echo === redis-cli -p 26379 sentinel failover sprayer-master
