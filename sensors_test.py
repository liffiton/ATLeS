from TSL2561 import TSL2561
import time

def main():
    light = TSL2561(debug=0)
    #light.set_gain(16)
    while True:
        full = light.read_full()
        ir = light.read_IR()
        lux = light.read_lux()
        print("%d,%d = %d lux" % (full, ir, lux))
        time.sleep(1)



if __name__ == '__main__':
    main()
