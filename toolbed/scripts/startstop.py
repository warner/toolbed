
def start(so, stdout, stderr):
    basedir = so["basedir"]
    dbfile = os.path.join(basedir, "toolbed.db")
    if not (os.path.isdir(basedir) and os.path.exists(dbfile)):
        print >>stderr, "'%s' doesn't look like a toolbed basedir, quitting" % basedir
        return 1
    ...

def stop(so, stdout, stderr):
    basedir = so["basedir"]
    dbfile = os.path.join(basedir, "toolbed.db")
    if not (os.path.isdir(basedir) and os.path.exists(dbfile)):
        print >>stderr, "'%s' doesn't look like a toolbed basedir, quitting" % basedir
        return 1
    ...

def restart(so, stdout, stderr):
    stop(so, stdout, stdout)
    return start(so, stdout, stderr)
