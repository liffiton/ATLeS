import time


class Controller(object):
    def __init__(self):
        self._hits = []

    def add_hit(self, hit):
        new_hit = {
            'time': time.time(),
            'hit': hit,
        }
        self._hits.append(new_hit)


class FixedRatioController(Controller):
    def __init__(self, response_step):
        super(FixedRatioController, self).__init__()
        self._step = response_step

    def do_response(self):
        return len(self._hits) % self._step == 0


class FixedIntervalController(Controller):
    def __init__(self, response_interval):
        '''response_interval (int): min seconds between responses'''
        super(FixedIntervalController, self).__init__()
        self._interval = response_interval
        self._prevtime = None

    def do_response(self):
        curtime = self._hits[-1]['time']

        if self._prevtime is None or (curtime - self._prevtime) >= self._interval:
            self._prevtime = curtime
            return True

        return False
