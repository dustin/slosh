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

application = service.Application('slosh')
serviceCollection = service.IServiceCollection(application)

# Keep really short sessions.
server.Session.sessionTimeout=30

site = server.Site(slosh.Topics())
site.sessionCheckTime = 30
internet.TCPServer(8000, site).setServiceParent(serviceCollection)
