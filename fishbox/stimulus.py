import abc
import atexit
import multiprocessing
import os
import signal
import sys

try:
    import wiringpi2
    _wiringpi2_mocked = False
except ImportError:
    from modulemock import Mockclass
    wiringpi2 = Mockclass()
    _wiringpi2_mocked = True


_LIGHT_PWM_PIN = 18  # pin for PWM control of visible light bar
_AMBIENT_LIGHT_PWM = 550  # value that produces ~70lux in a quick test (with enclosure fully opaque and board pushed into corner)


class NotRootError(RuntimeError):
    pass


class StimulusBase(object):
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def begin(self):
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
        self._helper = helperclass(*args, **kwargs)
        self._p = None  # the separate process running the stimulus thread

    def begin(self):
        self._helper.begin()
        self._p = multiprocessing.Process(target=self._helper.stimulus_thread, args=(self._child_pipe,))
        self._p.start()
        atexit.register(self.end)

    def end(self):
        self._pipe.send('end')
        # clear queue before joining
        while self._pipe.poll():
            self._pipe.recv()
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

    def begin(self):
        print("Dummy: begin()")

    def end(self):
        print("Dummy: end()")

    def show(self, stimulus):
        if stimulus:
            print("Dummy: stimulus %5d: %s" % (self._stimcount, str(stimulus)))
            self._stimcount += 1


class LightBarStimulus(ThreadedStimulus):
    def __init__(self, freq_Hz, nostim_level=_AMBIENT_LIGHT_PWM):
        '''Initialize as a ThreadedStimulus with StimulusLightBar helper, passed kwarg for freq_Hz and nostim_level.  freq_Hz=0 means the light bar will be on for as long as the stimulus is active.'''
        super(LightBarStimulus, self).__init__(StimulusLightBar, freq_Hz, nostim_level)


class StimulusLightBar(object):
    '''Stimulus in the form of flashing the visible light LED bar at a given frequency.'''
    def __init__(self, freq_Hz, nostim_level):
        self._active = False   # is flashing activated?
        self._on = False       # is light bar on?
        if freq_Hz == 0:
            self._interval = None  # infinite wait in poll()
        else:
            self._interval = 1.0 / freq_Hz / 2  # half of the period

        self._nostim_level = nostim_level  # PWM value for light level when stimulus not active

        self._lightval = None  # stores current PWM value to avoid extraneous pwmWrites

        # must be root to access GPIO, and wiringpi itself crashes in a way that
        # leaves the camera (setup in tracking.py) inaccessible until reboot.
        if (not _wiringpi2_mocked) and (os.geteuid() != 0):
            raise NotRootError("%s must be run with sudo." % sys.argv[0])

        wiringpi2.wiringPiSetupGpio()
        wiringpi2.pinMode(18,2)  # enable PWM mode on pin 18

        self._light_nostim()

        atexit.register(self._light_off)

    def _set_light(self, val):
        if self._lightval != val:
            wiringpi2.pwmWrite(_LIGHT_PWM_PIN, val)
            self._lightval = val

    def _light_off(self):
        self._set_light(0)

    def _light_on(self):
        self._set_light(1023)

    def _light_nostim(self):
        self._set_light(self._nostim_level)

    def _handle_command(self, cmd):
        if cmd:
            self._active = True
        else:
            self._active = False
            self._on = False

    def _update(self):
        if self._active:
            # toggle
            if self._interval is None:
                self._on = True
            else:
                self._on = not self._on
            if self._on:
                self._light_on()
            else:
                self._light_off()
        else:
            self._light_nostim()

    def begin(self):
        pass

    def stimulus_thread(self, pipe):
        # ignore signals that will be handled by parent
        signal.signal(signal.SIGALRM, signal.SIG_IGN)
        signal.signal(signal.SIGINT, signal.SIG_IGN)

        while True:
            # check pipe for commands and implement delay between flashes
            msg_ready = pipe.poll(self._interval)
            while msg_ready:
                val = pipe.recv()

                if val == 'end' or val is None:
                    return

                self._handle_command(val)

                msg_ready = pipe.poll()  # no timeout, return immediately inside loop

            self._update()
