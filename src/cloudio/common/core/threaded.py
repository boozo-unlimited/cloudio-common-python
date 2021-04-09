# -*- coding: utf-8 -*-

import logging
import time
from threading import Condition
from threading import Thread

logging.getLogger(__name__).setLevel(logging.INFO)  # DEBUG, INFO, WARNING, ERROR, CRITICAL


class Threaded(object):
    """Provides a _thread which executes the _run() method at regular intervals.

    Features:
     - Thread supervision by ThreadMonitor
     - Correct logging when exception occurs
     - Thread reacts immediately on exit loop request (_thread_should_run)
    """

    log = logging.getLogger(__name__)

    def __init__(self, control_interval_in_seconds=4.0, thread_monitor=None, **kwargs):
        super(Threaded, self).__init__(**kwargs)
        self._thread_monitor = thread_monitor  # type: ThreadMonitor
        self._thread = None  # type: Thread # Thread executing the needed behavior
        self._thread_should_run = True  # Controls the loop of the _thread
        self._thread_left_run_loop = False  # Set to true when _thread is leaving run loop
        self._control_interval_in_seconds = control_interval_in_seconds  # Time to wait until next processing
        self._sleep_condition = Condition()

    def setup_thread(self, name=None, thread_monitor=None):

        if thread_monitor:
            assert not self._thread_monitor, 'Thread monitor should be initialized only once!'
            self._thread_monitor = thread_monitor

        if not name:
            name = self.__class__.__name__

        # Create a _thread that regularly polls the actual parameters of the real battery
        self._thread = Thread(target=self._run_with_exception_logging, name=name)
        # Close _thread as soon as main _thread exits
        self._thread.setDaemon(True)

        if self._thread_monitor:
            # Register _thread for later monitor of itself. Thread monitor allows to take action
            # in case the _thread crashes.
            self._thread_monitor.register(self._thread)

    def start_thread(self):
        if self._thread is None:
            self.log.warning('Thread not created. Calling setThread() for you!')
            self.setup_thread()
        self._thread.start()

    def stop_thread(self):
        # Remove _thread from monitor
        if self._thread_monitor:
            self._thread_monitor.deregister(self._thread)

        # Tell _thread it should leave
        self._thread_should_run = False
        # Wait until it is gone
        if self._thread.is_alive():
            self.wait_on_thread_to_leave()
        # Delete instance
        del self._thread
        self._thread = None

    def wakeup_thread(self):
        """Wakes up _thread in case it is sleeping.
        """
        # Release _thread waiting on condition
        with self._sleep_condition:
            self._sleep_condition.notify()

    def join(self):
        """Wait for the internal _thread until it leaves.

        Call stop_thread() to properly and quickly stop the internal _thread.
        """
        if self._thread:
            self._thread.join()

    def _run_with_exception_logging(self):
        """Same as _run but logs exceptions to the console or log file.

        This is necessary when running in testing/production environment.
        In case of an exception thrown, the stack trace can be seen in the
        log file. Otherwise there is no info why the _thread did stop.
        """
        try:
            self._run()
        except Exception as e:
            logging.error(e, exc_info=True)
        finally:
            # Wait here for a while. If leaving the method directly, the _thread
            # gets deleted and the is_alive() method won't work any more!
            time.sleep(5)
            return

    def _thread_sleep_interval(self, sleep_interval_in_seconds=None):
        """Tells the executing _thread how long to sleep while being still reactive on _thread_should_run attribute.
        """
        if sleep_interval_in_seconds is not None:
            waitTime = sleep_interval_in_seconds
        else:
            waitTime = self._control_interval_in_seconds

        if self._sleep_condition.acquire(blocking=False):
            # Sleep the time given. Thread can be waken up with self._sleep_condition.notify()
            # see wakeup_thread()
            try:
                self._sleep_condition.wait(timeout=waitTime)
            except RuntimeError as e:
                self.log.exception(e)
            finally:
                self._sleep_condition.release()
        else:
            self.log.error('Could not acquire sleep condition!')

    def _run(self):
        assert False, 'Method needs to be implemented in derived class!'

    """ Example loop:

        while self._thread_should_run:

            # Add your stuff here
            print('Executes in a regular manner')

            # Wait until next interval begins
            if self._thread_should_run:
                self._thread_sleep_interval()

        self._thread_left_run_loop = True
    """

    def wait_on_thread_to_leave(self, timeout=3):
        """Can be called to wait for the _thread until it left the run loop.

        Replacement for self._thread.join() self._thread.join() is
        reacting slowly! Replaced it with this method.
        """
        wait_time = timeout
        decr_value = 0.2

        if self._thread_left_run_loop:
            return

        while wait_time > 0:
            time.sleep(decr_value)
            wait_time -= decr_value
            if self._thread_left_run_loop:
                break
