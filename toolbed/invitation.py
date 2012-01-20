import os
from hashlib import sha256
import time
import hmac
from .base32 import b2a, a2b
from .netstring import make_netstring, split_netstrings

def ahash(which, s):
    return sha256("%d:%s" % (which,s)).digest()

def get_hmac_key(code_ascii):
    return ahash(1, a2b(code_ascii))
def get_sender_address(code_ascii):
    return "channel-"+b2a(ahash(2, a2b(code_ascii)))

def pack_messages(code_ascii, *messages):
    msg = "".join([make_netstring(m) for m in messages])
    h = hmac.HMAC(get_hmac_key(code_ascii), msg, sha256).digest()
    return b2a(h), msg

def unpack_messages(code_ascii, h, msg):
    h1 = hmac.HMAC(get_hmac_key(code_ascii), msg, sha256).digest()
    if h != b2a(h1):
        raise ValueError("bad HMAC, corrupted message")
    messages = split_netstrings(msg)
    return messages


def create_outbound(db, petname, forward_payload):
    sent = time.time()
    expires = sent+24*60*60
    code_ascii = b2a(os.urandom(256/8))
    address = get_sender_address(code_ascii)
    stage = 0
    c = db.cursor()
    c.execute("INSERT INTO `outbound_invitations`"
              " VALUES (?,?,?,?,?,?, ?,?)",
              (address, sent, expires, petname, code_ascii, stage,
               forward_payload, ""))
    db.commit()
    return {"code": code_ascii}

def process_outbound(db, row, h, msg):
    petname = str(row[3])
    code_ascii = str(row[4])
    stage = int(row[5])
    forward_payload = str(row[6])
    reverse_payload = str(row[7])

    outmsgs = []
    newentry = None

    c = db.cursor()
    messages = unpack_messages(code_ascii, h, msg)
    if stage == 0:
        # we expect M1: (1,A2,A[bob])
        msgnum,addr,reverse_payload = messages
        if msgnum != "1":
            raise ValueError("unexpected message number")
        c.execute("UPDATE `outbound_invitations`"
                  " SET `stage`=2, `reverse_payload`=?"
                  " WHERE `petname`=? AND `code`=?",
                  (reverse_payload, petname, code_ascii))
        db.commit()
        # now send M2
        h,m = pack_messages(code_ascii, "2", forward_payload)
        outmsgs.append( ("send", addr, h, m) )
    elif stage == 2:
        # we expect M3, just an ACK: (3)
        msgnum, = messages
        if msgnum != "3":
            raise ValueError("unexpected message number")
        newentry = (petname, reverse_payload)
        c.execute("DELETE FROM `outbound_invitations`"
                  " WHERE `petname`=? and `code`=?",
                  (petname, code_ascii))
        db.commit()
    return outmsgs, newentry

def pending_outbound_invitations(db):
    c = db.cursor()
    c.execute("SELECT `sent`,`expires`,`petname`,`code`,`stage`"
              " FROM `outbound_invitations`")
    data = [ { "sent": float(row[0]),
               "expires": float(row[1]),
               "petname": str(row[2]),
               "code": str(row[3]),
               "stage": int(row[4]),
               } for row in c.fetchall() ]
    data.sort(key=lambda d: d["sent"], reverse=True)
    return data

def accept_invitation(db, petname, code_ascii, reverse_payload):
    receiver_address = "channel-"+b2a(os.urandom(256/8))
    c = db.cursor()
    c.execute("INSERT INTO `inbound_invitations` VALUES (?,?,?)",
              (receiver_address, petname, code_ascii))
    db.commit()
    outmsgs = []
    outmsgs.append( ("subscribe", receiver_address) )
    h,m = pack_messages(code_ascii, "1", receiver_address, reverse_payload)
    outmsgs.append( ("send", get_sender_address(code_ascii), h, m) )
    return outmsgs

def process_inbound(db, row, h, msg):
    petname = str(row[1])
    code_ascii = str(row[2])
    messages = unpack_messages(code_ascii, h, msg)
    # We're created by M0, so we only have one stage here. We expect M2:
    # (2,B[alice]), and respond with M3 (the ACK)
    msgnum,forward_payload = messages
    if msgnum != "2":
        raise ValueError("unexpected message number")
    newentry = (petname, forward_payload)
    c = db.cursor()
    c.execute("DELETE FROM `inbound_invitations`"
              " WHERE `petname`=? AND `code`=?",
              (petname, code_ascii))
    db.commit()
    addr = get_sender_address(code_ascii)
    h,m = pack_messages(code_ascii, "3")
    outmsgs = [ ("send", addr, h, m) ]

    return outmsgs, newentry

def addresses_to_subscribe(db):
    addresses = set()
    c = db.cursor()
    c.execute("SELECT * FROM `outbound_invitations`")
    for row in c.fetchall():
        addresses.add(str(row[0]))
    c.execute("SELECT * FROM `inbound_invitations`")
    for row in c.fetchall():
        addresses.add(str(row[0]))
    return addresses
