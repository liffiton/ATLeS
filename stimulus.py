import atexit
import multiprocessing
import os
import signal
import time

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


class VisualStimulusHelper(object):
    def __init__(self, pipe, fps=10):
        self._pipe = pipe
        self._fps = fps

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

    def vis_thread(self):
        # ignore signals that will be handled by parent
        signal.signal(signal.SIGALRM, signal.SIG_IGN)
        signal.signal(signal.SIGINT, signal.SIG_IGN)

        while True:
            self._draw()
            pygame.display.flip()

            # check pipe for commands
            while self._pipe.poll():
                val = self._pipe.recv()

                #print("Got: %s" % str(val))
                if val == 'end':
                    return

                self._handle_command(val)

            # check pygame events for quit
            for event in pygame.event.get():
                if event.type == pygame.QUIT or event.type == pygame.KEYUP:
                    self._pipe.send('quit')
                    return

            time.sleep(1.0 / self._fps)


class StimulusFlashing(VisualStimulusHelper):
    def __init__(self, pipe, fps=10):
        super(StimulusFlashing, self).__init__(pipe, fps)
        self._on = False
        self._flash = True  # so it starts lit
        self._bgcolor = (0,0,0)  # black
        self._oncolor = (255,255,255)  # white

    def _handle_command(self, cmd):
        if cmd is None:
            self._on = False
            self._flash = True  # so it starts lit next time
        else:
            self._on = True

    def _draw(self):
        if self._on and self._flash:
            self._screen.fill(self._oncolor)
        else:
            self._screen.fill(self._bgcolor)
        if self._on:
            self._flash = not self._flash


class VisualStimulus(object):
    def __init__(self):
        self._child_pipe, self._pipe = multiprocessing.Pipe(duplex=True)
        self._helper = StimulusFlashing(self._child_pipe, fps=6)

    def begin(self, conf):
        self._helper.begin(conf)
        self._p = multiprocessing.Process(target=self._helper.vis_thread)
        self._p.start()
        atexit.register(self.end)

    def end(self):
        self._pipe.send('end')
        self._p.join()

    def show(self, stimulus):
        self._pipe.send(stimulus)

    def msg_poll(self):
        if self._pipe.poll():
            response = self._pipe.recv()
            return response
        return None
