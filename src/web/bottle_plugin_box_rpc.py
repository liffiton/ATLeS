import inspect

from web.box_rpc import BoxManager


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
        params = inspect.signature(route.callback).parameters
        if self._keyword not in params:
            return callback

        def wrapper(*args, **kwargs):
            # inject the box list as a keyword argument
            kwargs[self._keyword] = self._boxmanager.get_boxes()

            return callback(*args, **kwargs)

        # Replace the route callback with the wrapped one
        return wrapper
