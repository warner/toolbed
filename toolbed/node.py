from twisted.application import service
from . import database, web

class Node(service.MultiService):
    def __init__(self, basedir, dbfile):
        service.MultiService.__init__(self)
        self.basedir = basedir
        self.dbfile = dbfile

        self.sqlite, self.db = database.get_db(dbfile)
        self.init_webport()

    def startService(self):
        print "NODE STARTED"
        service.MultiService.startService(self)

    def get_node_config(self, name):
        c = self.db.cursor()
        c.execute("SELECT %s FROM node LIMIT 1" % name)
        (value,) = c.fetchone()
        return value

    def set_node_config(self, name, value):
        c = self.db.cursor()
        c.execute("UPDATE node SET ?=?", (name, value))
        self.db.commit()

    def init_webport(self):
        w = web.WebPort(self.basedir, self, self.db)
        w.setServiceParent(self)
        # clear initial nonces. It's important to do this before the web port
        # starts listening, to avoid a race with 'tool open' adding a new
        # nonce
        c = self.db.cursor()
        c.execute("DELETE FROM webui_initial_nonces")
        self.db.commit()

