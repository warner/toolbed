
# wait for the node to start up, by polling the web port

# TODO: handle 'restart' correctly by writing something into the DB to
# distinguish between the old node and the new one. Maybe.

import urllib, time

def wait(rooturl):
    max_tries = 1000
    while max_tries > 0:
        try:
            urllib.urlopen(rooturl)
            return
        except IOError:
            time.sleep(0.1)
            max_tries -= 1
    raise RuntimeError("gave up after 100s")
