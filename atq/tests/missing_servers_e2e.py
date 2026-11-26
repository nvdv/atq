"""End to end tests when some task queue servers are unresponsive."""
import asyncio
import operator
import unittest

from atq import atqclient
from atq import Q
from atq.tests import _helpers

HOST = 'localhost'
NUM_WORKERS = 2
NUM_RUNS = 5  # Number of runs in tests.


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


class OneMissingServerE2ETest(unittest.TestCase):
    """e2e tests for task queue when one server is unresponsive."""

    @classmethod
    def setUpClass(cls):
        ports = _helpers.find_free_ports(3, HOST)
        cls.servers = [(HOST, port) for port in ports]
        cls.procs = _helpers.start_servers(
            HOST, [ports[0], ports[2]], NUM_WORKERS)

    @classmethod
    def tearDownClass(cls):
        for proc in cls.procs:
            _helpers.stop_server(proc)

    def setUp(self):
        self.q = Q(self.servers)

    def testBasic(self):
        """Tests basic functions when one server is unresponsive."""
        for _ in range(NUM_RUNS):
            result = asyncio.run(simple_test(self.q, 1, 2))
            self.assertEqual(result, -1)
            result = asyncio.run(simple_test(self.q, 3, 50))
            self.assertEqual(result, 97)

    def testExceptions(self):
        """Tests exception processing when one server is unresponsive."""
        for _ in range(NUM_RUNS):
            with self.assertRaisesRegex(ValueError, '^Hello, world!$'):
                asyncio.run(exception_test(self.q))


class TwoMissingServersE2ETest(unittest.TestCase):
    """e2e tests for task queue when two servers are unresponsive."""

    @classmethod
    def setUpClass(cls):
        ports = _helpers.find_free_ports(3, HOST)
        cls.servers = [(HOST, port) for port in ports]
        cls.procs = [
            _helpers.start_server(HOST, ports[2], NUM_WORKERS),
        ]

    @classmethod
    def tearDownClass(cls):
        for proc in cls.procs:
            _helpers.stop_server(proc)

    def setUp(self):
        self.q = Q(self.servers)

    def testBasic(self):
        """Tests basic functions when two servers are unresponsive."""
        for _ in range(NUM_RUNS):
            result = asyncio.run(simple_test(self.q, 1, 2))
            self.assertEqual(result, -1)
            result = asyncio.run(simple_test(self.q, 3, 50))
            self.assertEqual(result, 97)

    def testExceptions(self):
        """Tests exception processing when two servers are unresponsive."""
        for _ in range(NUM_RUNS):
            with self.assertRaisesRegex(ValueError, '^Hello, world!$'):
                asyncio.run(exception_test(self.q))


class AllServersMissingE2ETest(unittest.TestCase):
    """e2e tests for task queue when all servers are unresponsive."""

    @classmethod
    def setUpClass(cls):
        cls.retry_count = atqclient.MAX_RETRY_COUNT
        atqclient.MAX_RETRY_COUNT = 2
        ports = _helpers.find_free_ports(3, HOST)
        cls.servers = [(HOST, port) for port in ports]

    @classmethod
    def tearDownClass(cls):
        atqclient.MAX_RETRY_COUNT = cls.retry_count

    def setUp(self):
        self.q = Q(self.servers)

    def testExceptions(self):
        """Tests exceptions when all servers are unresponsive."""
        with self.assertRaises(atqclient.MaxRetriesReachedError):
            for _ in range(NUM_RUNS):
                asyncio.run(exception_test(self.q))
