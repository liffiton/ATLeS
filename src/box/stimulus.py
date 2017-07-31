import abc
import atexit
import multiprocessing
import os
import signal
import sys
from threading import Timer

from box import wiring


_LIGHT_PWM_PIN = 18      # pin for PWM control of visible light bar
_ELECTRIC_STIM_PIN = 25  # pin for control of the electric current stimulation


class NotRootError(RuntimeError):
    pass


# adapted from http://stackoverflow.com/a/16148744
class Watchdog:
    def __init__(self, timeout, pipe):  # timeout in seconds
        self._timeout = timeout
        self._pipe = pipe
        self._timer = None

    def stop(self):
        if self._timer:
            self._timer.cancel()
            self._timer = None

    def start(self):
        self._timer = Timer(self._timeout, self._triggered)
        self._timer.start()

    def poke(self):
        """Start the timer if it is not already started; else let it run."""
        if self._timer is None:
            self.start()

    def _triggered(self):
        self._pipe.send("timeout")
        self.stop()


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
    def __init__(self):
        self._child_pipe, self._pipe = multiprocessing.Pipe(duplex=True)
        self._p = None  # the separate process running the stimulus thread

    @abc.abstractmethod  # must be overridden
    def _stimulus_thread(self, pipe):
        pass

    def begin(self):
        self._p = multiprocessing.Process(target=self._stimulus_thread, args=(self._child_pipe,))
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


class GPIOStimulus(ThreadedStimulus):
    '''Stimulus in the form of activating or toggling a GPIO pin.'''
    def __init__(self, pin, levels=None, freq_Hz=None, safety_limit=None):
        '''
        levels is a tuple of (nostim, stim), where each is a PWM level for the cases
        of no stimulus and active stimulus, respectively.

        freq_Hz=0 means the pin will be set to stim_level for as long as the
        stimulus is active.

        safety_limit is given in seconds.  If the stimulus is active for that many seconds,
        an exception is raised.
        '''
        super(GPIOStimulus, self).__init__()

        # must be root to access GPIO, and wiringpi itself crashes in a way that
        # leaves the camera (setup in tracking.py) inaccessible until reboot.
        if (not wiring.wiring_mocked) and (os.geteuid() != 0):
            raise NotRootError("%s must be run with sudo." % sys.argv[0])

        self._pin = pin                    # GPIO pin to control

        if levels is not None:
            self._pwm = True
            self._nostim_level, self._stim_level = levels  # PWM values for pin when stimulus is/not active
        else:
            self._pwm = False

        if freq_Hz is None or freq_Hz == 0:
            self._interval = None  # infinite wait in poll()
        else:
            self._interval = 1.0 / freq_Hz / 2  # half of the period

        if safety_limit is not None:
            self._watchdog = Watchdog(safety_limit, self._pipe)
        else:
            self._watchdog = None

        self._stim_on = False   # is stimulus activated?
        self._on = False        # is stimulus pin currently on? (may be off while 'activated' if toggling)
        self._pinval = None  # stores current PWM value to avoid extraneous pwmWrites

    def _set_pin(self, val):
        if self._pinval != val:
            if self._pwm:
                wiring.pwm(self._pin, val)
            else:
                wiring.out(self._pin, val)
            self._pinval = val

    def _pin_nostim(self):
        if self._pwm:
            self._set_pin(self._nostim_level)
        else:
            self._set_pin(0)

        if self._watchdog:
            self._watchdog.stop()

    def _pin_stim(self):
        if self._pwm:
            self._set_pin(self._stim_level)
        else:
            self._set_pin(1)

        if self._watchdog:
            self._watchdog.poke()

    def _handle_command(self, cmd):
        if cmd:
            self._stim_on = True
        else:
            self._stim_on = False
            self._on = False

    def _update(self):
        if self._stim_on:
            if self._interval is None:
                self._pin_stim()
            else:
                # toggle fully on/off
                self._on = not self._on
                if self._on:
                    self._pin_stim()
                else:
                    self._pin_nostim()
        else:
            self._pin_nostim()

    def _begin(self):
        self._pin_nostim()

    def _end(self):
        self._set_pin(0)

    def _stimulus_thread(self, pipe):
        # ignore signals that will be handled by parent
        signal.signal(signal.SIGALRM, signal.SIG_IGN)
        signal.signal(signal.SIGINT, signal.SIG_IGN)

        self._begin()

        while True:
            # check pipe for commands and implement delay between flashes
            msg_ready = pipe.poll(self._interval)
            while msg_ready:
                val = pipe.recv()

                if val == 'end' or val is None:
                    self._end()
                    return
                elif val == 'timeout':
                    pipe.send('safety limit reached')
                    self._end()
                    return

                self._handle_command(val)

                msg_ready = pipe.poll()  # no timeout, return immediately inside loop

            self._update()


class LightBarStimulus(GPIOStimulus):
    def __init__(self, nostim_level, stim_level, freq_Hz=None):
        '''freq_Hz=0 means the light bar will be on for as long as the stimulus is active.'''
        super(LightBarStimulus, self).__init__(_LIGHT_PWM_PIN, levels=(nostim_level, stim_level), freq_Hz=freq_Hz)


class ElectricalStimulus(GPIOStimulus):
    def __init__(self, safety_limit):
        '''safety_limit: integer number of seconds; if stimulus active without a break for that long, terminate experiment.'''
        super(ElectricalStimulus, self).__init__(_ELECTRIC_STIM_PIN, safety_limit=safety_limit)
