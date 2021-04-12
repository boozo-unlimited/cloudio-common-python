#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time
import unittest

from tests.cloudio.common.paths import update_working_directory
from cloudio.common.core import threaded

update_working_directory()  # Needed when: 'pipenv run python -m unittest tests/cloudio/common/{this_file}.py'


class TestDefaultThreadMonitor(object):
    def __init__(self):
        super(TestDefaultThreadMonitor, self).__init__()

    def register(self, thread):
        pass

    def deregister(self, thread):
        pass


class TestCloudioCommonCoreThreaded(unittest.TestCase):
    """Tests threaded module.
    """

    def test_theaded_creation(self):
        thread = threaded.Threaded()

        thread.setup_thread('simple thread')

        # Needs to throw an assert
        with self.assertRaises(AssertionError):
            thread._run()

    def test_theaded_inheritance(self):
        class Worker(threaded.Threaded):
            def __init__(self):
                super(Worker, self).__init__()

                self.setup_thread('worker')

            def _run(self):
                pass

        worker = Worker()
        worker.start_thread()
        time.sleep(0.1)
        worker.stop_thread()

    def test_threaded_thread_monitor(self):

        class Worker(threaded.Threaded):
            def __init__(self, thread_mon):
                super(Worker, self).__init__()

                self.setup_thread(thread_monitor=thread_mon)

            def _run(self):
                pass

        thread_monitor = TestDefaultThreadMonitor()

        worker = Worker(thread_mon=thread_monitor)
        worker.start_thread()
        time.sleep(0.1)
        worker.stop_thread()

    def test_threaded_start_no_setup(self):

        class Worker(threaded.Threaded):
            def __init__(self):
                super(Worker, self).__init__()

            def _run(self):
                time.sleep(0.5)
                self._thread_left_run_loop = True

        worker = Worker()
        worker.start_thread()
        time.sleep(0.1)
        worker.wakeup_thread()
        worker.wait_on_thread_to_leave()
        worker.stop_thread()

    def test_threaded_join(self):

        class Worker(threaded.Threaded):
            def __init__(self):
                super(Worker, self).__init__()

            def _run(self):
                time.sleep(0.5)
                self._thread_left_run_loop = True

        worker = Worker()
        worker.start_thread()
        worker.join()
        worker.stop_thread()

    def test_threaded_thread_raises_exception(self):

        class Worker(threaded.Threaded):
            def __init__(self):
                super(Worker, self).__init__()

            def _run(self):
                time.sleep(0.3)
                raise Exception()

        worker = Worker()
        worker.start_thread()
        worker.join()
        worker.stop_thread()

    def test_threaded_thread_sleep_interval(self):

        class Worker(threaded.Threaded):
            def __init__(self):
                super(Worker, self).__init__()

            def _run(self):
                while self._thread_should_run:

                    # Add your stuff here
                    print('+')

                    # Wait until next interval begins
                    if self._thread_should_run:
                        self._thread_sleep_interval()

                self._thread_left_run_loop = True

        worker = Worker()
        worker.start_thread()
        time.sleep(0.5)
        worker.stop_thread()

    def test_threaded_thread_restart(self):
        """Checks if threaded class can be started, stop and restarted again.
        """

        class Worker(threaded.Threaded):
            def __init__(self, control_interval_in_seconds):
                super(Worker, self).__init__(control_interval_in_seconds=control_interval_in_seconds)

                self.loop_counter = 0

            def _run(self):
                while self._thread_should_run:

                    self.loop_counter += 1

                    # Wait until next interval begins
                    if self._thread_should_run:
                        self._thread_sleep_interval()

                self._thread_left_run_loop = True

        worker = Worker(control_interval_in_seconds=0.1)
        worker.start_thread()
        time.sleep(0.5)
        worker.stop_thread()

        self.assertTrue(worker.loop_counter > 0)
        last_loop_counter = worker.loop_counter

        worker.start_thread()
        time.sleep(0.5)
        worker.stop_thread()

        self.assertTrue(worker.loop_counter > last_loop_counter)


if __name__ == '__main__':
    unittest.main()
