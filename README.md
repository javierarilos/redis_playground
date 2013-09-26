redis_playground
================

Playing around with redis and a master-slave-sentinel configuration.



**Getting started:**
* *.sh files allow to start / stop each type of node.
* master_slave_latency.py - is a small test for checking the latency between write-to-master and read-from-slave the same key.
* ha-sentinel-poc.py - self contained script for testing a HA scenario. 
* redis_simple_sentinel_ha.py - playing around a little bit with the sentinel.

**Dependencies:**
* redis >= 2.6
* redis-py: version to be used must be sentinel aware (master branch as of september 26th 2013). https://github.com/andymccurdy/redis-py
