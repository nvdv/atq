"""atq client module."""
import asyncio
import cloudpickle
import pickle
import random
import warnings


class Error(Exception):
    """Base class for exceptions in this module."""
    pass


class WorkerConnectionError(Exception):
    """Raised on socket read error."""
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
        _workers: Ccollection of available workers specified by
                  hostnames and ports.
        _scheduler: Generator that returns host and port of selected worker.
    """
    def __init__(self, workers):
        self._workers = workers
        self._scheduler = random_scheduler(self._workers)

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
        """
        while True:
            host, port = next(self._scheduler)
            try:
                reader, writer = await asyncio.open_connection(host, port)
            except OSError:
                warnings.warn(
                    "Can't connect to %s:%s. Retrying..." % (host, port))
            else:
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
        if isinstance(task_result, BaseException):
            raise task_result
        return task_result

    async def q(self, func, *args, **kwargs):
        """Convenient wrapper for _run method."""
        return await self._run(func, args=args, kwargs=kwargs)
