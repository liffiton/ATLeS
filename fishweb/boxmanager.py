import collections
import copy
import inspect
import threading
import time

BoxSpec = collections.namedtuple('BoxSpec', 'ip, port, name, up')


class _BoxManager(threading.Thread):
    def __init__(self):
        super(_BoxManager, self).__init__()
        self._boxes = {
            # dummy data for now
            'box1': BoxSpec(ip="10.0.0.1", port=4444, name='box1', up=True),
            'box2': BoxSpec(ip="10.0.0.2", port=4444, name='box2', up=False),
            'box3': BoxSpec(ip="10.0.0.3", port=4444, name='box3', up=True),
        }
        self._boxlock = threading.Lock()

    def run(self):
        time.sleep(10000)

    def get_boxes(self):
        with self._boxlock:
            return copy.copy(self._boxes)


class BoxManagerPlugin(object):
    ''' A plugin to inject a box list from a  global BoxManager into any Bottle
    routes that need it (indicated via a "boxes" keyword (customizable)).
    '''

    name = 'boxmanager'
    api = 2

    def __init__(self, kw="boxes"):
        self._boxmanager = _BoxManager()
        self._boxmanager.daemon = True
        self._boxmanager.start()
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
