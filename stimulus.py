import multiprocessing

from pyprocessing import *   # flake8: noqa

# TODO: use abc to make an abstract base class for stimulus w/ show, end as requiring overrides...


class DummyStimulus(object):
    def __init__(self):
        self._stimcount = 0

    def show(self, stimulus):
        print "%5d: %s" % (self._stimcount, str(stimulus))
        self._stimcount += 1


class VisualStimulusHelper(object):
    def __init__(self, pipe):
        self._pipe = pipe
        self._pos = None
        self._blank = False
        self._bgcolor = 0  # black

    def _loop(self):
        '''Called repeatedly by pyprocessing.'''
        if not self._pipe.poll(0):
            self._draw()
            return

        val = self._pipe.recv()
        #print("Got: %s" % str(val))

        if type(val) in (int, float):
            self._pos = (val, val)
        elif val == 'blank':
            self._blank = True
        elif val == 'unblank':
            self._blank = False
        elif val == 'end':
            exit()

        self._draw()

        if val == 'blank':
            self._pipe.send('blanked')

    def _clear(self):
        background(self._bgcolor)

    def _draw(self):
        self._clear()
        if self._pos is not None and not self._blank:
            x = self._pos[0]  # + random.randint(-20,20)
            y = self._pos[1]  # + random.randint(-20,20)
            ellipse(x, y, 100, 100)

    def vis_thread(self):
        size(500,500)
        smooth()
        fill(0,0,255)
        self._clear()
        import __main__             # HACK
        __main__.draw = self._loop  # HACK  (monkeypatching)
        run()


class VisualStimulus(object):
    def __init__(self):
        self._child_pipe, self._pipe = multiprocessing.Pipe(duplex=True)
        self._helper = VisualStimulusHelper(self._child_pipe)
        self._p = multiprocessing.Process(target=self._helper.vis_thread)
        self._p.start()

    def show(self, stimulus):
        self._pipe.send(stimulus)

    def blank(self):
        self._pipe.send('blank')
        # wait for confirmation...
        response = self._pipe.recv()
        print response
        assert(response == 'blanked')

    def unblank(self):
        self._pipe.send('unblank')

    def end(self):
        self._pipe.send('end')
        self._p.join()
