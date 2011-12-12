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
        return b2a(ahash(2, self.code_binary))

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
        self.abob = str(db_row[5])
        self.balice = str(db_row[6])

    def expired(self, clock=time.time):
        return bool(self.expires < clock())
    def get_my_address(self):
        return self.get_sender_address()

    def rx_message(self, h, msg):
        db = self.client.db
        c = db.cursor()
        messages = self.unpack_messages(h, msg)
        if self.stage == 0:
            # we expect M1: (0,A2,A[bob])
            msgnum,addr,abob = messages
            if msgnum != "0":
                raise ValueError("unexpected message number")
            # now send M2
            h,m = self.pack_messages("1", self.balice)
            self.client.send_message_to_relay("send", addr, h, m)
            c.execute("UPDATE `outbound_invitations`"
                      " SET `stage`=2, `abob`=?"
                      " WHERE `petname`=? AND `code`=?",
                      (abob, self.petname, self.code))
            db.commit()
        elif self.stage == 2:
            # we expect M3, just an ACK: (2)
            msgnum, = messages
            if msgnum != "2":
                raise ValueError("unexpected message number")
            self.client.add_addressbook_entry(self.petname, self.abob)
            c.execute("DELETE FROM `outbound_invitations`"
                      " WHERE `petname`=? and `code`=?",
                      (self.petname, self.code))
            db.commit()

def create_outbound(petname, client, balice):
    sent = time.time()
    expires = sent+24*60*60
    code = b2a(os.urandom(256/8))
    stage = 0
    i = OutboundInvitation(client, (sent, expires, petname, code, stage,
                                    "", balice))
    db = client.db
    c = db.cursor()
    c.execute("INSERT INTO `outbound_invitations`"
              " VALUES (?,?,?,?,?,?,?)",
              (sent, expires, petname, code, 0, "", balice))
    db.commit()
    return i

class InboundInvitation(Common):
    def __init__(self, client, db_row, abob):
        self.client = client
        self.petname = str(db_row[0])
        self.code = str(db_row[1])
        self.code_binary = a2b(self.code)
        self.receiver_address = str(db_row[2])
        self.abob = abob

    def start(self):
        addr = self.get_sender_address()
        h,m = self.pack_messages("0", self.receiver_address, self.abob)
        self.client.send_message_to_relay("send", addr, h, m)

    def get_my_address(self):
        return self.receiver_address

    def rx_message(self, h, msg):
        messages = self.unpack_messages(h, msg)
        # We're created by M0, so we only have one stage here. We expect M2:
        # (1,B[alice]), and respond with M3 (the ACK)
        msgnum,balice = messages
        if msgnum != "1":
            raise ValueError("unexpected message number")
        self.client.add_addressbook_entry(self.petname, balice)
        addr = self.get_sender_address()
        h,m = self.pack_messages("2")
        self.client.send_message_to_relay("send", addr, h, m)
        db = self.client.db
        c = db.cursor()
        c.execute("DELETE FROM `inbound_invitations`"
                  " WHERE `petname`=? AND `code`=?",
                  (self.petname, self.code))
        db.commit()


def accept_invitation(petname, code, abob, client):
    receiver_address = b2a(os.urandom(256/8))
    i = InboundInvitation(client, (petname, code, receiver_address), abob)
    db = client.db
    c = db.cursor()
    c.execute("INSERT INTO `inbound_invitations`"
              " VALUES (?,?,?,?)",
              (petname, code, receiver_address))
    db.commit()
    i.start(client)
    return i
