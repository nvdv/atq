"""atq worker module."""
import asyncio
import cloudpickle
import concurrent.futures
import logging
import pickle

logging.basicConfig(
    format='%(asctime)s.%(msecs)03d %(levelname)s - %(message)s',
    datefmt='%m/%d/%Y %H:%M:%S', level=logging.INFO)


def task_wrapper(serialized_task):
    """Unpickles task, runs it and pickles result."""
    task = pickle.loads(serialized_task)
    logging.info('Running %s', str(task))
    return cloudpickle.dumps(task())


class QServer:
    """Task queue server.

    Attributes:
        host: Hostname of the server.
        port: Port number of the server.
        loop: Event loop to run in.
        executor: Executor that will run tasks from clients.
        num_executed_tasks: An integer that keeps track of completed tasks.
    """
    def __init__(self, host, port, event_loop, executor):
        self.host, self.port = host, port
        self.loop = event_loop
        self.executor = executor
        self.num_executed_tasks = 0

    async def handle_task(self, reader, writer):
        """Handles task execution."""
        serialized_task = await reader.read()
        try:
            result = await self.loop.run_in_executor(
                self.executor, task_wrapper, serialized_task)
        except Exception as exc:  # pylint: disable=broad-except
            logging.error('%s: %s', type(exc).__name__, str(exc))
            result = cloudpickle.dumps(exc)
        writer.write(result)
        await writer.drain()
        if writer.can_write_eof():
            writer.write_eof()
        self.num_executed_tasks += 1

    def run_forever(self):
        """Starts server."""
        logging.info('Starting worker on %s:%s', self.host, self.port)
        self.loop.run_until_complete(
            asyncio.start_server(
                self.handle_task, host=self.host, port=self.port))
        self.loop.run_forever()

    def shutdown(self):
        """Shuts server down."""
        self.executor.shutdown(wait=True)
        self.loop.stop()
        self.loop.close()

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
        event_loop = asyncio.get_event_loop()
        executor = concurrent.futures.ProcessPoolExecutor(
            max_workers=num_workers)
        return cls(host, port, event_loop, executor)
