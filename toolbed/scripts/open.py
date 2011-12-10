
import os
import webbrowser
from . import webwait
from .. import database

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
    URL = "http://localhost:%d/" % portnum
    webwait.wait(URL)
    print "Node appears to be running, opening browser"
    webbrowser.open(URL)
