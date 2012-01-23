
import os, re, json, httplib
from . import webwait
from .. import database, nonce

def send_message(so, out, err):
    basedir = os.path.abspath(so["basedir"])
    dbfile = os.path.join(basedir, "toolbed.db")
    if not (os.path.isdir(basedir) and os.path.exists(dbfile)):
        print >>err, "'%s' doesn't look like a toolbed basedir, quitting" % basedir
        return 1
    sqlite, db = database.get_db(dbfile, err)
    c = db.cursor()
    baseurl = webwait.wait(basedir, err)
    mo = re.search(r':(\d+)/', baseurl)
    portnum = int(mo.group(1))
    assert baseurl.endswith(":%d/" % portnum)

    token = nonce.make_nonce()
    c.execute("INSERT INTO `webui_access_tokens` VALUES (?)", (token,))
    db.commit()
    controlpath = "/control/api"
    body = json.dumps({"token": token,
                       "method": "sendMessage",
                       "args": {"name": so["petname"],
                                "message": so["message"]},
                       }).encode("utf-8")
    c = httplib.HTTPConnection("localhost", portnum)
    c.request("POST", controlpath,
              headers={"Content-Type": "text/json; charset=UTF-8",
                       "Connection": "close"},
              body=body) # c.request adds Content-Length for us
    response = c.getresponse()
    r = json.load(response)
    text = r["text"]
    print "RESPONSE:", text
