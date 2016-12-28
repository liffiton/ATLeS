import atexit

try:
    import wiringpi
    wiring_mocked = False
except ImportError:
    from .modulemock import MockClass
    wiringpi = MockClass("wiringpi")
    wiring_mocked = True


_LIGHT_PWM_PIN = 18   # pin for PWM control of visible light bar
_IR_GPIO_PIN = 23     # pin for control of IR light bar

wiringpi.wiringPiSetupGpio()
_pinmodes = dict()


def _pinmode(pin, mode):
    if pin not in _pinmodes or _pinmodes[pin] != mode:
        wiringpi.pinMode(pin, mode)
        _pinmodes[pin] = mode


def out(pin, val):
    _pinmode(pin, 1)  # enable output mode on pin
    wiringpi.digitalWrite(pin, val)


def pwm(pin, val):
    _pinmode(pin, 2)  # enable PWM mode on pin
    wiringpi.pwmWrite(pin, val)


def IR_on():
    out(_IR_GPIO_PIN, 1)  # turn on IR light bar
    atexit.register(IR_off)


def IR_off():
    out(_IR_GPIO_PIN, 0)  # turn off IR light bar


def visible_on(level):
    pwm(_LIGHT_PWM_PIN, level)  # turn on visible light bar
    atexit.register(visible_off)


def visible_off():
    out(_LIGHT_PWM_PIN, 0)  # turn off visible light bar
