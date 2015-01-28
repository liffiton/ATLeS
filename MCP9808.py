# MCP9808.py - A class for using the MCP9808 chip via the i2c bus
# Author: Mark Liffiton
# Date: January, 2015

from Adafruit_I2C import Adafruit_I2C

# Constants
_default_address = 0x18
_config_register = 0x01
_read_temp_register  = 0x05


class MCP9808(object):
    ''' A basic class for accessing the MCP9808 temperature sensor via I2C.

    Currently, does no configuration, so it expects the power-on default values in all registers.
    '''
    i2c = None

    def __init__(self, address=_default_address, debug=False):
        self.i2c = Adafruit_I2C(address, debug=debug)
        self._debug = debug

    def read_temp(self):
        ''' Read temperature from the device '''
        reading = self.i2c.readU16(_read_temp_register, little_endian=False)
        # If needed at some point:
        #over_crit = bool(reading & 0x8000)
        #over_upper = bool(reading & 0x4000)
        #under_lower = bool(reading & 0x2000)
        temp_sign = bool(reading & 0x1000)
        temp_2scomp = reading & 0x0fff

        if self._debug:
            print("Data: %s = %s" % (hex(reading), bin(reading)))

        if temp_sign:
            temp = -0x1000 + temp_2scomp  # value of MSB (sign bit) is actually negative
        else:
            temp = temp_2scomp

        temp /= 16.0  # default resolution is 1/16 degC per bit

        return temp


if __name__ == "__main__":
    mcp = MCP9808(debug=True)
    temp = mcp.read_temp()
    print "%0.2f degC" % temp
