import os, sys

from .. import database, util

def create_node(so, stdout=sys.stdout, stderr=sys.stderr):
    basedir = so["basedir"]
    if os.path.exists(basedir):
        print >>stderr, "basedir '%s' already exists, refusing to touch it" % basedir
        return 1
    os.mkdir(basedir)
    sqlite, db = database.get_db(os.path.join(basedir, "toolbed.db"), stderr)
    c = db.cursor()
    c.execute("INSERT INTO node (webport) VALUES (?)", (so["webport"],))
    c.execute("INSERT INTO services (name) VALUES (?)", ("client",))
    addr = util.to_ascii(os.urandom(32), prefix="addr-", encoding="base32")
    c.execute("INSERT INTO `client_config`"
              " (`address`, `relay_location`) VALUES (?,?)",
              (addr, so["relay"]))
    c.execute("INSERT INTO `client_profile`"
              " (`name`, `icon_data`) VALUES (?,?)",
              ("",""))
    db.commit()
    print >>stdout, "node created in %s" % basedir
    return 0


def create_relay(so, stdout=sys.stdout, stderr=sys.stderr):
    basedir = so["basedir"]
    if os.path.exists(basedir):
        print >>stderr, "basedir '%s' already exists, refusing to touch it" % basedir
        return 1
    os.mkdir(basedir)
    sqlite, db = database.get_db(os.path.join(basedir, "toolbed.db"), stderr)
    c = db.cursor()
    c.execute("INSERT INTO services (name) VALUES (?)", ("relay",))
    c.execute("INSERT INTO node (webport) VALUES (?)", (so["webport"],))
    c.execute("INSERT INTO relay_config (relayport) VALUES (?)",
              (so["relayport"],))
    db.commit()
    print >>stdout, "relay created in %s" % basedir
    return 0

