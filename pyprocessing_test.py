import multiprocessing
import random
import time


def dostuff():
    def draw():
        pyp.rect(100,100,20,random.random(100))
        pyp.ellipse(100,70,60,60)
        pyp.ellipse(81,70,16,32)
        pyp.ellipse(119,70,16,32)
        pyp.line(90,150,80,160)
        pyp.line(110,150,120,160)
    __main__ = dostuff  # HACK
    import pyprocessing as pyp
    pyp.size(200,200)
    pyp.rectMode(pyp.CENTER)
    dostuff.draw()
    pyp.run()


def main():
    p = multiprocessing.Process(target=dostuff)
    p.start()
    print "Still here!"
    time.sleep(10)
    print "Still still here!"


if __name__ == '__main__':
    main()
