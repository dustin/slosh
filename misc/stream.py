#!/usr/bin/env python
"""
Log slosh output.

Copyright (c) 2008  Dustin Sallings <dustin@spy.net>
"""

import sys

from twisted.internet import reactor, task
from twisted.web import client

cookies = {}

def cb(factory):
    def f(data):
        global cookies
        cookies = factory.cookies
        print data
    return f

def getPage(url):
    factory = client.HTTPClientFactory(url, cookies=cookies)
    scheme, host, port, path = client._parse(url)
    reactor.connectTCP(host, port, factory)
    factory.deferred.addCallback(cb(factory))
    return factory.deferred

lc = task.LoopingCall(getPage, sys.argv[1])
lc.start(0)

reactor.run()
