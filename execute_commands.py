#!/usr/bin/env python
#-*- coding: utf-8 -*-
#
# Copyright 2013 Telefonica Digital. All rights reserved.
#
# Authors:
#    jarias  <XYZ@tid.es> - 2013
#
u'''
MODULE DOCSTRING 
'''

# imports std lib

# imports 3rd party libs

# imports sprayer
from itertools import izip

from redis import StrictRedis
s = StrictRedis(port=55511)
#s = StrictRedis(port=33322)
print s.ping()

print 'segundo:', s.execute_command('PING')


def get_masters():
    masters_as_list = s.execute_command('SENTINEL', 'MASTERS')
    masters = {}
    for master_l in masters_as_list:
        #convert list representing a master to a dictionary
        i = iter(master_l)
        master_d = dict(izip(i, i))
        masters[master_d['name']] = master_d
    return masters

print get_masters()

def promote_original_master(name):
    """When a master fails, Sentinel promotes a slave. When the old master restarts, 
    it is set as slave.
    With this command, the old master is promoted again to master.
    """
    s.execute_command('SENTINEL', 'FAILOVER', name)
