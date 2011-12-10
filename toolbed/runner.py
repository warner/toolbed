
# only import stdlib at the top level. Do not import anything from our
# dependency set, or parts of toolbed that require things from the dependency
# set, until runtime, inside a command that specifically needs it.

import os, sys

try:
    from twisted.python import usage
except ImportError:
    print >>sys.stderr, "Unable to import Twisted."
    print >>sys.stderr, "Please run 'python setup.py build'"
    sys.exit(1)

class BasedirParameterMixin:
    optParameters = [
        ("basedir", "d", os.path.expanduser("~/.toolbed"), "Base directory"),
        ]
class BasedirArgument:
    def parseArgs(self, basedir=None):
        if basedir is not None:
            self["basedir"] = basedir

class StartArguments(BasedirArgument):
    def parseArgs(self, basedir=None, *twistd_args):
        self.twistd_args = twistd_args
        BasedirArgument.parseArgs(self, basedir)

class CreateNodeOptions(BasedirParameterMixin, BasedirArgument, usage.Options):
    optParameters = [
        ("webport", "p", "tcp:5775:interface=127.0.0.1",
         "TCP port for the node's HTTP interface."),
        ]

class StartNodeOptions(BasedirParameterMixin, StartArguments, usage.Options):
    optFlags = [
        ("no-open", "n", "Do not automatically open the control panel"),
        ]
class StopNodeOptions(BasedirParameterMixin, BasedirArgument, usage.Options):
    pass
class RestartNodeOptions(BasedirParameterMixin, StartArguments, usage.Options):
    def postOptions(self):
        self["no-open"] = False
class OpenOptions(BasedirParameterMixin, BasedirArgument, usage.Options):
    pass

class Options(usage.Options):
    synopsis = "\nUsage: tool <command>"
    subCommands = [("create-node", None, CreateNodeOptions, "Create a node"),
                   ("start", None, StartNodeOptions, "Start a node"),
                   ("stop", None, StopNodeOptions, "Stop a node"),
                   ("restart", None, RestartNodeOptions, "Restart a node"),
                   ("open", None, OpenOptions, "Open web control panel"),
                   ]

    def getUsage(self, **kwargs):
        t = usage.Options.getUsage(self, **kwargs)
        return t + "\nPlease run 'tool <command> --help' for more details on each command.\n"

    def postOptions(self):
        if not hasattr(self, 'subOptions'):
            raise usage.UsageError("must specify a command")

def create_node(*args):
    from .scripts.create_node import create_node
    return create_node(*args)

def start(*args):
    from .scripts.startstop import start
    return start(*args)

def stop(*args):
    from .scripts.startstop import stop
    return stop(*args)

def restart(*args):
    from .scripts.startstop import restart
    return restart(*args)

def open_control_panel(*args):
    from .scripts.open import open_control_panel
    return open_control_panel(*args)

DISPATCH = {"create-node": create_node,
            "start": start,
            "stop": stop,
            "restart": restart,
            "open": open_control_panel,
            }

def run(args, stdout, stderr):
    config = Options()
    try:
        config.parseOptions(args)
    except usage.error, e:
        c = config
        while hasattr(c, 'subOptions'):
            c = c.subOptions
        print >>stderr, str(c)
        print >>stderr, e.args[0]
        return 1
    command = config.subCommand
    so = config.subOptions
    try:
        rc = DISPATCH[command](so, stdout, stderr)
        return rc
    except ImportError, e:
        print >>stderr, "--- ImportError ---"
        print >>stderr, "Please run 'python setup.py build'"
        return 1
