
import collections
from twisted.application import service
from twisted.python import log
from twisted.internet import protocol, endpoints, reactor
from twisted.protocols import basic
from .netstring import make_netstring, split_netstrings

class Connection(basic.NetstringReceiver):
    def stringReceived(self, msg):
        try:
            messages = split_netstrings(msg)
        except ValueError:
            log.msg("malformed netstring received")
            self.transport.loseConnection()
        self.factory.message_received(self, messages)

class Client(service.MultiService, protocol.ClientFactory):
    protocol = Connection

    def __init__(self, db):
        service.MultiService.__init__(self)
        self.db = db
        c = self.db.cursor()
        c.execute("SELECT `relay_location` FROM `client_config`")
        relay_location = str(c.fetchone()[0])
        self.endpoint = endpoints.clientFromString(reactor, relay_location)
        self.connection = None

        self.pending_messages = collections.deque()

        c.execute("SELECT `pubkey` FROM `client_config`");
        self.sk_s = str(c.fetchone()[0])
        self.send_message_to_relay("subscribe", self.sk_s)


    def maybe_send_messages(self):
        if not self.connection:
            d = self.endpoint.connect(self)
            reactor.callLater(30, d.cancel)
            d.addCallback(self.connected)
            d.addErrback(self.connect_failed)
            return
        while self.pending_messages:
            m = self.pending_messages.popleft()
            self.connection.sendString(m)

    def connected(self, connection):
        self.connection = connection
        self.maybe_send_messages()

    def connect_failed(self, why):
        log.err(why, "connection failed")

    def send_message_to_relay(self, *messages):
        msg = "".join([make_netstring(m) for m in messages])
        self.pending_messages.append(msg)
        self.maybe_send_messages()

    def message_received(self, messages):
        print "RECEIVED", messages

    def control_sendMessage(self, args):
        print "SENDMESSAGE", args
