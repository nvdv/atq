"""Basic end to end tests for task queue with multiple servers."""
import asyncio
import operator
import unittest

from atq import Q
from atq.tests import _helpers

HOST = 'localhost'
NUM_WORKERS = 2
NUM_RUNS = 20  # Number of runs in tests.


async def simple_test(q, x, y):
    """Executes some basic functions in the task queue."""
    s1 = q.q(operator.add, x, y)
    s2 = q.q(operator.mul, x, y)
    return await q.q(operator.sub, await s2, await s1)


def raise_exception():
    """Raises a ValueError exception."""
    raise ValueError('Hello, world!')


async def exception_test(q):
    """Raises exception in the task queue."""
    return await q.q(raise_exception)


class MultipleServersE2ETest(unittest.TestCase):
    """e2e tests for task queue with multiple servers."""

    @classmethod
    def setUpClass(cls):
        ports = _helpers.find_free_ports(3, HOST)
        cls.servers = [(HOST, port) for port in ports]
        cls.procs = _helpers.start_servers(HOST, ports, NUM_WORKERS)

    @classmethod
    def tearDownClass(cls):
        for proc in cls.procs:
            _helpers.stop_server(proc)

    def setUp(self):
        self.q = Q(self.servers)

    def testBasic(self):
        """Tests basic functions with multiple servers."""
        for _ in range(NUM_RUNS):
            result = asyncio.run(simple_test(self.q, 1, 2))
            self.assertEqual(result, -1)
            result = asyncio.run(simple_test(self.q, 3, 50))
            self.assertEqual(result, 97)

    def testExceptions(self):
        """Tests exception processing with multiple servers."""
        for _ in range(NUM_RUNS):
            with self.assertRaisesRegex(ValueError, '^Hello, world!$'):
                asyncio.run(exception_test(self.q))
