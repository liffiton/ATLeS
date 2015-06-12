from TSL2561 import TSL2561
from MCP9808 import MCP9808
import time


def main():
    tsl = TSL2561(debug=0)
    mcp = MCP9808(debug=0)
    #tsl.set_gain(16)
    while True:
        full = tsl.read_full()
        ir = tsl.read_IR()
        lux = tsl.read_lux()
        print("%d,%d = %d lux" % (full, ir, lux))
        temp = mcp.read_temp()
        print("%0.2f degC" % temp)
        time.sleep(1)


if __name__ == '__main__':
    main()
