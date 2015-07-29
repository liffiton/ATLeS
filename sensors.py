import atexit
import multiprocessing
import signal

from TSL2561 import TSL2561
from MCP9808 import MCP9808
import datetime
import time


class Sensors(object):
    ''' Class for reading and reporting sensor values '''
    def __init__(self, read_interval=1):
        self._child_pipe, self._pipe = multiprocessing.Pipe(duplex=True)
        self._read_interval = read_interval
        self._readings = None

    def _sensors_thread(self, pipe):
        # ignore signals that will be handled by parent
        signal.signal(signal.SIGALRM, signal.SIG_IGN)
        signal.signal(signal.SIGINT, signal.SIG_IGN)

        tsl = TSL2561(debug=0)
        mcp = MCP9808(debug=0)
        #tsl.set_gain(16)

        while True:
            temp = mcp.read_temp()
            #print("%0.2f degC" % temp)

            #full = tsl.read_full()
            #ir = tsl.read_IR()
            lux = tsl.read_lux()
            #print("%d,%d = %d lux" % (full, ir, lux))

            pipe.send({'time': datetime.datetime.now(), 'temp': temp, 'lux': lux})

            # check for end signal
            while pipe.poll():
                val = pipe.recv()
                if val == 'end' or val is None:
                    return

            time.sleep(self._read_interval)

    def begin(self):
        self._p = multiprocessing.Process(target=self._sensors_thread, args=(self._child_pipe,))
        self._p.start()
        atexit.register(self.end)
        # Get an initial reading (so get_latest() is guaranteed to return something)
        self._readings = self._pipe.recv()

    def end(self):
        self._pipe.send('end')
        # clear queue before joining
        while self._pipe.poll():
            self._pipe.recv()
        self._p.join()

    def get_latest(self):
        while self._pipe.poll():
            self._readings = self._pipe.recv()
        return self._readings
