#!/bin/sh
echo "Creating configuration file for the sentinel: sentinel.conf"
if [ -f sentinel.conf ] 
then
    rm sentinel.conf
fi
echo sentinel monitor sprayer-master 127.0.0.1 33311 1 >> sentinel.conf
echo sentinel down-after-milliseconds sprayer-master 5000 >> sentinel.conf
echo sentinel can-failover sprayer-master yes >> sentinel.conf
echo sentinel parallel-syncs sprayer-master 1 >> sentinel.conf
echo sentinel failover-timeout sprayer-master 900000 >> sentinel.conf

echo "Creating configuration file for the master: master.conf"
if [ -f master.conf ] 
then
    rm master.conf
fi
echo port 33311 >> master.conf
echo slave-priority 10 >> master.conf

echo "Creating configuration file for the slave: slave.conf"
if [ -f slave.conf ] 
then
    rm slave.conf
fi
echo port 33322 >> slave.conf
echo slaveof localhost 33311 >> slave.conf
echo slave-priority 100 >> slave.conf
echo appendonly yes >> slave.conf
echo appendfsync everysec >> slave.conf

echo "running redis-server as master, using master.conf"
redis-server master.conf &
echo "running redis-server as slave, using slave.conf"
redis-server slave.conf &
echo "running redis-server as sentinel, using sentinel.conf"
redis-server sentinel.conf --sentinel &

sleep 3

echo ===
echo === the following command forces the master to be the default one
echo === redis-cli -p 26379 sentinel failover sprayer-master
