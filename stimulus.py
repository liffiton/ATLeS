import multiprocessing

import pygame

# TODO: use abc to make an abstract base class for stimulus w/ show() and end() requiring overrides...


class DummyStimulus(object):
    def __init__(self):
        self._stimcount = 0

    def show(self, stimulus):
        print "%5d: %s" % (self._stimcount, str(stimulus))
        self._stimcount += 1

    def blank(self):
        print "Blanked."

    def unblank(self):
        print "Unblanked."

    def end(self):
        print "Ended."


class VisualStimulusHelperPygame(object):
    def __init__(self, pipe):
        self._pipe = pipe
        self._pos = None
        self._blank = False
        self._bgcolor = (0,0,0)  # black
        pygame.init()
        self._screen = pygame.display.set_mode((640, 480))

    def _draw(self):
        self._screen.fill(self._bgcolor)
        if self._pos is not None and not self._blank:
            x = self._pos[0]  # + random.randint(-20,20)
            y = self._pos[1]  # + random.randint(-20,20)
            pygame.draw.circle(self._screen, (255,0,0), (x,y), 100)
        pygame.display.update()

    def vis_thread(self):
        while True:
            if not self._pipe.poll(0):
                self._draw()
                continue

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


class VisualStimulus(object):
    def __init__(self):
        self._child_pipe, self._pipe = multiprocessing.Pipe(duplex=True)
        self._helper = VisualStimulusHelperPygame(self._child_pipe)
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
