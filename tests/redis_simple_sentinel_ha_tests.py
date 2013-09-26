#!/usr/bin/env python
#-*- coding: utf-8 -*-
#
#
# Authors:
#    javier.arilos@gmail.com - 2013
#
u"""
Tests for redis_simple_sentinel_ha module.
"""

# imports std lib
import unittest

# imports 3rd party libs

# imports sprayer
from redis_simple_sentinel_ha import StrictSentinel, init_strict_redis, NoSentinelException


class StrictRedisViaSentinelTests(unittest.TestCase):
    def test_init_strict_redis(self):
        strict_redis = init_strict_redis({'port': 26379})
        self.assertTrue(strict_redis.ping())
        self.assertTrue(strict_redis.info().has_key('tcp_port'))

    def test_simplest(self):
        sentinel = StrictSentinel()
        strict_redis = sentinel.get_strict_redis('sprayer-master')
        self.assertTrue(strict_redis.ping())

    def test_nonexisting_sentinel(self):
        sentinel_cfg = {'host': 'localhost', 'port': 44455}
        sentinel = StrictSentinel(retries_sleep=0.001, **sentinel_cfg)
        self.assertRaises(NoSentinelException, sentinel.get_strict_redis, 'sprayer-master', 0.01)

    def test_two_sentinel_one_ko(self):
        """ Test two sentinels one non-existing and one OK. The existing is used to connect.
        """
        sentinels = [{'host': 'localhost', 'port': 44455}, {'host': 'localhost', 'port': 26379}]
        sentinel = StrictSentinel(retries_sleep=0.001, sentinels=sentinels)
        strict_redis = sentinel.get_strict_redis('sprayer-master')
        self.assertTrue(strict_redis.ping())

    def test_two_sentinel_one_dies(self):
        """Test two sentinels, connecting to the first, that dies.
        """