"""Basic end to end tests for task queue with single server."""
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


class SimpleE2ETest(unittest.TestCase):
    """e2e tests for task queue basic functionality."""

    @classmethod
    def setUpClass(cls):
        cls.port = _helpers.find_free_ports(1, HOST)[0]
        cls.p = _helpers.start_server(HOST, cls.port, NUM_WORKERS)

    @classmethod
    def tearDownClass(cls):
        _helpers.stop_server(cls.p)

    def setUp(self):
        self.q = Q([(HOST, self.port)])

    def testBasic(self):
        """Tests running basic functions."""
        for _ in range(NUM_RUNS):
            result = asyncio.run(simple_test(self.q, 1, 2))
            self.assertEqual(result, -1)
            result = asyncio.run(simple_test(self.q, 3, 50))
            self.assertEqual(result, 97)

    def testExceptions(self):
        """Tests exception processing."""
        for _ in range(NUM_RUNS):
            with self.assertRaisesRegex(ValueError, '^Hello, world!$'):
                asyncio.run(exception_test(self.q))
