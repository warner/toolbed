import os, time, signal
from twisted.scripts import twistd
from twisted.python import usage

# by the time 'tool start' is safe to run, all our dependencies are
# available, so these imports are allowed to pull in everything

from .. import node

class MyTwistdConfig(twistd.ServerOptions):
    subCommands = [("XYZ", None, usage.Options, "node")]

class MyPlugin:
    tapname = "xyznode"
    def __init__(self, ser):
        self.ser = ser
    def makeService(self, so):
        return self.ser

def start(so, out, err):
    basedir = os.path.abspath(so["basedir"])
    dbfile = os.path.join(basedir, "toolbed.db")
    if not (os.path.isdir(basedir) and os.path.exists(dbfile)):
        print >>err, "'%s' doesn't look like a toolbed basedir, quitting" % basedir
        return 1
    # now prepare to turn into a twistd process
    os.chdir(basedir)
    n = node.Node(basedir, dbfile) # this is the Service
    twistd_args = so.twistd_args + ("XYZ",)
    twistd_config = MyTwistdConfig()
    try:
        twistd_config.parseOptions(twistd_args)
    except usage.error, ue:
        print twistd_config
        print "tool %s: %s" % (so.subCommand, ue)
        return 1
    twistd_config.loadedPlugins = {"XYZ": MyPlugin(n)}
    # this spawns off a child process, and the parent calls os._exit(0), so
    # there's no way for us to get control afterwards, even with 'except
    # SystemExit'. So if we want to do anything with the running child, we
    # have two options:
    #  * fork first, and have our child wait for the runApp() child to get
    #    running. (note: just fork(). This is easier than fork+exec, since we
    #    don't have to get PATH and PYTHONPATH set up, since we're not
    #    starting a *different* process, just cloning a new instance of the
    #    current process)
    #  * or have the user run a separate command some time after this one
    #    exits.
    print "starting node in %s" % basedir
    twistd.runApp(twistd_config)

def stop(so, out, err):
    basedir = so["basedir"]
    dbfile = os.path.join(basedir, "toolbed.db")
    if not (os.path.isdir(basedir) and os.path.exists(dbfile)):
        print >>err, "'%s' doesn't look like a toolbed basedir, quitting" % basedir
        return 1
    print >>out, "STOPPING", basedir
    pidfile = os.path.join(basedir, "twistd.pid")
    if not os.path.exists(pidfile):
        print >>err, "%s does not look like a running node directory (no twistd.pid)" % basedir
        # we define rc=2 to mean "nothing is running, but it wasn't me who
        # stopped it"
        return 2
    pid = open(pidfile, "r").read()
    pid = int(pid)

    # kill it hard (SIGKILL), delete the twistd.pid file, then wait for the
    # process itself to go away. If it hasn't gone away after 20 seconds, warn
    # the user but keep waiting until they give up.
    try:
        os.kill(pid, signal.SIGKILL)
    except OSError, oserr:
        if oserr.errno == 3:
            print oserr.strerror
            # the process didn't exist, so wipe the pid file
            os.remove(pidfile)
            return 2
        else:
            raise
    try:
        os.remove(pidfile)
    except EnvironmentError:
        pass
    start = time.time()
    time.sleep(0.1)
    wait = 40
    first_time = True
    while True:
        # poll once per second until we see the process is no longer running
        try:
            os.kill(pid, 0)
        except OSError:
            print >>out, "process %d is dead" % pid
            return
        wait -= 1
        if wait < 0:
            if first_time:
                print >>err, ("It looks like pid %d is still running "
                              "after %d seconds" % (pid,
                                                    (time.time() - start)))
                print >>err, "I will keep watching it until you interrupt me."
                wait = 10
                first_time = False
            else:
                print >>err, "pid %d still running after %d seconds" % \
                      (pid, (time.time() - start))
                wait = 10
        time.sleep(1)
    # we define rc=1 to mean "I think something is still running, sorry"
    return 1


def restart(so, out, err):
    stop(so, out, err)
    return start(so, out, err)
