"""atq client module."""
import asyncio
import cloudpickle
import pickle
import random
import warnings

from collections import defaultdict

WAIT_TIME = 0.1  # seconds
MAX_RETRY_COUNT = 100


class Error(Exception):
    """Base class for exceptions in this module."""
    pass


class WorkerConnectionError(Error):
    """Raised on socket read error."""
    pass


class MaxRetriesReachedError(Error):
    """Raised when maximum number of retries is reached."""
    pass


class Task:
    """Wraps function and it's arguments."""
    def __init__(self, host, func, *args, **kwargs):
        self.host = host
        self.func, self.args, self.kwargs = func, args, kwargs

    def __call__(self):
        return self.func(*self.args, **self.kwargs)

    def __str__(self):
        return '<%s> from %s' % (self.func.__name__, self.host)


def random_scheduler(workers):
    """Picks next worker uniformly at random."""
    while True:
        yield random.choice(workers)


class Q:
    """Task queue client.

    Attributes:
        _workers: Collection of available workers specified by
                  hostnames and ports.
        _scheduler: Generator that returns host and port of selected worker.
        _retries_per_server: Defaultdict that stores number of retries for
                             each task queue server.
    """
    def __init__(self, workers):
        self._workers = workers
        self._scheduler = random_scheduler(self._workers)
        self._retries_per_server = defaultdict(int)

    async def _run(self, func, args=(), kwargs={}):  # pylint: disable=dangerous-default-value
        """Runs function in the task queue.

        Runs func in task queue and returns result or raises exception.

        Args:
            func: Function to run in task queue.
            args: Function non-keyword arguments
            kwargs: Function keyword arguments.

        Raises:
            WorkerConnectionError: Raised on error reading data from job
                                   queue worker.
            MaxRetriesReachedError: Raised when maximum number of retries for
                                    specific server is reached.
        """
        while True:
            server_address = next(self._scheduler)
            try:
                reader, writer = await asyncio.open_connection(*server_address)
            except OSError:
                self._retries_per_server[server_address] += 1
                if self._retries_per_server[server_address] > MAX_RETRY_COUNT:
                    raise MaxRetriesReachedError(
                        'Max number of retries is reached for %s:%s' %
                        server_address)
                warnings.warn(
                    "Can't connect to %s:%s. Retrying..." % server_address)
                await asyncio.sleep(WAIT_TIME)
            else:
                self._retries_per_server[server_address] = 0
                break

        curr_host, *_ = writer.get_extra_info('sockname')
        serialized_task = cloudpickle.dumps(
            Task(curr_host, func, *args, **kwargs))
        writer.write(serialized_task)
        if writer.can_write_eof():
            writer.write_eof()
        await writer.drain()

        try:
            serialized_result = await reader.read()
        except ConnectionResetError:
            raise WorkerConnectionError

        task_result = pickle.loads(serialized_result)
        writer.close()
        if isinstance(task_result, BaseException):
            raise task_result
        return task_result

    async def q(self, func, *args, **kwargs):
        """Convenient wrapper for _run method."""
        return await self._run(func, args=args, kwargs=kwargs)
