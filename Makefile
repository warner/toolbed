
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

# note: building pynacl requires swig to be installed. Both pynacl and
# ed25519 require python-dev (headers).
VIRTUALENV=virtualenv-1.9.1/virtualenv.py
PIP=venv/bin/pip
venv: Makefile support/virtualenv-1.9.1.tar.gz support/pynacl-minimal-6ef7f091.tar.gz support/python-ed25519-1.1.tar.gz
	tar xf support/virtualenv-1.9.1.tar.gz
	$(PYTHON) $(VIRTUALENV) --never-download --system-site-packages venv
	$(PIP) install support/python-ed25519-1.1.tar.gz
	$(PIP) install support/pynacl-minimal-6ef7f091.tar.gz

clean:
	-rm -rf venv virtualenv-1.9.1
