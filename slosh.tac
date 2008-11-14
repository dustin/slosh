#!/usr/bin/env python
"""

Copyright (c) 2008  Dustin Sallings <dustin@spy.net>
"""

import sys
import ConfigParser

sys.path.append("lib")

from twisted.application import internet, service
from twisted.web import server, resource, static
from twisted.internet import defer, task

import slosh

conf = ConfigParser.ConfigParser()
conf.read('slosh.conf')

application = service.Application('slosh')
serviceCollection = service.IServiceCollection(application)

# Keep really short sessions.
server.Session.sessionTimeout=30

root = static.File(conf.get("web", "root"))
root.putChild('topics', slosh.Topics())

site = server.Site(root)
site.sessionCheckTime = 30
internet.TCPServer(8000, site).setServiceParent(serviceCollection)
