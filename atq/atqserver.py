"""atq server module."""
import asyncio
import cloudpickle
import concurrent.futures
import logging
import pickle
import signal

LOG_FORMAT = '%(asctime)s.%(msecs)03d %(levelname)s - %(message)s'
LOG_DATEFMT = '%m/%d/%Y %H:%M:%S'

logger = logging.getLogger(__name__)


def configure_logging(level=logging.INFO):
    """Configures root logging for the server and worker processes."""
    logging.basicConfig(format=LOG_FORMAT, datefmt=LOG_DATEFMT, level=level)


def task_wrapper(serialized_task):
    """Unpickles task, runs it and pickles result."""
    task = pickle.loads(serialized_task)
    logger.info('Running %s', str(task))
    return cloudpickle.dumps(task())


def _init_worker():
    """Initializes a worker process (ignores SIGINT and sets up logging)."""
    signal.signal(signal.SIGINT, signal.SIG_IGN)
    configure_logging()


class QServer:
    """Task queue server.

    Attributes:
        host: Hostname of the server.
        port: Port number of the server.
        executor: Executor that will run tasks from clients.
    """
    def __init__(self, host, port, task_executor):
        self.host, self.port = host, port
        self.executor = task_executor

    async def handle_task(self, reader, writer):
        """Handles task execution."""
        serialized_task = await reader.read()
        loop = asyncio.get_running_loop()
        try:
            result = await loop.run_in_executor(
                self.executor, task_wrapper, serialized_task)
        except Exception as exc:  # pylint: disable=broad-except
            logger.error('%s: %s', type(exc).__name__, str(exc))
            result = cloudpickle.dumps(exc)
        writer.write(result)
        await writer.drain()
        if writer.can_write_eof():
            writer.write_eof()
        writer.close()

    async def _serve(self):
        """Runs the asyncio TCP server until cancelled."""
        loop = asyncio.get_running_loop()
        server = await asyncio.start_server(
            self.handle_task, host=self.host, port=self.port)
        current_task = asyncio.current_task()
        try:
            loop.add_signal_handler(signal.SIGTERM, current_task.cancel)
        except NotImplementedError:
            pass
        async with server:
            try:
                await server.serve_forever()
            except asyncio.CancelledError:
                pass

    def run_forever(self):
        """Starts server."""
        logger.info('Starting server on %s:%s', self.host, self.port)
        asyncio.run(self._serve())

    def shutdown(self):
        """Shuts server down."""
        self.executor.shutdown(wait=True)

    @classmethod
    def create(cls, host, port, num_workers):
        """Factory method that creates an instance of the server.

        Args:
            host: Hostname of the server.
            port: Port number of the server.
            num_workers: Number of worker processes.
        Returns:
            An instance of the server.
        """
        pool_executor = concurrent.futures.ProcessPoolExecutor(
            max_workers=num_workers, initializer=_init_worker)
        return cls(host, port, pool_executor)
