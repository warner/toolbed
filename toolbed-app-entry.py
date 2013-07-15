# this is copied into the zipfile's __main__.py

#print "toolbed-app-entry.py"
#import sys, pprint
#print "-- sys.path:"
#pprint.pprint(sys.path)
#print "--"

if 0:
    import sys, toolbed, pprint, zipfile, tempfile
    print toolbed
    pprint.pprint(sys.path)
    print sys.argv[0]
    z = zipfile.ZipFile(sys.argv[0], "r")
    print z
    edso = z.open("ed25519/_ed25519.so","r").read()
    print len(edso)
    tf = tempfile.NamedTemporaryFile()
    tf.write(edso)
    print tf.name
    # TODO: figure out how to dynload this, stuff it in sys.modules, then later
    # when ed25519/keys.py imports _ed25519, it should already be there. Do the
    # same for _nacl.so .
    sys.exit(0)
import sys
from toolbed.scripts.runner import run
rc = run(sys.argv[1:], sys.stdout, sys.stderr)
sys.exit(rc)

