
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

