import unittest

from ..invitation import OutboundInvitation
from ..base32 import b2a

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
