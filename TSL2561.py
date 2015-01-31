# TSL2561.py - A class for using the TSL2561 chip via the i2c bus
# Author: Mark Liffiton
# Date: January, 2015
### Adapted from:
###   https://github.com/seanbechhofer/raspberrypi/tree/master/python

from Adafruit_I2C import Adafruit_I2C
import time

# Constants
_default_address = 0x39
_control_command = 0x80
_timing_command  = 0x81
_read_ir_vis_command  = 0xAC
_read_ir_only_command = 0xAE


class TSL2561(object):
    i2c = None

    def __init__(self, address=_default_address, debug=False):
        self._debug = debug
        self.i2c = Adafruit_I2C(address, debug=debug)
        self.power_up()
        self._gain = -1  # don't know gain to start (board may be powered and configured)
        self.set_gain(1)

    def power_up(self):
        ''' Send byte 0x03 to Control register (0h). '''
        self.i2c.write8(_control_command, 0x03)

    def power_down(self):
        ''' Send byte 0x00 to Control register (0h). '''
        self.i2c.write8(_control_command, 0x00)

    def set_gain(self, gain=1):
        """ Set the gain.

        Arguments:
        gain -- The new gain value.  Gain is set to 1x if gain=1, 16x otherwise.  (Default=1)
        """
        if (gain != self._gain):
            if (gain == 1):
                self.i2c.write8(_timing_command, 0x02)  # set gain = 1X and timing = 402 ms
            else:
                self.i2c.write8(_timing_command, 0x12)  # set gain = 16X and timing = 402 ms

            self._gain = gain                           # save gain for calculation

            # store when new integration will be done (> 402 ms away)
            # 0.8 found to work experimentally
            # 0.402 and even 0.5 too short, give incorrect first readings sometimes
            self._integration_done = time.time() + 0.8

    def _wait_for_integration(self):
        ''' Wait for integration to complete if gain has been reset / new integration ongoing '''
        timeleft = self._integration_done - time.time()
        if timeleft > 0:
            time.sleep(timeleft)

    def read_full(self):
        ''' Read visible+IR value from the device '''
        self._wait_for_integration()
        return self.i2c.readU16(_read_ir_vis_command)

    def read_IR(self):
        ''' Read IR only value from the device '''
        self._wait_for_integration()
        return self.i2c.readU16(_read_ir_only_command)

    def read_lux(self):
        ''' Read both values and calculate a lux measurement '''
        full = self.read_full()
        IR = self.read_IR()

        if self._gain == 1:
            full *= 16    # scale 1x to 16x
            IR *= 16      # scale 1x to 16x

        ratio = (IR / float(full))  # changed to make it run under python 2

        if ((ratio >= 0) & (ratio <= 0.52)):
            lux = (0.0315 * full) - (0.0593 * full * (ratio**1.4))
        elif (ratio <= 0.65):
            lux = (0.0229 * full) - (0.0291 * IR)
        elif (ratio <= 0.80):
            lux = (0.0157 * full) - (0.018 * IR)
        elif (ratio <= 1.3):
            lux = (0.00338 * full) - (0.0026 * IR)
        elif (ratio > 1.3):
            lux = 0

        return lux

if __name__ == "__main__":
    tsl = TSL2561(debug=True)
    lux = tsl.read_lux()
    print "%0.3f lux" % lux
