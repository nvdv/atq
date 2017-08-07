"""Customized ProcessPoolExecutor."""
import concurrent.futures
import concurrent.futures.process
import multiprocessing


def _process_worker(initializer, call_queue, result_queue):
    """Runs initializer before _process_worker to set signal handlers."""
    initializer()
    concurrent.futures.process._process_worker(call_queue, result_queue)  # pylint: disable=protected-access


class ProcessPoolExecutorWithInit(concurrent.futures.ProcessPoolExecutor):
    """Process pool executor with initializer.

    Allows executing _initializer on each worker before processing tasks.
    """

    def __init__(self, *args, initializer=None, **kwargs):
        super().__init__(*args, **kwargs)
        self._initializer = initializer

    def _adjust_process_count(self):
        for _ in range(len(self._processes), self._max_workers):
            p = multiprocessing.Process(
                target=_process_worker,
                args=(self._initializer,
                      self._call_queue,
                      self._result_queue))
            p.start()
            self._processes[p.pid] = p
