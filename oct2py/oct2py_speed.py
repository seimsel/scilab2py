''' py2oct_speed.py - Checks the speed penalty of the Python to Octave bridge

Uses timeit to test the raw execution of a matlab command,
Then tests progressively larger array passing.
'''
import time
import timeit
import numpy as np
from py2oct import Octave


class OctaveSpeed(object):
    ''' Checks the speed penalty of the Python to Octave bridge

    Uses timeit to test the raw execution of a matlab command,
    Then tests progressively larger array passing.
    '''
    def __init__(self):
        self.octave = Octave()
        self.array = []

    def raw_speed(self):
        """ Run a fast matlab command and see how long it takes """
        self.octave.run("x = 1")

    def large_array_put(self):
        """ Create a large matrix and load it into the octave session """
        self.octave.put('x', self.array)

    def large_array_get(self):
        """ Retrieve the large matrix from the octave session """
        self.octave.get('x')

    def run(self):
        """ Uses timeit to test the raw execution of a matlab command,
        Then tests progressively larger array passing.
        """
        print 'py2oct speed test'
        print '*' * 20
        time.sleep(1)

        print 'Raw speed: ',
        avg = timeit.timeit(self.raw_speed, number=200) / 200
        print '%d usec per loop' % (avg * 1e6)

        nruns = [200, 200, 200, 50, 1]
        for ind, nruns in enumerate(nruns):
            side = 10 ** ind
            self.array = np.reshape(np.arange(side ** 2), (-1))
            print 'Put %sx%s: ' % (side, side),
            avg = timeit.timeit(self.large_array_put, number=nruns) / nruns
            print '%0.1f msec' % (avg * 1e3)

            print 'Get %sx%s: ' % (side, side),
            avg = timeit.timeit(self.large_array_get, number=nruns) / nruns
            print '%0.1f msec' % (avg * 1e3)

        print '*' * 20
        print 'Test complete!'

if __name__ == '__main__':
    speed_test = OctaveSpeed()
    speed_test.run()