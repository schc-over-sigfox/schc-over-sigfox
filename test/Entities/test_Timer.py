import time
import unittest
from unittest import TestCase

from Entities.Timer import Timer
from Entities.exceptions import SCHCTimeoutError


@unittest.skip
class TestTimer(TestCase):

    def test_sleep(self):
        timer = Timer()
        timeout = 1

        with self.assertRaises(SCHCTimeoutError):
            timer.sleep(timeout, raise_exception=True)

        t_i = time.perf_counter()
        timer.sleep(timeout, raise_exception=False)
        t_f = time.perf_counter()

        self.assertTrue(t_f - t_i >= timeout)

    def test_start(self):
        timer = Timer()
        timeout = 1

        timer.start(timeout, raise_exception=False)
        self.assertTrue(timer.THREAD.is_alive())
        self.assertFalse(timer.STOPPED)
        time.sleep(timeout + 1)
        self.assertFalse(timer.THREAD.is_alive())
        self.assertFalse(timer.STOPPED)

    def test_stop(self):
        timer = Timer()
        timeout = 1

        timer.start(timeout, raise_exception=False)
        self.assertTrue(timer.THREAD.is_alive())
        self.assertFalse(timer.STOPPED)
        timer.stop()
        self.assertFalse(timer.THREAD.is_alive())
        self.assertTrue(timer.STOPPED)

    def test_time(self):
        timer = Timer()
        current_time = timer.time()
        self.assertIsInstance(current_time, int)
        resolution = 60
        self.assertEqual(current_time // resolution, timer.time(resolution))
