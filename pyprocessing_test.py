import multiprocessing
import random
import time

from pyprocessing import *


def dostuff():
    '''
    To get pyprocessing to work somewhere other than the real __main__ module,
    we have to create our functions and insert them into the __main__ module by
    importing it and monkeypatching it.
    '''
    def draw():
        rect(100,100,20,random.randint(90,110))
        ellipse(100,70,60,60)
        ellipse(81,70,16,32)
        ellipse(119,70,16,32)
        line(90,150,80,160)
        line(110,150,120,160)
    import __main__       # HACK
    __main__.draw = draw  # HACK  (monkeypatching)
    size(200,200)
    rectMode(CENTER)
    run()


def main():
    p = multiprocessing.Process(target=dostuff)
    p.start()
    print "Still here!"
    time.sleep(5)
    print "Still still here!"


if __name__ == '__main__':
    main()
