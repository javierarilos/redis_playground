import subprocess
import sys
from time import time
from time import sleep

from redis.client import StrictRedis
from redis.sentinel import Sentinel
from redis import ConnectionError

NAME = 'sprayer-master'


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
# err = subprocess.call('./start-master.sh')
# if err:
#     print 'error starting master instance.'
#     sys.exit(99)
a = StrictRedis('localhost', 33311)
raw_input('./start-master.sh')
wait_for_redis(a)

# err = subprocess.call('./start-slave.sh')
# if err:
#     print 'error starting slave instance.'
#     sys.exit(99)
raw_input('./start-slave.sh')
b = StrictRedis('localhost', 44411)
wait_for_redis(b)

# err = subprocess.call('./start-sentinel.sh')
# if err:
#     print 'error starting sentinel instance.'
#     sys.exit(99)
raw_input('./start-sentinel.sh')
c = StrictRedis('localhost', 55511)
wait_for_redis(c)

sentinel = Sentinel([('localhost', 55511)], socket_timeout=0.1)
if sentinel.discover_master(NAME)[1] != 33311:
    print 'unexpected situation: expecting port 33311 to be the master'
    sys.exit(99)

print """>> Getting an High Availability connection through the sentinel.
"""
mha = sentinel.master_for(NAME)
if int(mha.config_get()['port']) != 33311:
    print 'unexpected master. expecting master to be on port 33311.'
    sys.exit(99)

assert mha.ping() and a.ping()

print """>> Currently: (MASTER:{})<==(SLAVES:{})""".format(sentinel.discover_master(NAME),
                                                           sentinel.discover_slaves(NAME))

print """>> Stopping A instance (current master)
"""
# err = subprocess.call('./stop-master.sh')
# if err:
#     print 'error stopping master instance.'
#     sys.exit(99)
raw_input('./stop-master.sh')
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

print """>> Currently: (MASTER:{})<==(SLAVES:{})""".format(sentinel.discover_master(NAME),
                                                           sentinel.discover_slaves(NAME))

print """>> lets start instance A"""

raw_input('./start-master.sh')
a = StrictRedis('localhost', 33311)
wait_for_redis(a)

print """>> Currently: (MASTER:{})<==(SLAVES:{})""".format(sentinel.discover_master(NAME),
                                                           sentinel.discover_slaves(NAME))


def promote_original_master(s, name):
    """When a master fails, Sentinel promotes a slave. When the old master restarts,
    it is set as slave.
    With this command, the old master is promoted again to master.
    """
    s.execute_command('SENTINEL', 'FAILOVER', name)

promote_original_master(c, NAME)

sleep(5)

print """>> Currently: (MASTER:{})<==(SLAVES:{})""".format(sentinel.discover_master(NAME),
                                                           sentinel.discover_slaves(NAME))
