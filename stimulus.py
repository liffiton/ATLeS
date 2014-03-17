
class DummyStimulus(object):
    def __init__(self):
        self._stimcount = 0

    def show(self, stimulus):
        print "%5d: %s" % (self._stimcount, str(stimulus))
        self._stimcount += 1
