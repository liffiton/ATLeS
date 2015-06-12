import abc
import atexit
import multiprocessing
import os
import signal
import time

try:
    import wiringpi2
except ImportError:
    from modulemock import Mockclass
    wiringpi2 = Mockclass()

try:
    import pygame
except ImportError:
    from modulemock import Mockclass
    pygame = Mockclass()


_LIGHT_PWM_PIN = 18  # pin for PWM control of visible light bar


class StimulusBase(object):
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def begin(self, conf):
        pass

    @abc.abstractmethod
    def end(self):
        pass

    @abc.abstractmethod
    def show(self, stimulus):
        pass

    def msg_poll(self):
        '''By default, Stimulus objects produce no messages unless this is overridden.'''
        return None


class ThreadedStimulus(StimulusBase):
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod  # must be overridden, but should be called via super()
    def __init__(self, helperclass, *args, **kwargs):
        self._child_pipe, self._pipe = multiprocessing.Pipe(duplex=True)
        self._helper = helperclass(self._child_pipe, *args, **kwargs)
        self._p = None  # the separate process running the stimulus thread

    def begin(self, conf):
        self._helper.begin(conf)
        self._p = multiprocessing.Process(target=self._helper.stimulus_thread)
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


class DummyStimulus(StimulusBase):
    def __init__(self):
        self._stimcount = 0

    def begin(self, conf):
        print "Dummy: begin()"

    def end(self):
        print "Dummy: end()"

    def show(self, stimulus):
        if stimulus is not None:
            print "Dummy: stimulus %5d: %s" % (self._stimcount, str(stimulus))
            self._stimcount += 1


class VisualStimulus(ThreadedStimulus):
    def __init__(self):
        '''Initialize as a ThreadedStimulus with StimulusFlashing helper, passed kwarg for fps'''
        super(VisualStimulus, self).__init__(StimulusFlashing, fps=6)


class LightBarStimulus(ThreadedStimulus):
    def __init__(self, freq_Hz):
        '''Initialize as a ThreadedStimulus with StimulusLightBar helper, passed kwarg for freq_Hz'''
        super(LightBarStimulus, self).__init__(StimulusLightBar, freq_Hz)


class PygameHelper(object):
    __metaclass__ = abc.ABCMeta

    def __init__(self, pipe, fps):
        self._pipe = pipe
        self._fps = fps
        self._screen = None

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

    def stimulus_thread(self):
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

    @abc.abstractmethod
    def _draw(self):
        pass

    @abc.abstractmethod
    def _handle_command(self, cmd):
        pass


class StimulusFlashing(PygameHelper):
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


class StimulusLightBar(object):
    '''Stimulus in the form of flashing the visible light LED bar at a given frequency.'''
    def __init__(self, pipe, freq_Hz):
        self._pipe = pipe
        self._active = False  # is flashing activated?
        self._on = False      # is light bar on?
        self._interval = 1.0 / freq_Hz / 2  # half of the period
        wiringpi2.wiringPiSetupGpio()
        wiringpi2.pinMode(18,2)  # enable PWM mode on pin 18

    def _handle_command(self, cmd):
        if cmd is None:
            self._active = False
            # immediately deactivate
            self._update(False)
        else:
            self._active = True
            # immediately activate
            self._update(True)

    def _update(self, newstate=None):
        if newstate is not None:
            # change state of light if newstate is different
            if newstate != self._on:
                self._on = newstate
                print self._on
                wiringpi2.pwmWrite(_LIGHT_PWM_PIN, 1024 if self._on else 0)
        elif self._active:
            # toggle
            self._on = not self._on
            print self._on
            wiringpi2.pwmWrite(_LIGHT_PWM_PIN, 1024 if self._on else 0)

    def begin(self, conf):
        pass

    def stimulus_thread(self):
        while True:
            # check pipe for commands and implement delay between flashes
            msg_ready = self._pipe.poll(self._interval)
            while msg_ready:
                val = self._pipe.recv()

                #print("Got: %s" % str(val))
                if val == 'end':
                    return

                self._handle_command(val)

                msg_ready = self._pipe.poll()  # no timeout, return immediately inside loop

            self._update()
