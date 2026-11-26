"""Basic end to end tests for task queue with single server."""
import asyncio
import operator
import os
import signal
import subprocess
import sys
import unittest

from atq import Q

HOST, PORT = 'localhost', 12345
NUM_WORKERS = 2
TESTS_PATH = 'atq/tests'
NUM_RUNS = 20  # Number of runs in tests.

q = Q([
    (HOST, PORT)
])


async def simple_test(x, y):
    """Executes some basic functions in the task queue."""
    s1 = q.q(operator.add, x, y)
    s2 = q.q(operator.mul, x, y)
    return await q.q(operator.sub, await s2, await s1)


def raise_exception():
    """Raises a ValueError exception."""
    raise ValueError('Hello, world!')


async def exception_test():
    """Raises exception in the task queue."""
    return await q.q(raise_exception)


class SimpleE2ETest(unittest.TestCase):
    """e2e tests for task queue basic functionality."""

    @classmethod
    def setUpClass(cls):
        # Server should be able to import this module to function properly.
        test_env = os.environ.copy()
        test_env["PYTHONPATH"] = TESTS_PATH
        cls.p = subprocess.Popen(
            [sys.executable, '-m', 'atq', '-H', HOST, '-p', str(PORT),
             '-w', str(NUM_WORKERS)], env=test_env, stderr=subprocess.DEVNULL)

    @classmethod
    def tearDownClass(cls):
        os.kill(cls.p.pid, signal.SIGINT)
        cls.p.communicate()

    def testBasic(self):
        """Tests running basic functions."""
        for _ in range(NUM_RUNS):
            result = asyncio.run(simple_test(1, 2))
            self.assertEqual(result, -1)
            result = asyncio.run(simple_test(3, 50))
            self.assertEqual(result, 97)

    def testExceptions(self):
        """Tests exception processing."""
        for _ in range(NUM_RUNS):
            with self.assertRaisesRegex(ValueError, '^Hello, world!$'):
                asyncio.run(exception_test())
