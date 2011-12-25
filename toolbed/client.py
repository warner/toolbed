import re
import collections
import weakref
import json
from twisted.application import service
from twisted.python import log
from twisted.internet import protocol, reactor
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
        self.factory.client.message_received(self, messages)

class ConnectionFactory(protocol.ReconnectingClientFactory):
    protocol = Connection

    def buildProtocol(self, addr):
        p = protocol.ReconnectingClientFactory.buildProtocol(self, addr)
        self.resetDelay()
        reactor.callLater(0, self.client.connected, p)
        return p

    def clientConnectionLost(self, connector, unused_reason):
        protocol.ReconnectingClientFactory.clientConnectionLost(self, connector, unused_reason)
        self.client.disconnected()


class Client(service.MultiService):
    def __init__(self, db):
        service.MultiService.__init__(self)
        self.db = db
        c = self.db.cursor()
        c.execute("SELECT `relay_location` FROM `client_config`")
        relay_location = str(c.fetchone()[0])
        # I'd prefer to use:
        #
        #  self.endpoint = endpoints.clientFromString(reactor, relay_location)
        #
        # but endpoints don't play nicely with the ReconnectingClientFactory
        # that I need. So we manually parse out "tcp:host=HOST:port=PORT" and
        # build a boring old-style connection out of that
        mo = re.search(r'^tcp:host=([^:]+):port=(\d+)$', relay_location)
        if not mo:
            raise ValueError("unable to parse relay_location '%s'" % relay_location)
        self.relay_host = mo.group(1)
        self.relay_port = int(mo.group(2))
        self.factory = ConnectionFactory()
        self.factory.client = self
        self.connection = None

        self.pending_messages = collections.deque()

        self.subscribers = weakref.WeakKeyDictionary()

        c.execute("SELECT `pubkey` FROM `client_config`");
        self.vk_s = str(c.fetchone()[0])
        self.send_message_to_relay("subscribe", self.vk_s)

    def startService(self):
        service.MultiService.startService(self)
        reactor.connectTCP(self.relay_host, self.relay_port, self.factory)

    def connected(self, connection):
        self.connection = connection
        self.maybe_send_messages()
        self.notify("relay-connection-changed", True)

    def disconnected(self):
        self.connection = None
        self.notify("relay-connection-changed", False)

    def maybe_send_messages(self):
        while self.connection and self.pending_messages:
            m = self.pending_messages.popleft()
            self.connection.sendString(m)

    def send_message_to_relay(self, *messages):
        msg = "".join([make_netstring(m) for m in messages])
        self.pending_messages.append(msg)
        self.maybe_send_messages()

    def message_received(self, p, messages):
        assert str(messages[0]) == "send"
        to = str(messages[1])
        #assert to == self.vk_s
        print "MSG", str(messages[2])

        for i in (self.current_outbound_invitations()
                  + self.current_inbound_invitations()):
            if to == i.get_my_address():
                i.rx_message(*messages[2:])

    def add_addressbook_entry(self, petname, payload_data):
        data = json.loads(payload_data.decode("utf-8"))
        c = self.db.cursor()
        c.execute("INSERT INTO `addressbook` VALUES (?,?,?)",
                  (petname, data["my-name"], data["my-icon"]))
        self.db.commit()
        self.notify("invitations-changed", None)
        self.notify("address-book-changed", None)

    def control_relayConnected(self):
        return bool(self.connection)

    def control_getProfileName(self):
        c = self.db.cursor()
        c.execute("SELECT `name` FROM `client_profile`")
        return c.fetchone()[0]

    def control_setProfileName(self, args):
        c = self.db.cursor()
        c.execute("UPDATE `client_profile` SET `name`=?", (args["name"],))
        self.db.commit()

    def control_getProfileIcon(self):
        c = self.db.cursor()
        c.execute("SELECT `icon_data` FROM `client_profile`")
        return c.fetchone()[0]

    def control_setProfileIcon(self, args):
        c = self.db.cursor()
        c.execute("UPDATE `client_profile` SET `icon_data`=?",
                  (args["icon-data"],))
        self.db.commit()

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
        payload = {"my-name": self.control_getProfileName(),
                   "my-icon": self.control_getProfileIcon(),
                   # TODO: passing the icon as a data: URL is probably an
                   # attack vector, change it to just pass the data and have
                   # the client add the "data:" prefix
                   }
        forward_payload_data = json.dumps(payload).encode("utf-8")
        invitation.create_outbound(petname, self, forward_payload_data)
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
        payload = {"my-name": self.control_getProfileName(),
                   "my-icon": self.control_getProfileIcon(), # see above
                   }
        reverse_payload_data = json.dumps(payload).encode("utf-8")
        invitation.accept_invitation(invite["name"], invite["code"],
                                     reverse_payload_data, self)

    def control_getOutboundInvitationsJSONable(self):
        data = [{ "sent": i.sent,
                  "expires": i.expires,
                  "petname": i.petname,
                  "code": i.code,
                  "stage": i.stage,
                  } for i in self.current_outbound_invitations()]
        data.sort(key=lambda d: d["sent"], reverse=True)
        return data

    def control_getAddressBookJSONable(self):
        c = self.db.cursor()
        c.execute("SELECT `petname`,`selfname`,`icon_data` FROM `addressbook`"
                  " ORDER BY `petname` ASC")
        data = [{ "petname": str(row[0]),
                  "selfname": str(row[1]),
                  "icon_data": str(row[2]),
                  }
                for row in c.fetchall()]
        return data

    def control_subscribe_events(self, subscriber):
        self.subscribers[subscriber] = None
    def control_unsubscribe_events(self, subscriber):
        self.subscribers.pop(subscriber, None)
    def notify(self, what, data):
        print "NOTIFY", what, data
        for s in self.subscribers:
            msg = json.dumps({"message": data})
            s.event(what, msg) # TODO: eventual-send
