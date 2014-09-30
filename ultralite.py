#!/usr/bin/env python3
"""
# Ultralite
*For when portability is critical, but you still need some HTTP convenience*

## Author
by Cathal Garvey, copyright 2014, proudly licensed under the
[GNU Affero General Public License](https://www.gnu.org/licenses/agpl-3.0.txt).

* Twitter: @onetruecathal
* Email: cathalgarvey@cathalgarvey.me
* Github: https://github.com/cathalgarvey
* miniLock.io: JjmYYngs7akLZUjkvFkuYdsZ3PyPHSZRBKNm6qTYKZfAM

## About
Anyone who's coded in Python for long will have discovered [Kenneth Reitz's
"Requests" library](http://docs.python-requests.org/en/latest/), which makes
HTTP operations far more clean and straightforward than provided for by the
Python standard library (though things are improving on that score).

Requests is as simple to install as `pip install requests`, and as pip comes
installed with newer distributions of Python, this is really the best way you
can get good HTTP in Python.

However, there are times when you want your code to be portable and not to
depend on even the easiest third-party libraries, and for that there's
Ultralite.

The goal is to support 90% of the convenience of requests, while remaining
short and in-lineable, so you can literally copy/paste all of the code in this
module and drop it into your own code to get a taste of requests, anywhere.

## How do I use this?
The intended use-case is to copy/paste this into your own modules or libraries.
You can also use `pip install ultralight` to install for use in the interactive
interpreter or to list it as a dependency in setup.py.

When copy/pasting, just copy the entire Ultralite class from this module, and
import the standard library modules it requires. Default headers can be added
to the class attribute "_default_headers"; these will be added to *all*
requests' header dictionaries, with user-provided headers overwriting them.

At present this only supports HEAD and GET requests, but will handle
POST/PUT/DELETE in the near future also in a manner similar to requests
(enabled by improvements in the standard library).

Features provided that mimic requests:

* Ultralite methods "get"/"head"/"put"/"post"/"delete" (not all implemented)
* Methods return Ultralite.UltraliteResponse objects which are requests-like:
    - UltraliteResponse.headers -> dict
    - UltraliteResponse.status_code -> int
    - UltraliteResponse.reason -> str
    - UltraliteResponse.content -> bytes
    - UltraliteResponse.text -> unicode decoding of UltraliteResponse.content
    - UltraliteResponse.raw -> http.client.HTTPResponse / urllib.error.XXX
    - UltraliteResponse.request -> urllib.request.Request
    - UltraliteResponse.raise_for_status() -> Raise Ultralite.UltraliteError if
      http response code is not within 2XX range, otherwise do nothing.
    - UltraliteResponse.json() -> attempt json-decoding UltraliteResponse.text

## Does this depend on anything?
Nope. This is valid pure-stdlib python as of Python 3.3+.

"""

import urllib.request
import urllib.parse
import urllib.error
import http.client
import json


class Ultralite:

    class UltraliteError(Exception):
        pass

    class UltraliteResponse:
        def __init__(self, request, response):
            self.request = request
            self.raw = response
            if isinstance(response, http.client.HTTPResponse):
                self.headers = dict(response.getheaders())
                self.status_code = response.status
                self.reason = response.reason
                self.content = response.read()
            elif isinstance(response, urllib.error.HTTPError):
                self.headers = dict(response.headers)
                self.status_code = response.code
                self.reason = response.reason
                self.content = b''
            elif isinstance(response, urllib.error.URLError):
                self.reason = response.reason
                self.status_code = -1
                self.headers = {}
                self.content = b''

        @property
        def text(self):
            return self.content.decode()

        def json(self):
            return json.loads(self.text)

        def raise_for_status(self):
            if not 200 <= self.status_code <= 299:
                raise Ultralite.UltraliteError(
                    "Status code not in 2XX range: {} - {}".format(
                        self.status_code, self.reason))

    _default_headers = {}

    @classmethod
    def call_method(self, method, url, *, headers={}, params=None):
        outbound_headers = self._default_headers.copy()
        outbound_headers.update(headers)
        if params is not None:
            url += "?{}".format(urllib.parse.urlencode(params))
        req = urllib.request.Request(
            url,
            headers=headers,
            method=method)
        try:
            resp = urllib.request.urlopen(req)
        except urllib.error.URLError as e:
            resp = e
        except urllib.error.HTTPError as e:
            resp = e
        return Ultralite.UltraliteResponse(req, resp)

    @classmethod
    def get(self, *a, **kw):
        return self.call_method('GET', *a, **kw)

    @classmethod
    def head(self, *a, **kw):
        return self.call_method('HEAD', *a, **kw)

    @classmethod
    def post(self, *a, **kw):
        raise NotImplementedError("I'll get around to this bit.")

    @classmethod
    def put(self, *a, **kw):
        raise NotImplementedError("I'll get around to this bit.")

    @classmethod
    def delete(self, *a, **kw):
        raise NotImplementedError("I'll get around to this bit.")


if __name__ == "__main__":
    # Tests using httpbin.org
    # Test whether params worked correctly
    import doctest
    doctest.IGNORE_EXCEPTION_DETAIL = True
    Ultralite.__doc__ = """
    Patching in some doctests that would clutter Ultralite otherwise:

    >>> assert 1==2, "Not true"
    Traceback (most recent call last):
    AssertionError: Not true

    >>> Ultralite.get("http://httpbin.org").raise_for_status()

    >>> Ultralite.get("http://httpbin.org/status/404").raise_for_status()
    Traceback (most recent call last):
    UltraliteError: Status code not in 2XX range: 404 - NOT FOUND

    >>> r = Ultralite.get('http://httpbin.org/get',
    ...         params={'foo':'bar'}, headers={'User-Agent':'Ultralite'})
    >>> r.json()['args']['foo']
    'bar'
    >>> r.json()['headers']['User-Agent']
    'Ultralite'

    >>> r = Ultralite.head('http://httpbin.org/get')
    >>> r.raise_for_status()
    >>> r.status_code
    200
    >>> r.content
    b''

    Doctests over.
    """
    doctest.run_docstring_examples(Ultralite, globals(), verbose=False)
else:
    # If imported as a module, alias the top-level functions a-la requests.
    get = Ultralite.get
    head = Ultralite.head
    post = Ultralite.post
    put = Ultralite.put
    delete = Ultralite.delete
