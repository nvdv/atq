import asyncio
import pprint
import requests
import sys
sys.path.append('../atq')  # Required to run examples without installation.
import atq

from collections import ChainMap
from collections import Counter

URLS = {
    "http://www.gutenberg.org/cache/epub/996/pg996.txt",
    "http://www.gutenberg.org/files/1342/1342-0.txt",
    "http://www.gutenberg.org/cache/epub/1661/pg1661.txt",
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
    top = asyncio.get_event_loop().run_until_complete(get_top_words(URLS, 10))
    pprint.pprint(top)
