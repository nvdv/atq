"""Top N words example.

Gets text file, counts number of words in them and returns top N words in
every file.

To run this example run workers first:

    python3 -m atq --host localhost --port 12345
    python3 -m atq --host localhost --port 12346
    python3 -m atq --host localhost --port 12347

and then run

    python3 examples/topn.py

"""
import asyncio
import os
import pprint
import requests
import sys

# Required to run examples without installation.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import atq

from collections import ChainMap
from collections import Counter

URLS = {
    "https://raw.githubusercontent.com/python/peps/main/peps/pep-0008.rst",
    "https://raw.githubusercontent.com/python/peps/main/peps/pep-0492.rst",
    "https://raw.githubusercontent.com/python/peps/main/peps/pep-0634.rst",
}

q = atq.Q([
    ("localhost", 12345),
    ('localhost', 12346),
    ('localhost', 12347),
])


def top_words(url, n):
    """Returns top n words from text specified by url."""
    text = requests.get(url).text.split()
    return {url: Counter(text).most_common(n)}


async def get_top_words(urls, n):
    """Returns top n words in documents specified by URLs."""
    tops_in_url = await asyncio.gather(
        *[q.q(top_words, url, n) for url in urls])
    return ChainMap(*tops_in_url)


if __name__ == '__main__':
    top = asyncio.run(get_top_words(URLS, 10))
    pprint.pprint(top)
