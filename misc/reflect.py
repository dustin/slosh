#!/usr/bin/env python
"""
Stream updates from one slosh instance to one or more others.

Copyright (c) 2008  Dustin Sallings <dustin@spy.net>
"""

import sys
import urllib

from twisted.internet import reactor, task, error
from twisted.web import client, sux

cookies = {}

def cb(factory):
    def f(data):
        global cookies
        cookies = factory.cookies
    return f

class Post(object):

    def __init__(self):
        self.pairs = []

    def add(self, key, data):
        self.pairs.append((key, data))

    def __repr__(self):
        return "<Post %s>" % (', '.join([k + "=" + v for (k,v) in self.pairs]))

class Emitter(sux.XMLParser):

    def __init__(self, urls):
        self.urls = urls
        self.connectionMade()
        self.currentEntry=None
        self.data = []
        self.depth = 0

    def write(self, b):
        self.dataReceived(b)

    def close(self):
        self.connectionLost(error.ConnectionDone())

    def open(self):
        pass

    def read(self):
        return None

    def gotTagStart(self, name, attrs):
        self.depth += 1
        self.data = []
        if self.depth == 2:
            assert self.currentEntry is None
            self.currentEntry = Post()

    def gotTagEnd(self, name):
        self.depth -= 1
        if self.currentEntry:
            if self.depth == 1:
                self.emit()
                self.currentEntry = None
            else:
                self.currentEntry.add(name, ''.join(self.data).decode('utf8'))

    def gotText(self, data):
        self.data.append(data)

    def gotEntityReference(self, data):
        e = {'quot': '"', 'lt': '&lt;', 'gt': '&gt;', 'amp': '&amp;'}
        if e.has_key(data):
            self.data.append(e[data])
        else:
            print "Unhandled entity reference: ", data

    def emit(self):
        h = {'Content-Type': 'application/x-www-form-urlencoded'}
        params = urllib.urlencode(self.currentEntry.pairs)
        for url in self.urls:
            client.getPage(url, method='POST', postdata=params, headers=h)

def logError(e):
    print e

def copy(urlin, urlsout):
    # Stolen cookie code since the web API is inconsistent...
    headers={}
    l=[]
    for cookie, cookval in cookies.items():
        l.append('%s=%s' % (cookie, cookval))
    headers['Cookie'] = '; '.join(l)

    factory = client.HTTPDownloader(urlin, Emitter(urlsout), headers=headers)
    scheme, host, port, path = client._parse(urlin)
    reactor.connectTCP(host, port, factory)
    factory.deferred.addCallback(cb(factory))
    factory.deferred.addErrback(logError)
    return factory.deferred

lc = task.LoopingCall(copy, sys.argv[1], sys.argv[2:])
lc.start(0)

reactor.run()
