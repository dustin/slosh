#!/usr/bin/env python
"""
Stream updates from one slosh instance to one or more others.

Copyright (c) 2008  Dustin Sallings <dustin@spy.net>
"""

import sys
import urllib

from twisted.internet import reactor, task, error
from twisted.web import client, sux

# The transformation function will receive a sequence of pairs and should
# return either a new sequence of pairs or a dict (or something else that has
# an items method that returns a list of pairs).
def identityTransform(s):
    return s

class Post(object):

    def __init__(self, transformer):
        self.pairs = []
        self.transformer = transformer

    def add(self, key, data):
        self.pairs.append((key, data))

    # items is called by urllib.urlencode, the results of which will be posted
    def items(self):
        return self.transformer(self.pairs)

    def __repr__(self):
        return "<Post %s>" % (', '.join([k + "=" + v for (k,v) in self.pairs]))

class Emitter(sux.XMLParser):

    def __init__(self, urls, transformer):
        self.urls = urls
        self.transformer = transformer
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
            self.currentEntry = Post(self.transformer)

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
        params = urllib.urlencode(self.currentEntry)
        for url in self.urls:
            client.getPage(url, method='POST', postdata=params, headers=h)

class ReflectionClient(object):

    cookies = {}

    def __init__(self, urlin, urlsout, transformer=identityTransform):
        self.urlin = urlin
        self.urlsout = urlsout
        self.transformer = transformer

        self.scheme, self.host, self.port, self.path = client._parse(urlin)

    def cb(self, factory):
        def f(data):
            self.cookies = factory.cookies
        return f

    def logError(e):
        print e

    def __call__(self):
        # Stolen cookie code since the web API is inconsistent...
        headers={}
        l=[]
        for cookie, cookval in self.cookies.items():
            l.append('%s=%s' % (cookie, cookval))
        headers['Cookie'] = '; '.join(l)

        factory = client.HTTPDownloader(self.urlin,
            Emitter(self.urlsout, self.transformer), headers=headers)
        reactor.connectTCP(self.host, self.port, factory)
        factory.deferred.addCallback(self.cb(factory))
        factory.deferred.addErrback(self.logError)
        return factory.deferred

lc = task.LoopingCall(ReflectionClient(sys.argv[1], sys.argv[2:]))
lc.start(0)

reactor.run()
