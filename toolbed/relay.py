
import collections, weakref, time
from twisted.internet.protocol import ServerFactory
from twisted.protocols.basic import NetstringReceiver
from twisted.application import service, strports
from .netstring import split_netstrings

class RelayProtocol(NetstringReceiver):
    def stringReceived(self, msg):
        try:
            messages = split_netstrings(msg)
        except ValueError:
            self.transport.loseConnection()
        self.factory.client_message(self, messages)

class RelayService(ServerFactory, service.MultiService):
    protocol = RelayProtocol

    def __init__(self, db):
        service.MultiService.__init__(self)
        self.db = db
        c = self.db.cursor()
        c.execute("SELECT relayport FROM relay_config")
        relayport = str(c.fetchone()[0])
        s = strports.service(relayport, self)
        s.setServiceParent(self)

        # we use the WeakKeyDictionary as a WeakSet
        self.subscriptions = collections.defaultdict(weakref.WeakKeyDictionary)
        self.clients = weakref.WeakKeyDictionary()

    def buildProtocol(self, addr):
        p = ServerFactory.buildProtocol(self, addr)
        self.clients[p] = {"from": addr, "connected": time.time(),
                           "rx": 0, "tx": 0, "subscriptions": set()}

    def client_message(self, p, messages):
        self.clients[p]["rx"] += 1
        command = messages[0]
        if command == "subscribe":
            address = messages[1]
            self.subscriptions[address][p] = None
            self.clients[p]["subscriptions"].add(address)
        elif command == "send":
            address = messages[1]
            msg = messages[2]
            for p in self.subscriptions[address].keys():
                p.sendString(msg)
                self.clients[p]["tx"] += 1
