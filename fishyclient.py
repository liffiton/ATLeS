# fishyclient.py -- a test(?) client that connects to fishymiddle.py

import rpyc
import random

if __name__ == '__main__':
    c = rpyc.connect("localhost", 12344)
    print c.root
    c.root.register("MYNAMEIS%d" % random.randint(0, 100))
