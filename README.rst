atq
===
``atq`` is a pure-Python asynchronous task queue built to work with ``asyncio``.
It is designed to run costly functions outside main event loop using
distributed workers.

``atq`` requires Python 3.5+ and is distributed under BSD license.

Usage
-----
First, you should start workers on the servers you plan to use for task execution

    .. code-block ::
        atqserver --host <hostname> --port <port-number> --worker <num-workers>

where
- ``<hostname>`` is a hostname of the server
- ``<port-number>`` is a port that server will listen on
- ``<num-workers>`` is a number of worker processes

Please note that code of tasks should be accessible by ``atq``, so it's advised
to run ``atq`` server from your project root directory in more complex
situations.

Then you will need to create a client using hostnames and ports of initialized
servers:

.. highlight:: python
    import atq

    q = atq.Q([
        ("localhost", 12345),
    ])


Finally you can use ``atq`` in your code:

.. highlight:: python
    import atq
    import asyncio
    import requests
    from collections import ChainMap
    from collections import Counter

    URLS = [
        ...
    ]

    q = atq.Q([
        ("localhost", 12345),
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

    top = asyncio.get_event_loop().run_until_complete(get_top_words(URLS, 10))

You can find more examples in ``examples`` subdirectory.

Installation
------------
.. code-block ::
    pip3 install atq


Testing
-------
.. code-block ::
    python3 setup.py test


License
-------
BSD
