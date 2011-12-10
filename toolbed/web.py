import os
from twisted.application import service, strports
from twisted.web import server, static, resource
from .nonce import make_nonce

def media(media_filename):
    fn = os.path.join(os.path.dirname(__file__), "media", media_filename)
    f = open(fn, "rb")
    #data = f.read().decode("utf-8")
    data = f.read()
    f.close()
    return data

class Control(resource.Resource):
    def __init__(self, db):
        resource.Resource.__init__(self)
        self.db = db
        self.tokens = set()
    def render_GET(self, request):
        request.setHeader("content-type", "text/plain")
        if "nonce" not in request.args:
            return "Please use 'tool open' to get to the control panel\n"
        nonce = request.args["nonce"][0]
        c = self.db.cursor()
        c.execute("SELECT nonce FROM webui_initial_nonces")
        nonces = [str(row[0]) for row in c.fetchall()]
        if nonce not in nonces:
            return ("Sorry, that nonce is expired or invalid,"
                    " please run 'tool open' again\n")
        # good nonce, single-use
        c.execute("DELETE FROM webui_initial_nonces WHERE nonce=?", (nonce,))
        self.db.commit()
        # this token lasts as long as the node is running
        token = make_nonce()
        self.tokens.add(token)
        request.setHeader("content-type", "text/html")
        return media("login.html") % token

    def render_POST(self, request):
        token = request.args["token"][0]
        if token not in self.tokens:
            request.setHeader("content-type", "text/plain")
            return ("Sorry, this session token is expired,"
                    " please run 'tool open' again\n")
        return "Token is good, now let's get down to business!\n"


class Root(resource.Resource):
    # child_FOO is a nevow thing, not in twisted.web.resource thing
    def __init__(self, db):
        resource.Resource.__init__(self)
        self.putChild("", static.Data("Hello\n", "text/plain"))
        self.putChild("control", Control(db))

class WebPort(service.MultiService):
    def __init__(self, basedir, node, db):
        service.MultiService.__init__(self)
        self.basedir = basedir
        self.node = node
        self.db = db

        webport = str(node.get_node_config("webport"))
        root = Root(db)
        site = server.Site(root)
        s = strports.service(webport, site)
        s.setServiceParent(self)

    def startService(self):
        service.MultiService.startService(self)
        # TODO: now update the webport, if we started with port=0


