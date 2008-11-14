#!/usr/bin/env python
"""

Copyright (c) 2008  Dustin Sallings <dustin@spy.net>
"""

import sys

sys.path.append("lib")

from twisted.application import internet, service
from twisted.web import server, resource, static
from twisted.internet import defer, task

import slosh

class TopResource(resource.Resource):

    topics = {}

    def getChild(self, path, request):
        a=path.split('/', 1)
        t=a[0]
        rest = None
        if len(a) > 1: rest=a[1]

        topic = self.topics.get(t, None)
        if not topic:
            topic = slosh.Topic()
            self.topics[t] = topic

        return topic

application = service.Application('slosh')
serviceCollection = service.IServiceCollection(application)

# Keep really short sessions.
server.Session.sessionTimeout=30

site = server.Site(TopResource())
site.sessionCheckTime = 30
internet.TCPServer(8000, site).setServiceParent(serviceCollection)
