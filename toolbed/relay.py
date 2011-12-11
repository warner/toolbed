
from twisted.internet.protocol import ServerFactory
from twisted.protocols.basic import NetstringReceiver
from twisted.application import service, strports

class _EmptyTransport:
    def loseConnection(self):
        pass
class _NetstringParser(NetstringReceiver):
    def stringReceived(self, msg):
        self.messages.append(msg)

def make_netstring(msg):
    assert isinstance(msg, str)
    return "%d:%s," % (len(msg), msg)

def split_netstrings(s):
    p = _NetstringParser()
    p.messages = messages = []
    p.makeConnection(_EmptyTransport())
    p.dataReceived(s)
    if p._remainingData:
        raise ValueError("leftover data: %d bytes" % len(p._remainingData))
    return messages

class RelayProtocol(NetstringReceiver):
    def stringReceived(self, msg):
        pass

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
