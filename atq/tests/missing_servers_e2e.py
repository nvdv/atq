"""End to end tests when some task queue servers are unresponsive."""
import asyncio
import operator
import os
import signal
import subprocess
import unittest

from atq import atqclient
from atq import Q

HOST1, PORT1 = 'localhost', 12345
HOST2, PORT2 = 'localhost', 12346
HOST3, PORT3 = 'localhost', 12347
NUM_WORKERS = 2
TESTS_PATH = 'atq/tests'
NUM_RUNS = 5  # Number of runs in tests.


SERVERS = [
    (HOST1, PORT1),
    (HOST2, PORT2),
    (HOST3, PORT3),
]


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
        test_env = os.environ.copy()
        test_env["PYTHONPATH"] = TESTS_PATH
        cls.p1 = subprocess.Popen(
            ['python3', '-m', 'atq', '-H', HOST1, '-p', str(PORT1),
             '-w', str(NUM_WORKERS)], env=test_env, stderr=subprocess.DEVNULL)
        cls.p3 = subprocess.Popen(
            ['python3', '-m', 'atq', '-H', HOST3, '-p', str(PORT3),
             '-w', str(NUM_WORKERS)], env=test_env, stderr=subprocess.DEVNULL)

    @classmethod
    def tearDownClass(cls):
        os.kill(cls.p1.pid, signal.SIGINT)
        os.kill(cls.p3.pid, signal.SIGINT)
        cls.p1.communicate()
        cls.p3.communicate()

    def setUp(self):
        self.q = Q(SERVERS)

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
        test_env = os.environ.copy()
        test_env["PYTHONPATH"] = TESTS_PATH
        cls.p3 = subprocess.Popen(
            ['python3', '-m', 'atq', '-H', HOST3, '-p', str(PORT3),
             '-w', str(NUM_WORKERS)], env=test_env, stderr=subprocess.DEVNULL)

    @classmethod
    def tearDownClass(cls):
        os.kill(cls.p3.pid, signal.SIGINT)
        cls.p3.communicate()

    def setUp(self):
        self.q = Q(SERVERS)

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

    @classmethod
    def tearDownClass(cls):
        atqclient.MAX_RETRY_COUNT = cls.retry_count

    def setUp(self):
        self.q = Q(SERVERS)

    def testExceptions(self):
        """Tests exceptions when all servers are unresponsive."""
        with self.assertRaises(atqclient.MaxRetriesReachedError):
            for _ in range(NUM_RUNS):
                asyncio.run(exception_test(self.q))
