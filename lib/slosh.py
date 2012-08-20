#!/usr/bin/env python
"""

Copyright (c) 2008  Dustin Sallings <dustin@spy.net>
"""

import json
import cStringIO as StringIO

from twisted.web import server, resource
from twisted.internet import task

class Topic(resource.Resource):

    max_queue_size = 100
    max_id = 1000000000

    def __init__(self, parent, topic):
        self.last_id = 0
        self.parent = parent
        self.topic = topic
        self.objects=[]
        self.requests=[]
        self.known_sessions={}
        self.methods = {'GET': self._do_GET, 'POST': self._do_POST}
        self.__cleanup = task.LoopingCall(self.__touch_active_sessions)
        self.__cleanup.start(5, now=False)

    def _do_GET(self, request):
        session = request.getSession()
        if session.uid not in self.known_sessions:
            print "New session: ", session.uid
            self.known_sessions[session.uid] = self.last_id
            session.notifyOnExpire(self.__mk_session_exp_cb(session.uid))
        if not self.__deliver(request):
            self.requests.append(request)
            request.notifyFinish().addBoth(self.__req_finished, request)
        return server.NOT_DONE_YET

    def _do_POST(self, request):
        # Store the object
        self.objects.append(json.load(request.content))
        if len(self.objects) > self.max_queue_size:
            del self.objects[0]
        self.last_id += 1
        if self.last_id > self.max_id:
            self.last_id = 1
        for r in self.requests:
            self.__deliver(r)
        return self.__mk_res(request, 'ok', 'application/json')

    def render(self, request):
        return self.methods[request.method](request)

    def __since(self, n):
        # If a nonsense ID comes in, scoop them all up.
        if n > self.last_id:
            print "Overriding last ID from %d to %d" % (n, self.last_id - 1)
            n = self.last_id - 1
        f = max(0, self.last_id - n)
        rv = self.objects[0-f:] if self.last_id > n else []
        return rv, self.last_id - n

    def __req_finished(self, whatever, request):
        self.requests.remove(request)

    def __touch_active_sessions(self):
        for r in self.requests:
            r.getSession().touch()

    def __deliver(self, req):
        sid = req.getSession().uid
        since = req.args.get('n')
        if since:
            since=int(since[0])
        else:
            since = self.known_sessions[sid]
        data, oldsize = self.__since(since)
        if data:
            self.__transmit_json(req, data, oldsize)
            req.finish()
        self.known_sessions[sid] = self.last_id
        return data

    def __transmit_json(self, req, data, oldsize):
        jdata=[dict(s) for s in data]
        j=json.dumps({'max': self.last_id, 'saw': oldsize,
            'delivering': len(data), 'res': jdata})
        req.write(self.__mk_res(req, j, 'application/json'))

    def __mk_session_exp_cb(self, sid):
        def f():
            print "Expired session", sid
            del self.known_sessions[sid]
            if not self.known_sessions:
                print "Need to delete topic", self.topic
                self.__cleanup.stop()
                self.parent.delEntity(self.topic)
        return f

    def __mk_res(self, req, s, t):
        req.setHeader("content-type", t)
        req.setHeader("content-length", str(len(s)))
        return s

class Topics(resource.Resource):

    def getChild(self, path, request):
        t=path.split('/', 1)[0]
        if t.find(".") > 0:
            t=t.split(".", 1)[0]
            topic = self.getChildWithDefault(t, request)
        else:
            topic = Topic(self, t)
            self.putChild(t, topic)
            print "Registered new topic", t
        return topic

