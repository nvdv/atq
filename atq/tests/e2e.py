"""End to end tests for task queue."""
import asyncio
import operator
import os
import signal
import subprocess
import unittest

from atq import Q

HOST, PORT = 'localhost', 12345
NUM_WORKERS = 2

q = Q([
    (HOST, PORT)
])


async def simple_test(x, y):
    """Executes some basic functions in the task queue."""
    s1 = q.q(operator.add, x, y)
    s2 = q.q(operator.mul, x, y)
    return await q.q(operator.sub, await s2, await s1)


class SimpleEndToEndTest(unittest.TestCase):
    """e2e test for task queue basic functionality."""

    @classmethod
    def setUpClass(cls):
        cls.p = subprocess.Popen(
            ['python3', '-m', 'atq', '-H', HOST, '-p', str(PORT),
             '-w', str(NUM_WORKERS)])

    @classmethod
    def tearDownClass(cls):
        os.kill(cls.p.pid, signal.SIGINT)

    def testBasic(self):
        """Tests some basic functions."""
        result = asyncio.get_event_loop().run_until_complete(simple_test(1, 2))
        self.assertEqual(result, -1)
        result = asyncio.get_event_loop().run_until_complete(simple_test(3, 50))
        self.assertEqual(result, 97)
