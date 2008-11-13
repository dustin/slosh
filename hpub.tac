#!/usr/bin/env python
"""

Copyright (c) 2008  Dustin Sallings <dustin@spy.net>
"""

import sys
from twisted.application import internet, service
from twisted.web import server, resource, static
from twisted.internet import defer

class Topic(resource.Resource):

    def __init__(self):
        self.requests=[]

    def render(self, request):
        if request.method == 'GET':
            self.requests.append(request)
            return server.NOT_DONE_YET
        else:
            t=self.requests
            self.requests=[]
            c=str(request.args)
            for r in t:
                r.write(self.__mk_res(r, c, 'text/plain'))
                r.finish()
            return self.__mk_res(request, 'ok', 'text/plain')

    def __mk_res(self, req, s, t):
        req.setHeader("content-type", t)
        req.setHeader("content-length", str(len(s)))
        return s

class TopResource(resource.Resource):

    topics = {}

    def getChild(self, path, request):
        a=path.split('/', 1)
        t=a[0]
        rest = None
        if len(a) > 1: rest=a[1]

        topic = self.topics.get(t, None)
        if not topic:
            topic = Topic()
            self.topics[t] = topic

        return topic

application = service.Application('hpub')
serviceCollection = service.IServiceCollection(application)

internet.TCPServer(8000, server.Site(TopResource())
    ).setServiceParent(serviceCollection)
