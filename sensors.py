import atexit
import multiprocessing

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

    def _sensors_thread(self):
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

            self._child_pipe.send({'time': datetime.datetime.now(), 'temp': temp, 'lux': lux})

            # check for end signal
            while self._child_pipe.poll():
                val = self._child_pipe.recv()
                if val == 'end':
                    return

            time.sleep(self._read_interval)

    def begin(self):
        self._p = multiprocessing.Process(target=self._sensors_thread)
        self._p.start()
        atexit.register(self.end)
        # Get an initial reading (so get_latest() is guaranteed to return something)
        self._readings = self._pipe.recv()

    def end(self):
        self._pipe.send('end')
        self._p.join()

    def get_latest(self):
        while self._pipe.poll():
            self._readings = self._pipe.recv()
        return self._readings
