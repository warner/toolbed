import os.path
import unittest
import collections

from .. import invitation
from ..invitation import OutboundInvitation
from ..base32 import b2a, a2b
from ..client import Client
from .. import database
from ..scripts.create_node import create_node
from ..netstring import split_netstrings

class Outbound(unittest.TestCase):
    def test_create(self):
        now = 1234567
        i = OutboundInvitation(None,
                               (now, now+300, "Alice", b2a("code_binary"), 0,
                                "abob", "balice") )
        self.failUnlessEqual(i.sent, now)
        self.failUnlessEqual(i.expires, now+300)
        self.failUnlessEqual(i.code, b2a("code_binary"))
        self.failUnlessEqual(i.code_binary, "code_binary")
        self.failUnlessEqual(i.stage, 0)
        self.failUnlessEqual(i.abob, "abob")
        self.failUnlessEqual(i.balice, "balice")

        def nowclock():
            return now
        def futureclock():
            return now + 500
        self.failIf(i.expired(nowclock))
        self.failUnless(i.expired(futureclock))
        self.failUnlessEqual(i.get_my_address(), "ihraxtbpsuxoohiuzjy646zkk5bh25e7gpyhwtpessv2ywn46bvq")
        self.failUnlessEqual(b2a(i.get_hmac_key()), "fvyuhvbg567wpixb5lzodtkvhpmfccwdrlp5a6zf7vvvqvlhhshq")

        h1,m1 = i.pack_messages("1", "hello world")
        m2 = i.unpack_messages(h1,m1)
        self.failUnlessEqual(list(m2), ["1", "hello world"])
        otherh,otherm = i.pack_messages("different message")
        self.failUnlessRaises(ValueError, i.unpack_messages, otherh, m1)

    def test_key(self):
        now = 1234567
        i1 = OutboundInvitation(None,
                                (now, now+300, "Alice", b2a("code_binary"), 0,
                                 "abob", "balice") )
        i2 = OutboundInvitation(None,
                                (now, now+300, "Alice", b2a("othercode"), 0,
                                 "abob", "balice") )

        h1,m1 = i1.pack_messages("stuff")
        self.failUnlessRaises(ValueError, i2.unpack_messages, h1, m1)

def testfilepath(*names):
    expanded = []
    for n in names:
        if isinstance(n, (tuple,list)):
            expanded.extend(list(n))
        else:
            expanded.append(n)
    names = expanded
    for i in range(1,len(names)):
        dirname = os.path.join(*names[:i])
        if not os.path.isdir(dirname):
            os.mkdir(dirname)
    return os.path.abspath(os.path.join(*names))

class Nexus:
    def __init__(self):
        self.subscriptions = collections.defaultdict(set)
    def send(self, c, m):
        messages = split_netstrings(m)
        if messages[0] == "subscribe":
            self.subscriptions[messages[1]].add(c)
        elif messages[0] == "send":
            for c_to in self.subscriptions[messages[1]]:
                c_to.message_received(c, messages)
        else:
            raise ValueError("unrecognized command %s" % messages[0])

class FakeClient(Client):
    nexus = None
    def maybe_send_messages(self):
        if not self.nexus:
            return
        while self.pending_messages:
            m = self.pending_messages.popleft()
            self.nexus.send(self, m)
    def message_received(self, fromwho, messages):
        Client.message_received(self, fromwho, messages)
        self.log.append((fromwho, messages))
    def add_addressbook_entry(self, petname, data):
        self.book.append( (petname,data) )

class Roundtrip(unittest.TestCase):
    def mkfile(self, *names):
        return testfilepath("_test", *names)

    def create_clients(self, *names):
        base = os.path.join("_test", *names)
        self.mkfile(names, "dummy")
        create_node({"basedir": os.path.join(base, "c1"),
                     "webport": "0",
                     "relay": "tcp:host=localhost:port=0"})
        dbfile1 = self.mkfile(names, "c1", "toolbed.db")
        c1 = FakeClient(database.get_db(dbfile1)[1])

        create_node({"basedir": os.path.join(base, "c2"),
                     "webport": "0",
                     "relay": "tcp:host=localhost:port=0"})
        dbfile2 = self.mkfile(names, "c2", "toolbed.db")
        c2 = FakeClient(database.get_db(dbfile2)[1])

        n = Nexus()
        c1.nexus = n; c1.log = []; c1.book = []
        c2.nexus = n; c2.log = []; c2.book = []
        c1.maybe_send_messages(); c2.maybe_send_messages()
        self.c1 = c1
        self.c2 = c2
        self.n = n

    def test_contact(self):
        self.create_clients("invitation", "Roundtrip", "contact")
        c1,c2 = self.c1,self.c2
        c1.send_message_to_relay("send", c2.vk_s, "hello")
        self.failUnlessEqual(len(c2.log), 1)
        self.failUnlessEqual(c2.log[-1][0], c1)
        self.failUnlessEqual(c2.log[-1][1], ["send", c2.vk_s, "hello"])

    def test_invite(self):
        self.create_clients("invitation", "Roundtrip", "invite")
        c1,c2,n = self.c1,self.c2,self.n
        c1.control_sendInvitation({"name": "c2"})
        data = c1.control_getOutboundInvitationsJSONable()
        self.failUnlessEqual(len(data), 1)
        self.failUnlessEqual(data[0]["petname"], "c2")
        code = data[0]["code"]
        # c1 should have subscribed to hear about its channel by now
        com = invitation.Common() ; com.code_binary = a2b(code)
        c1_channel = com.get_sender_address()
        self.failUnless(c1_channel in n.subscriptions)
        self.failUnlessEqual(n.subscriptions[c1_channel], set([c1]))

        # all protocol messages complete inside this call
        c2.control_acceptInvitation({"name": "c1", "code": code})

        self.failUnlessEqual(c1.book, [("c2", "abob")])
        self.failUnlessEqual(c2.book, [("c1", "balice")])
