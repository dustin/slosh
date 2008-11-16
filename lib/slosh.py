#!/usr/bin/env python
"""

Copyright (c) 2008  Dustin Sallings <dustin@spy.net>
"""

import xml.sax
import xml.sax.saxutils
import cStringIO as StringIO

from twisted.web import server, resource
from twisted.internet import task

# Stolen from memcached protocol
try:
    from collections import deque
except ImportError:
    class deque(list):
        def popleft(self):
            return self.pop(0)

class RequestQueue(object):

    max_queue_size = 100

    def __init__(self, session):
        self.session = session
        self.accepted = 0
        self.__q=deque()

    def append(self, content):
        self.accepted += 1
        self.__q.append(content)
        if self.accepted > self.max_queue_size:
            self.__q.popleft()

    def empty(self):
        rv = (self.__q, self.accepted)
        self.__q = deque()
        self.accepted = 0
        return rv

class Topic(resource.Resource):

    def __init__(self):
        self.requests=[]
        self.queues={}
        l = task.LoopingCall(self.__touch_active_sessions)
        l.start(5, now=False)

    def render(self, request):
        if request.method == 'GET':
            session = request.getSession()
            if session.uid not in self.queues:
                print "New session: ", session.uid
                self.queues[session.uid] = RequestQueue(session)
                session.notifyOnExpire(self.__mk_session_exp_cb(session.uid))
            if not self.__deliver(request):
                self.requests.append(request)
                request.notifyFinish().addBoth(self.__req_finished(request))
            return server.NOT_DONE_YET
        else:
            # Store all the data for all known queues
            params=self.__xml(request.args)
            for sid, a in self.queues.iteritems():
                print "Queueing to", sid
                a.append(params)
            for r in self.requests:
                self.__deliver(r)
            return self.__mk_res(request, 'ok', 'text/plain')

    def __req_finished(self, request):
        print "New in-flight request %s (%d)" % (request, id(request))
        def f(*whatever):
            print "Completed %s (%d)" % (request, id(request))
            self.requests.remove(request)
        return f

    def __xml(self, h):
        class G(xml.sax.saxutils.XMLGenerator):
            def doElement(self, name, value, attrs={}):
                self.startElement(name, attrs)
                if value is not None:
                    self.characters(value)
                self.endElement(name)
        s=StringIO.StringIO()
        g=G(s, 'utf-8')
        g.startElement("p", {})
        for k,v in h.iteritems():
            for subv in v:
                g.doElement(k, subv)
        g.endElement("p")
        s.seek(0, 0)
        return s.read()

    def __touch_active_sessions(self):
        for r in self.requests:
            r.getSession().touch()

    def __deliver(self, req):
        sid = req.getSession().uid
        (data, oldsize) = self.queues[sid].empty()
        if data:
            print "Delivering to %s at %s (%d)" % (sid, req, id(req))
            c = ('<?xml version="1.0"?>\n<res saw="' + str(oldsize)
                + '">' + '\n'.join(data) + "</res>")
            req.write(self.__mk_res(req, c, 'text/xml'))
            req.finish()
        return data

    def __mk_session_exp_cb(self, sid):
        def f():
            print "Expired session", sid
            del self.queues[sid]
        return f

    def __mk_res(self, req, s, t):
        req.setHeader("content-type", t)
        req.setHeader("content-length", str(len(s)))
        return s

class Topics(resource.Resource):

    def getChild(self, path, request):
        t=path.split('/', 1)[0]
        topic = Topic()
        self.putChild(t, topic)
        print "Registered new topic", t
        return topic

