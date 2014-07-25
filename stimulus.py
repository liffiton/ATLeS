import multiprocessing
import os

import pygame

# TODO: use abc to make an abstract base class for stimulus w/ show() and end() requiring overrides...


class DummyStimulus(object):
    def __init__(self):
        self._stimcount = 0

    def begin(self):
        print "Begin."

    def end(self):
        print "End."

    def show(self, stimulus):
        print "%5d: %s" % (self._stimcount, str(stimulus))
        self._stimcount += 1

    def blank(self):
        print "Blanked."

    def unblank(self):
        print "Unblanked."


class VisualStimulusHelperPygame(object):
    def __init__(self, pipe):
        self._pipe = pipe
        self._pos = None
        self._blank = False
        self._bgcolor = (0,0,0)  # black

    def begin(self, conf):
        '''Create a window in the specific location with the specified dimensions.'''

        # Figure out x,y coordinates if given as negative values (i.e., from right/bottom)
        pygame.init()
        info = pygame.display.Info()
        if conf['x'] < 0:
            conf['x'] = info.current_w - conf['width'] + conf['x'] + 1
        if conf['y'] < 0:
            conf['y'] = info.current_h - conf['height'] + conf['y'] + 1

        os.environ['SDL_VIDEO_WINDOW_POS'] = "%d,%d" % (conf['x'], conf['y'])
        self._screen = pygame.display.set_mode((conf['width'], conf['height']))
        #self._screen = pygame.display.set_mode((640, 480), pygame.HWSURFACE|pygame.DOUBLEBUF|pygame.FULLSCREEN)
        pygame.mouse.set_visible(False)

    def _draw(self):
        self._screen.fill(self._bgcolor)
        if self._pos is not None and not self._blank:
            x = int(self._pos[0])  # + random.randint(-20,20)
            y = int(self._pos[1])  # + random.randint(-20,20)
            pygame.draw.circle(self._screen, (255,0,0), (x,y), 100)
        pygame.display.flip()

    def vis_thread(self):
        while True:
            val = self._pipe.recv()  # waits for next command
            #print("Got: %s" % str(val))

            if type(val) in (int, float):
                self._pos = (val, val)
            elif val is None:
                self._pos = None
            elif val == 'blank':
                self._blank = True
            elif val == 'unblank':
                self._blank = False
            elif val == 'end':
                return

            self._draw()

            # check pygame events for quit
            for event in pygame.event.get():
                if event.type == pygame.QUIT or event.type == pygame.KEYUP:
                    self._pipe.send('quit')
                    return

            if val == 'blank':
                self._pipe.send('blanked')


class VisualStimulus(object):
    def __init__(self):
        self._child_pipe, self._pipe = multiprocessing.Pipe(duplex=True)
        self._helper = VisualStimulusHelperPygame(self._child_pipe)

    def begin(self, conf):
        self._helper.begin(conf)
        self._p = multiprocessing.Process(target=self._helper.vis_thread)
        self._p.start()

    def end(self):
        self._pipe.send('end')
        self._p.join()

    def show(self, stimulus):
        self._pipe.send(stimulus)

    def blank(self):
        self._pipe.send('blank')
        # wait for confirmation...
        response = self._pipe.recv()
        if response == 'quit':
            exit()
        else:
            assert(response == 'blanked')

    def unblank(self):
        self._pipe.send('unblank')
