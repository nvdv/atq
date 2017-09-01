# atq
`atq` is a pure-Python asynchronous task queue built to work with `asyncio`.
It is designed to run costly functions outside main event loop using
distributed workers.

`atq` requires Python 3.5+ and is distributed under BSD license.

## Usage
First, you should start workers on the servers you plan to use for task execution
```sh
atq --host <hostname> --port <port-number> --worker <num-workers>
```
where
- `<hostname>` is a hostname of the server
- `<port-number>` is a port that server will listen on
- `<num-workers>` is a number of worker processes

Then you will need to create a client using hostnames and ports of initialized
servers:

```python
import atq

q = atq.Q([
    ("localhost", 12345),
])
```

Finally you can use `atq` in your code:

```python
import atq
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
```
You can find more examples in `examples` subdirectory.

## Installation
At present `atq` can be installed from this repo
```sh
pip3 install -e git+https://github.com/nvdv/atq.git@master#egg=atq
```

## Testing
```sh
python3 setup.py test
```

## License
BSD
