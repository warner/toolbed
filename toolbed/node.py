from twisted.application import service

class Node(service.MultiService):
    def __init__(self, basedir, dbfile):
        service.MultiService.__init__(self)

    def startService(self):
        print "NODE STARTED"
        service.MultiService.startService(self)

