import collections
from twisted.application import service
from twisted.python import log
from twisted.internet import protocol, endpoints, reactor
from twisted.protocols import basic
from .netstring import make_netstring, split_netstrings
from . import invitation

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
        to = str(messages[1])
        #assert to == self.vk_s
        print "MSG", str(messages[2])

        for i in (self.current_outbound_invitations
                  + self.current_inbound_invitations):
            if to == i.get_my_address():
                i.rx_message(*messages[2:])

    def control_sendMessage(self, args):
        print "SENDMESSAGE", args
        msg_to = str(args["to"])
        msg_body = str(args["message"])
        self.send_message_to_relay("send", msg_to, msg_body)

    def control_startInvitation(self, args):
        print "startInvitation"

    def control_sendInvitation(self, args):
        petname = str(args["name"])
        # in the medium-size code protocol, the invitation code I is just a
        # random string.
        print "sendInvitation", petname
        BALICE = "balice" # this is what the recipient gets
        invitation.create_outbound(petname, self, BALICE)
        self.subscribe_to_all_pending_invitations()
        # when this XHR returns, the JS client will fetch the pending
        # invitation list and show the most recent entry

    def current_outbound_invitations(self):
        c = self.db.cursor()
        c.execute("SELECT * FROM `outbound_invitations`")
        return [invitation.OutboundInvitation(self,row)
                for row in c.fetchall()]

    def current_inbound_invitations(self):
        c = self.db.cursor()
        c.execute("SELECT * FROM `inbound_invitations`")
        return [invitation.InboundInvitation(self,row,None)
                for row in c.fetchall()]


    def subscribe_to_all_pending_invitations(self):
        for i in self.current_outbound_invitations():
            self.send_message_to_relay("subscribe", i.get_my_address())
        for i in self.current_inbound_invitations():
            self.send_message_to_relay("subscribe", i.get_my_address())
        # TODO: when called by startInvitation, it'd be nice to sync here: be
        # certain that the relay server has received our subscription
        # request, before returning to startInvitation and allowing the user
        # to send the invite code. If they stall for some reason, we might
        # miss the response.

    def control_cancelInvitation(self, invite):
        print "cancelInvitation", invite
        c = self.db.cursor()
        c.execute("DELETE FROM `outbound_invitations`"
                  " WHERE `petname`=? AND `code`=?",
                  (str(invite["petname"]), str(invite["code"])))
        self.db.commit()

    def control_acceptInvitation(self, invite):
        print "acceptInvitation", invite["name"], invite["code"]
        ABOB = "abob" # this is what the sender gets
        invitation.accept_invitation(invite["name"], invite["code"], ABOB, self)

    def control_getOutboundInvitationsJSONable(self):
        data = [{ "sent": i.sent,
                  "expires": i.expires,
                  "petname": i.petname,
                  "code": i.code,
                  "stage": i.stage,
                  } for i in self.current_outbound_invitations()]
        data.sort(key=lambda d: d["sent"], reverse=True)
        return data
