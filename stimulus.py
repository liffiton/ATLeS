import multiprocessing
import random
import time

from pyprocessing import *

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

    def _loop(self):
        '''Called repeatedly by pyprocessing.'''
        if not self._pipe.poll(0):
            self._draw()
            return

        val = self._pipe.recv()
        #print("Got: %s" % str(val))
        if type(val) in (int, float):
            self._pos = (val, val)
        elif type(val) == str:
            if val == 'blank':
                self._blank = True
            elif val == 'unblank':
                self._blank = False
            elif val == 'end':
                exit()

        self._draw()

    def _draw(self):
        background(0)
        if self._pos is not None and not self._blank:
            x = self._pos[0]  # + random.randint(-20,20)
            y = self._pos[1]  # + random.randint(-20,20)
            ellipse(x, y, 100, 100)

    def vis_thread(self):
        size(500,500)
        smooth()
        background(0)
        fill(123,231,0)
        import __main__             # HACK
        __main__.draw = self._loop  # HACK  (monkeypatching)
        run()


class VisualStimulus(object):
    def __init__(self):
        self._child_pipe, self._pipe = multiprocessing.Pipe(duplex=False)
        self._helper = VisualStimulusHelper(self._child_pipe)
        self._p = multiprocessing.Process(target=self._helper.vis_thread)
        self._p.start()

    def show(self, stimulus):
        self._pipe.send(stimulus)

    def blank(self, delay):
        self._pipe.send('blank')
        time.sleep(delay)

    def unblank(self):
        self._pipe.send('unblank')

    def end(self):
        self._pipe.send('end')
        self._p.join()
