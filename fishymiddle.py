# fishymiddle.py -- middleware for multi-fishybox environments

import rpyc


boxes = {}


class BoxHandlerService(rpyc.Service):
    def on_connect(self):
        self._name = "---"

    def on_disconnect(self):
        global boxes
        del boxes[self._name]

    def exposed_register(self, name):
        global boxes
        self._name = name
        print "Registered: %s" % self._name
        boxes[self._name] = self

    def exposed_log(self, msg):
        print msg


if __name__ == '__main__':
    from rpyc.utils.server import ThreadedServer
    t = ThreadedServer(BoxHandlerService, port=12344)
    t.start()
