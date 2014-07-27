import time


class Controller(object):
    def __init__(self):
        self._hits = []

    def set_response(self, response):
        self._response = response

    def add_hit(self, hit):
        new_hit = {
            'time': time.time(),
            'hit': hit,
        }
        self._hits.append(new_hit)


class FixedRatioController(Controller):
    def __init__(self, response_step):
        '''response_step (int): #hits between responses (1 = every hit)'''
        super(FixedRatioController, self).__init__()
        self._step = response_step

    def get_response(self):
        if len(self._hits) % self._step == 0:
            return self._response
        else:
            return None


class FixedIntervalController(Controller):
    def __init__(self, response_interval):
        '''response_interval (int): min seconds between responses'''
        super(FixedIntervalController, self).__init__()
        self._interval = response_interval
        self._prevtime = None

    def get_response(self):
        curtime = self._hits[-1]['time']

        if self._prevtime is None or (curtime - self._prevtime) >= self._interval:
            self._prevtime = curtime
            return self._response
        else:
            return None
