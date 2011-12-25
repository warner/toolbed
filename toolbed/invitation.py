import os
from hashlib import sha256
import time
import hmac
from .base32 import b2a, a2b
from .netstring import make_netstring, split_netstrings

def ahash(which, s):
    return sha256("%d:%s" % (which,s)).digest()

class Common:
    def get_hmac_key(self):
        return ahash(1, self.code_binary)
    def get_sender_address(self):
        return "channel-"+b2a(ahash(2, self.code_binary))

    def pack_messages(self, *messages):
        msg = "".join([make_netstring(m) for m in messages])
        h = hmac.HMAC(self.get_hmac_key(), msg, sha256).digest()
        return b2a(h), msg

    def unpack_messages(self, h, msg):
        h1 = hmac.HMAC(self.get_hmac_key(), msg, sha256).digest()
        if h != b2a(h1):
            raise ValueError("bad HMAC, corrupted message")
        messages = split_netstrings(msg)
        return messages

class OutboundInvitation(Common):
    def __init__(self, client, db_row):
        self.client = client
        self.sent = float(db_row[0])
        self.expires = float(db_row[1])
        self.petname = str(db_row[2])
        self.code = str(db_row[3])
        self.code_binary = a2b(self.code)
        self.stage = int(db_row[4])
        self.forward_payload = str(db_row[5])
        self.reverse_payload = str(db_row[6])

    def expired(self, clock=time.time):
        return bool(self.expires < clock())
    def get_my_address(self):
        return self.get_sender_address()

    def rx_message(self, h, msg):
        db = self.client.db
        c = db.cursor()
        messages = self.unpack_messages(h, msg)
        if self.stage == 0:
            # we expect M1: (1,A2,A[bob])
            msgnum,addr,reverse_payload = messages
            if msgnum != "1":
                raise ValueError("unexpected message number")
            c.execute("UPDATE `outbound_invitations`"
                      " SET `stage`=2, `reverse_payload`=?"
                      " WHERE `petname`=? AND `code`=?",
                      (reverse_payload, self.petname, self.code))
            db.commit()
            # now send M2
            h,m = self.pack_messages("2", self.forward_payload)
            self.client.send_message_to_relay("send", addr, h, m)
        elif self.stage == 2:
            # we expect M3, just an ACK: (3)
            msgnum, = messages
            if msgnum != "3":
                raise ValueError("unexpected message number")
            self.client.add_addressbook_entry(self.petname, self.reverse_payload)
            c.execute("DELETE FROM `outbound_invitations`"
                      " WHERE `petname`=? and `code`=?",
                      (self.petname, self.code))
            db.commit()

def create_outbound(petname, client, forward_payload):
    sent = time.time()
    expires = sent+24*60*60
    code = b2a(os.urandom(256/8))
    stage = 0
    i = OutboundInvitation(client, (sent, expires, petname, code, stage,
                                    forward_payload, ""))
    db = client.db
    c = db.cursor()
    c.execute("INSERT INTO `outbound_invitations`"
              " VALUES (?,?,?,?,?,?,?)",
              (sent, expires, petname, code, 0, forward_payload, ""))
    db.commit()
    return i

class InboundInvitation(Common):
    def __init__(self, client, db_row, reverse_payload):
        self.client = client
        self.petname = str(db_row[0])
        self.code = str(db_row[1])
        self.code_binary = a2b(self.code)
        self.receiver_address = str(db_row[2])
        self.reverse_payload = reverse_payload

    def start(self):
        self.client.send_message_to_relay("subscribe", self.receiver_address)
        addr = self.get_sender_address()
        h,m = self.pack_messages("1", self.receiver_address,
                                 self.reverse_payload)
        self.client.send_message_to_relay("send", addr, h, m)

    def get_my_address(self):
        return self.receiver_address

    def rx_message(self, h, msg):
        messages = self.unpack_messages(h, msg)
        # We're created by M0, so we only have one stage here. We expect M2:
        # (2,B[alice]), and respond with M3 (the ACK)
        msgnum,forward_payload = messages
        if msgnum != "2":
            raise ValueError("unexpected message number")
        self.client.add_addressbook_entry(self.petname, forward_payload)
        db = self.client.db
        c = db.cursor()
        c.execute("DELETE FROM `inbound_invitations`"
                  " WHERE `petname`=? AND `code`=?",
                  (self.petname, self.code))
        db.commit()
        addr = self.get_sender_address()
        h,m = self.pack_messages("3")
        self.client.send_message_to_relay("send", addr, h, m)


def accept_invitation(petname, code, reverse_payload, client):
    receiver_address = "channel-"+b2a(os.urandom(256/8))
    i = InboundInvitation(client, (petname, code, receiver_address),
                          reverse_payload)
    db = client.db
    c = db.cursor()
    c.execute("INSERT INTO `inbound_invitations`"
              " VALUES (?,?,?)",
              (petname, code, receiver_address))
    db.commit()
    i.start()
    return i
