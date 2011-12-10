#!/usr/bin/env python

import sys

# this 'tool' script is at the top of the source directory, so the source
# directory will automatically be added to sys.path. Thus this should always
# work:
from toolbed.runner import run

# Delegate everything else off to toolbed.runner, which must be careful to
# not import too much unless the command specifically asks for it.

rc = run(sys.argv[1:], sys.stdout, sys.stderr)
sys.exit(rc)
