class MockClass(object):
    '''A class that allows you to call any method in it or its attributes
    (recursively), resulting in printing the exact call to stdout.
    '''
    def __init__(self, name):
        self._name = name

    def __repr__(self):
        return "MockClass({0})".format(self._name)

    def __call__(self, *args, **kwargs):
        argstr = ', '.join([x.__repr__() for x in args] + ["%s=%s" % (key,value.__repr__()) for key, value in kwargs.items()])
        print("MOCK: called %s(%s)" % (self._name, argstr))
        return MockClass(self._name + "()")

    def __getattribute__(self, attr):
        if attr == '_name' or attr == '__repr__':
            return object.__getattribute__(self, attr)
        else:
            return MockClass('.'.join([self._name, attr]))
