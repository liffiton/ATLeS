import copy
import inspect
import socket
import threading
import time

try:
    from queue import Queue
except ImportError:
    from Queue import Queue

from sqlalchemy import sql
from zeroconf import ServiceBrowser, Zeroconf

from fishweb import db_schema
from fishweb.box_rpc import Box


class BoxManager(object):
    def __init__(self, engine):
        self._engine = engine

        self._boxes = dict()
        self._boxlock = threading.Lock()

        self._updatequeue = Queue()

        # work around a bug in zeroconf on Cygwin
        try:
            zeroconf = Zeroconf()
        except socket.error:
            zeroconf = Zeroconf(["0.0.0.0"])
        self._browser = ServiceBrowser(zeroconf, "_fishbox._tcp.local.", self)  # starts its own daemon thread

        # start polling boxes and the queue in separate threads
        t = threading.Thread(target=self.poll_boxes)
        t.daemon = True
        t.start()
        t = threading.Thread(target=self.watch_queue)
        t.daemon = True
        t.start()

    def add_service(self, zeroconf, type, name):
        ''' Called automatically by ServiceBrowser. '''
        info = zeroconf.get_service_info(type, name)
        print("Service %s added, service info: %s" % (name, info))
        boxname = info.properties[b'name'].decode()
        assert boxname == name.split('.')[0]
        newbox = Box(name=boxname,
                     ip=socket.inet_ntoa(info.address),
                     port=info.port,
                     properties=info.properties
                     )
        # connect in a separate thread so we don't have to wait for the connection here
        threading.Thread(target=newbox.connect, args=[self._updatequeue.put]).start()
        with self._boxlock:
            self._boxes[boxname] = newbox
        self._updatequeue.put(boxname)

    def remove_service(self, zeroconf, type, name):
        ''' Called automatically by ServiceBrowser. '''
        print("Service %s removed" % name)
        boxname = name.split('.')[0]
        with self._boxlock:
            self._boxes[boxname].down()
        self._updatequeue.put(boxname)

    def get_boxes(self):
        with self._boxlock:
            return copy.copy(self._boxes)

    def _update_box(self, box, conn):
        boxes = db_schema.boxes
        # get updated box data
        with self._boxlock:
            if box in self._boxes:
                boxdict = self._boxes[box].as_dict()
            else:
                boxdict = None
        # check whether this box is in the database yet
        select = sql.select([boxes.c.name]).where(boxes.c.name == box)
        box_exists = conn.execute(select).scalar()
        if box_exists:
            # if so, update
            if boxdict is not None:
                update = boxes.update().where(boxes.c.name == box).values(boxdict)
            else:
                update = boxes.update().where(boxes.c.name == box).values(connected=False)
            conn.execute(update)
        else:
            # if not, insert
            insert = boxes.insert(boxdict)
            conn.execute(insert)

    def watch_queue(self):
        # Runs in its own thread
        # Needs a separate sqlite connection for a separate thread
        conn = self._engine.connect()
        while True:
            box = self._updatequeue.get()
            self._update_box(box, conn)

    def poll_boxes(self):
        # Runs in its own thread
        # Needs a separate sqlite connection for a separate thread
        conn = self._engine.connect()
        boxes = db_schema.boxes
        select = sql.select([boxes.c.name])
        while True:
            # Poll/update all boxes every 2 seconds
            box_names = [row['name'] for row in conn.execute(select)]
            # quick sanity check: all boxes in our list of RPC objects must be registered in the DB
            for box in self._boxes:
                assert box in box_names
            for box in box_names:
                self._update_box(box, conn)
            time.sleep(2)


class BoxRPCPlugin(object):
    ''' A plugin that creates a global BoxManager (registers/polls boxes,
        maintains DB and RPC connections) and injects a list of BoxRPC objects into
        any Bottle routes that need it (indicated via a "boxes_rpc" keyword
        (customizable)).
    '''

    name = 'boxes'
    api = 2

    def __init__(self, db_engine, kw="boxes_rpc"):
        self._boxmanager = BoxManager(db_engine)
        self._keyword = kw

    def setup(self, app):
        pass

    def close(self):
        pass

    def apply(self, callback, route):
        # Test if the original callback accepts our keyword.
        # Ignore it if it does not need a box list.
        args = inspect.getargspec(route.callback).args
        if self._keyword not in args:
            return callback

        def wrapper(*args, **kwargs):
            # inject the box list as a keyword argument
            kwargs[self._keyword] = self._boxmanager.get_boxes()

            return callback(*args, **kwargs)

        # Replace the route callback with the wrapped one
        return wrapper
