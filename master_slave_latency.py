#!/usr/bin/env python
#-*- coding: utf-8 -*-
#
#
# Authors:
#    javierarilos - 2013
#
u"""
Checking the latency in a master-slave configuration.
"""

# imports std lib
import logging
import time
import timeit

# imports 3rd party libs
import redis

diagram = """
master                                             slave
localhost:33311                                    localhost:44411
-------------------                                -------------------
|                 |                                |                 |
|                 |          slaveof               |                 |
|     REDIS       | <----------------------------- |     REDIS       |
|                 |                                |                 |
|                 |                                |                 |
-------------------                                -------------------
"""

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)
hdlr = logging.StreamHandler()
log.addHandler(hdlr)


def print_statistics(delays, elements, how_long):
    delayed_elements = len(delays)
    delayed_percentage = delayed_elements / float(elements) * 100 if delayed_elements else 0

    global max_delay, min_delay, sum_delay
    max_delay = 0
    min_delay = 0
    sum_delay = 0

    for delay_tuple in delays:
        it, added, delay = delay_tuple
        max_delay = max(max_delay, delay)
        min_delay = min(min_delay, delay)
        sum_delay += delay

    # average of delay (counting only delayed elements)
    avg_delay = sum_delay / float(delayed_elements) if sum_delay else 0
    # average of delay (counting all elements).
    avg_delay_complete = sum_delay / float(elements) if sum_delay else 0

    log.info('======= STATISTICS =======')
    log.info('Total time: %f', how_long)
    log.info('Total elements: %d', elements)
    log.info('Number of delayed elements: %d', delayed_elements)
    log.info('%% of delayed elements: %f', delayed_percentage)
    log.info('Maximum delay: %f', max_delay)
    log.info('Minimum delay: %f', min_delay)
    log.info('Average delay: %f', avg_delay)
    log.info('Average delay complete: %f', avg_delay_complete)

def main():
    log.info("Redis Master-Slave Latency measurer.")
    log.info(diagram)
    log.info("")

    # Init redis clients.
    r1 = redis.StrictRedis(port=33311)
    r2 = redis.StrictRedis(port=44411)

    r1.ping()
    r2.ping()

    #r2.slaveof(host='127.0.0.1', port=33311)

    elements = 1000000
    ten_percent = elements / 10
    set_name = 'my_large_set'
    delays = []

    r1.delete(set_name)

    def check_delay():
        delayed = False
        for it in xrange(1, elements):
            r1.sadd(set_name, it)
            added = time.time()
            if not(it % ten_percent):
                log.info('>> %d', it)
            while not r2.sismember(set_name, it):
                delayed = True
            if delayed:
                delay = time.time() - added
                #print '>> delay {:.6f} secs in iteration : {}'.format(delay, it)
                delays.append((it, added, delay))
        return delays
    log.info("starting to check delay for {} elements.".format(elements))
    how_long = timeit.timeit(check_delay, number=1)

    log.info("check_delay took %d for %d elements", how_long, elements)
    
    print_statistics(delays, elements, how_long)


if __name__ == '__main__':
    main()
