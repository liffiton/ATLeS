from TSL2561 import TSL2561
import time

def main():
    lightsensor = TSL2561()
    lightsensor.setGain(1)
    while True:
        ambient = lightsensor.readFull()
        ir = lightsensor.readIR()
        print("%d,%d" % (ambient, ir))
        time.sleep(1)



if __name__ == '__main__':
    main()
