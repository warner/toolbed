from twisted.application import service, strports
from twisted.web import server, static, resource

class Root(resource.Resource):
    # child_FOO is a nevow thing, not in twisted.web.resource thing
    def __init__(self):
        resource.Resource.__init__(self)
        self.putChild("", static.Data("Hello\n", "text/plain"))

class WebPort(service.MultiService):
    def __init__(self, basedir, node, db):
        service.MultiService.__init__(self)
        self.basedir = basedir
        self.node = node
        self.db = db

        webport = str(node.get_node_config("webport"))
        root = Root()
        site = server.Site(root)
        s = strports.service(webport, site)
        s.setServiceParent(self)

    def startService(self):
        service.MultiService.startService(self)
        # TODO: now update the webport, if we started with port=0


