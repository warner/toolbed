
import time
import collections
from twisted.application import service
from twisted.python import log
from twisted.internet import protocol, endpoints, reactor
from twisted.protocols import basic
from ed25519 import create_keypair
from .netstring import make_netstring, split_netstrings

class Connection(basic.NetstringReceiver):
    def stringReceived(self, msg):
        try:
            messages = split_netstrings(msg)
        except ValueError:
            log.msg("malformed netstring received")
            self.transport.loseConnection()
            return
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
        self.vk_s = str(c.fetchone()[0])
        self.send_message_to_relay("subscribe", self.vk_s)


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

    def message_received(self, p, messages):
        assert str(messages[0]) == "send"
        assert str(messages[1]) == self.vk_s
        print "MSG", str(messages[2])

    def control_sendMessage(self, args):
        print "SENDMESSAGE", args
        msg_to = str(args["to"])
        msg_body = str(args["message"])
        self.send_message_to_relay("send", msg_to, msg_body)

    def control_startInvitation(self, args):
        print "startInvitation"

    def control_sendInvitation(self, args):
        sent = time.time()
        expires = sent + 60
        petname = str(args["name"])
        isk,ivk = create_keypair()
        private_code = isk.to_ascii(prefix="is0", encoding="base32")
        code = ivk.to_ascii(prefix="i0", encoding="base32")
        print "sendInvitation", petname
        c = self.db.cursor()
        c.execute("INSERT INTO `pending_invitations` VALUES (?,?,?,?,?)",
                  (sent, expires, petname, private_code, code))
        self.db.commit()

    def control_cancelInvitation(self, invite):
        print "cancelInvitation", invite
        c = self.db.cursor()
        c.execute("DELETE FROM `pending_invitations`"
                  " WHERE `petname`=? AND `code`=?",
                  (str(invite["petname"]), str(invite["code"])))
        self.db.commit()

    def control_getPendingInvitationsJSONable(self):
        c = self.db.cursor()
        c.execute("SELECT `sent`,`expires`,`petname`,`code`"
                  " FROM `pending_invitations`"
                  " ORDER BY `sent` DESC")
        data = [{ "sent": float(row[0]),
                  "expires": float(row[1]),
                  "petname": str(row[2]),
                  "code": str(row[3]),
                  } for row in c.fetchall()]
        return data
