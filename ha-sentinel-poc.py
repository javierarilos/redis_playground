import subprocess
import sys
from time import time
from time import sleep

from redis.client import StrictRedis
from redis.sentinel import Sentinel
from redis import ConnectionError


def wait_for_redis(strict_redis, tout=15):
    connected = False
    start = time()
    while not connected and time() - start < tout:
        try:
            connected = strict_redis.ping()
        except ConnectionError:
            pass

print '>> assuring a clean start. stopping the three redis.'
err = subprocess.call('./stop-master.sh')
err = subprocess.call('./stop-slave.sh')
err = subprocess.call('./stop-sentinel.sh')

print """>> Starting and checking: 
instance A as master on port 33311, 
instance B as slave on port 44411, 
sentinel on port 55511"""

err = subprocess.call('./start-master.sh')
if err:
    print 'error starting master instance.'
    sys.exit(99)
a = StrictRedis('localhost', 33311)
wait_for_redis(a)


err = subprocess.call('./start-slave.sh')
if err:
    print 'error starting slave instance.'
    sys.exit(99)

b = StrictRedis('localhost', 44411)
wait_for_redis(b)

err = subprocess.call('./start-sentinel.sh')
if err:
    print 'error starting sentinel instance.'
    sys.exit(99)

c = StrictRedis('localhost', 55511)
wait_for_redis(c)

sentinel = Sentinel([('localhost', 55511)], socket_timeout=0.1)
if sentinel.discover_master('sprayer-master')[1] != 33311:
    print 'unexpected situation: expecting port 33311 to be the master'
    sys.exit(99)

print """>> Getting an High Availability connection through the sentinel.
"""
mha = sentinel.master_for('sprayer-master')
if int(mha.config_get()['port']) != 33311:
    print 'unexpected master. expecting master to be on port 33311.'
    sys.exit(99)

assert mha.ping() and a.ping()

print """>> Now the situation is: (MASTER:{})<==(SLAVES:{})""".format(sentinel.discover_master('sprayer-master'),
                                                                      sentinel.discover_slaves('sprayer-master'))

print """>> Stopping A instance (current master)
"""
err = subprocess.call('./stop-master.sh')
if err:
    print 'error stopping master instance.'
    sys.exit(99)

print ">> waiting for A to stop."

try:
    while a.ping():
        pass
except ConnectionError:
    print '>> instance A stopped.'

print """>> Recovering HA connection...
"""
start = time()

connected = False
while not connected:
    try:
        connected = mha.ping()
    except ConnectionError:
        sleep(0.01)

print """>> HA Connection was recovered in {} seconds
""".format(time() - start)

if int(mha.config_get()['port']) != 44411:
    print 'unexpected master. expecting master to be on port 44411.'
    sys.exit(99)
else:
    print """>> New master is in port : {}""".format(mha.config_get()['port'])

try:
    a.ping()
except ConnectionError:
    print ">> Classical StrictRedis connection to A is dead. This is all right."

if b.ping():
    print ">> Classical StrictRedis connection to B is OK."
else:
    print '>> unexpected error while pinging to B'
    sys.exit(99)

print """>> Now the situation is: (MASTER:{})<==(SLAVES:{})""".format(sentinel.discover_master('sprayer-master'),
                                                                      sentinel.discover_slaves('sprayer-master'))

print """>> lets start instance A"""

err = subprocess.call('./start-master.sh')
if err:
    print 'error starting instance A.'
    sys.exit(99)

a = StrictRedis('localhost', 33311)
a.ping()

print """>> Now the situation is: (MASTER:{})<==(SLAVES:{})""".format(sentinel.discover_master('sprayer-master'),
                                                                      sentinel.discover_slaves('sprayer-master'))



