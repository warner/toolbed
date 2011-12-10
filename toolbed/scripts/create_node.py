import os, sys
from .. import database

def create_node(so, stdout, stderr):
    basedir = so["basedir"]
    if os.path.exists(basedir):
        print >>stderr, "basedir '%s' already exists, refusing to touch it" % basedir
        return 1
    os.mkdir(basedir)
    sqlite, db = database.get_db(os.path.join(basedir, "toolbed.db"), stderr)
    c = db.cursor()
    c.execute("INSERT INTO node (webport) VALUES (?)", (so["webport"],))
    db.commit()
    print >>stdout, "node created in %s" % basedir
    return 0

