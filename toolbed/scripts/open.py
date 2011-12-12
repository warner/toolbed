
import os
import webbrowser
from . import webwait
from .. import database, nonce

def open_control_panel(so, out, err):
    basedir = os.path.abspath(so["basedir"])
    dbfile = os.path.join(basedir, "toolbed.db")
    if not (os.path.isdir(basedir) and os.path.exists(dbfile)):
        print >>err, "'%s' doesn't look like a toolbed basedir, quitting" % basedir
        return 1
    sqlite, db = database.get_db(dbfile, err)
    c = db.cursor()
    c.execute("SELECT webport FROM node LIMIT 1")
    (webport,) = c.fetchone()
    parts = webport.split(":")
    assert parts[0] == "tcp"
    portnum = int(parts[1])
    baseurl = "http://localhost:%d/" % portnum
    webwait.wait(baseurl)
    print "Node appears to be running, opening browser"
    c.execute("SELECT name FROM services")
    services = set([str(row[0]) for row in c.fetchall()])
    if "relay" in services:
        url = baseurl+"relay"
    else:
        n = nonce.make_nonce()
        c.execute("INSERT INTO webui_initial_nonces VALUES (?)", (n,))
        db.commit()
        url = baseurl+"control?nonce=%s" % n
    if so["no-open"]:
        print >>out, "Please open: %s" % url
    else:
        webbrowser.open(url)
