
import collections, weakref, time
from twisted.python import log
from twisted.application import service, strports
from twisted.internet.protocol import ServerFactory
from twisted.protocols.basic import NetstringReceiver
from .netstring import make_netstring, split_netstrings

class RelayProtocol(NetstringReceiver):
    def stringReceived(self, msg):
        try:
            messages = split_netstrings(msg)
        except ValueError:
            log.msg("malformed netstring received")
            self.sendString("".join([make_netstring("error"),
                                     make_netstring("disconnecting\n")]))
            self.transport.loseConnection()
            return
        self.service.client_message(self, messages)

class RelayService(service.MultiService, ServerFactory):
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
        p.service = self
        self.clients[p] = {"from": addr,
                           "connected": time.time(),
                           "rx": 0,
                           "tx": 0,
                           "subscriptions": set()}
        return p

    def get_clients_jsonable(self):
        data = []
        for c in self.clients.values():
            r = {}
            for k,v in c.items():
                if k == "from":
                    v = str(v)
                if k == "subscriptions":
                    v = list(v)
                r[k] = v
            data.append(r)
        return data

    def client_message(self, p, messages):
        self.clients[p]["rx"] += 1
        command = messages[0]
        if command == "subscribe":
            address = messages[1]
            self.subscriptions[address][p] = None
            self.clients[p]["subscriptions"].add(address)
        elif command == "send":
            address = messages[1]
            for p in self.subscriptions[address].keys():
                p.sendString("".join([make_netstring(m) for m in messages]))
                self.clients[p]["tx"] += 1
        print self.clients.values()
