
.PHONY: c1 c2 relay
c1:
	-./tool stop c1
	rm -rf c1
	./tool create-node c1
c2:
	-./tool stop c2
	rm -rf c2
	./tool create-node c2
relay:
	-./tool stop relay
	rm -rf relay
	./tool create-relay relay

stop-all:
	-./tool stop c1
	-./tool stop c2
	-./tool stop relay
bounce-all:
	-./tool restart relay
	sleep 1
	-./tool restart c1
	-./tool restart c2
bounce:
	-./tool restart c1
	-./tool restart c2

