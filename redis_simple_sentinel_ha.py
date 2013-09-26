#!/usr/bin/env python
#-*- coding: utf-8 -*-
#
#
# Authors:
#    javier.arilos@gmail.com - 2013
#
u"""
Simple Redis Sentinel Client for HA.
"""

# imports std lib

# imports 3rd party libs

# imports sprayer
from itertools import izip

from redis import StrictRedis, ConnectionError


# CONNECTION STATUSES:
import time
import redis

NO_SENTINEL = 'NO_SENTINEL'                     # No connection to Sentinel.
SENTINEL_OK = 'SENTINEL_OK'                     # Connected to Sentinel, but not to Master.
MASTER_AND_SENTINEL = 'MASTER_AND_SENTINEL'     # Connected to Master and Sentinel.


class TimeoutException(Exception):
    pass


class NoSentinelException(Exception):
    pass


class NoMasterException(Exception):
    pass


def is_connected(strict_redis):
    """
    :param strict_redis: StrictRedis instance to check.
    :return: True if strict_redis is connected (strict_redis.ping() is True)
    """
    try:
        if strict_redis.ping():
            return True
        else:
            return False
    except ConnectionError:
        return False


def time_exceeded(max_time):
    return time.time() > max_time


def parse_info(response):
    """Patched version of redis.client parse_info.
        Parse the result of Redis's INFO command into a Python dict"""
    info = {}
    response = redis._compat.nativestr(response)

    def get_value(value):
        if ',' not in value or '=' not in value:
            return value

        sub_dict = {}
        for item in value.split(','):
            k, v = item.rsplit('=', 1)
            try:
                sub_dict[k] = int(v)
            except ValueError:
                sub_dict[k] = v
        return sub_dict

    def split_by_first(text, separator):
        position = text.find(separator)
        pre = text[:position]
        post = text[position + 1:]
        return pre, post

    for line in response.splitlines():
        if line and not line.startswith('#'):
            try:
                key, value = split_by_first(line, ':')
                if '.' in value:
                    info[key] = float(value)
                else:
                    info[key] = int(value)
            except ValueError:
                info[key] = get_value(value)

    return info


def init_strict_redis(i):
    """Creates a new Strict redis and patches it to allow info command to work in a master-slave
        See: https://github.com/andymccurdy/redis-py/issues/354"""
    s = StrictRedis(**i)
    s.response_callbacks['INFO'] = parse_info
    return s


class StrictSentinel(object):
    """StrictSentinel is a redis.StrictRedis provider that is Sentinel aware.
    By connecting to a Sentinel or list of Sentinels provides access to a StrictRedis instance to the master.

    The only connection or connections parameters needed are those for the Sentinel, then Redis master is queried to
    the Sentinel.
    """

    def __init__(self, host='localhost', port=26379, db=0, password=None, socket_timeout=None, charset='utf-8',
                 errors='strict', decode_responses=False, sentinels=None, retries_sleep=1):
        """ Should receive the connection parameters for one Sentinel or a list of sentinels in sentinels parameter.
        :param host: Redis Sentinel host.
        :param port: Redis Sentinel port.
        :param db: Redis db to user.
        :param password: Redis Sentinel password.
        :param socket_timeout: Redis Sentinel socket_timeout.
        :param charset: Redis Sentinel charset.
        :param errors: Redis Sentinel errors.
        :param decode_responses: Redis Sentinel decode_responses.
        :param sentinels: list of sentinels with all their connection parameters as dictionaries.
        :param retries_sleep: time to sleep between retries when connection to master or all sentinels fail.
        :return:
        """
        self.db = db
        self.password = password
        self.socket_timeout = socket_timeout
        self.charset = charset
        self.errors = errors
        self.decode_responses = decode_responses
        if not sentinels:
            sentinels = [{
                'host': host,
                'port': port,
                'db': self.db,
                'password': self.password,
                'socket_timeout': socket_timeout,
                'charset': self.charset,
                'errors': self.errors,
                'decode_responses': self.decode_responses,
                }]
        self.sentinels = sentinels
        self.status = NO_SENTINEL
        self.retries_sleep = retries_sleep

    def _map_master_info_to_strict_redis(self, master):
        new_master = {
            'host': master['ip'],
            'port': int(master['port']),
            'db': self.db,
            'password': self.password,
            'socket_timeout': self.socket_timeout,
            'charset': self.charset,
            'errors': self.errors,
            'decode_responses': self.decode_responses,
        }
        return new_master

    def get_masters(self):
        """Queries the Sentinel about all its masters.
        :return a dictionary for the masters
        """
        masters_as_list = self.sentinel.execute_command('SENTINEL', 'MASTERS')
        masters = {}
        for master_l in masters_as_list:
            #convert list representing a master to a dictionary
            i = iter(master_l)
            master_d = dict(izip(i, i))
            masters[master_d['name']] = master_d
        return masters

    def get_strict_redis(self, master_name, timeout=5):
        """
        :param master_name: name of the master to be get.
        :param timeout: maximum time, in seconds, to return a StrictRedis instance or None.
        :return:
        """
        max_time = time.time() + timeout
        if self.status == NO_SENTINEL:
            while self.status is NO_SENTINEL and not time_exceeded(max_time):
                # search for a sentinel.
                i = 0
                while self.status is NO_SENTINEL and i < len(self.sentinels):
                    self.sentinel = init_strict_redis(self.sentinels[i])
                    if is_connected(self.sentinel):
                        self.status = SENTINEL_OK
                    i += 1

                if self.status is NO_SENTINEL and not time_exceeded(max_time):
                    time.sleep(self.retries_sleep)

            while self.status is SENTINEL_OK and not time_exceeded(max_time):
                # get the master from the sentinel
                masters = self.get_masters()
                master = masters[master_name]
                master = self._map_master_info_to_strict_redis(master)
                self.master = init_strict_redis(master)
                #TODO: HANDLE MASTER.PING == False.
                if is_connected(self.master):
                    self.status = MASTER_AND_SENTINEL

        if self.status is NO_SENTINEL:
            raise NoSentinelException
        elif self.status is SENTINEL_OK:
            raise NoMasterException

        return self.master