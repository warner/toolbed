
.PHONY: c1 c2 relay
c1:
	-./bin/tool stop c1
	rm -rf c1
	./bin/tool create-node c1
c2:
	-./bin/tool stop c2
	rm -rf c2
	./bin/tool create-node c2
relay:
	-./bin/tool stop relay
	rm -rf relay
	./bin/tool create-relay relay

stop-all:
	-./bin/tool stop c1
	-./bin/tool stop c2
	-./bin/tool stop relay
bounce-all:
	-./bin/tool restart relay
	sleep 1
	-./bin/tool restart c1
	-./bin/tool restart c2
bounce:
	-./bin/tool restart c1
	-./bin/tool restart c2

# to run this from a source tree, first run "make venv". You will need
# python, python-dev, and swig installed, but nothing else. All other
# dependencies will be downloaded, verified, built, and installed into the
# virtualenv.

# after building, you can use "bin/tool" to start everything

# for development, you can override the contents of the venv by just setting
# PYTHONPATH before running bin/tool. All toolbed source files are imported
# directly from toolbed/ , so changing source files does not require a
# rebuild (just a restart).

# "make app" will generate a single-file executable named "tool" which
# depends upon /usr/bin/python, but nothing else.

# "make mac-app" will create a Mac application bundle which includes a copy
# of that single-file executable, along with a menu item that can start/stop
# the daemon and open the control page.

# note: building pynacl requires swig to be installed. Both pynacl and
# ed25519 require python-dev (headers).
VIRTUALENV=virtualenv-1.9.1/virtualenv.py
PIP=venv/bin/pip
venv: Makefile support/virtualenv-1.9.1.tar.gz support/pynacl-minimal-6ef7f091.tar.gz support/python-ed25519-1.1.tar.gz
	tar xf support/virtualenv-1.9.1.tar.gz
	$(PYTHON) $(VIRTUALENV) --never-download venv
	$(PIP) install support/zope.interface-4.0.5.zip
	$(PIP) install support/Twisted-13.1.0.tar.bz2
	$(PIP) install support/python-ed25519-1.1.tar.gz
	$(PIP) install support/pynacl-minimal-6ef7f091.tar.gz

clean:
	-rm -rf venv virtualenv-1.9.1
