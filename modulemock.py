class Mockclass(object):
    '''A class that allows you to call any method in it, resulting in printing the exact call to stdout.'''
    @staticmethod
    def __getattribute__(attr):
        def _mockmethod(*args, **kwargs):
            argstr = ', '.join([x.__repr__() for x in args] + ["%s=%s" % (key,value.__repr__()) for key, value in kwargs.items()])
            print("MOCK: called %s(%s)" % (attr, argstr))

        return _mockmethod
