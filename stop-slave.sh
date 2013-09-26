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
PROC_PID=`cat $PID_FILE`
CONF_FILE="$PROC_NAME.conf"
echo "Stopping $PROC_NAME with PID $PROC_PID" 
kill $PROC_PID
if [ -f $CONF_FILE ] 
then
    rm $CONF_FILE
fi
