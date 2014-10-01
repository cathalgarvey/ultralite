#!/usr/bin/env python3
"""
## Ultralite
*For when portability is critical, but you still need some HTTP convenience*

### Author
by Cathal Garvey, copyright 2014, proudly licensed under the
[GNU Affero General Public License](https://www.gnu.org/licenses/agpl-3.0.txt).

* Twitter: @onetruecathal
* Email: cathalgarvey@cathalgarvey.me
* Github: https://github.com/cathalgarvey
* miniLock.io: JjmYYngs7akLZUjkvFkuYdsZ3PyPHSZRBKNm6qTYKZfAM

### About
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
And all of this while passing flake8 and pyflakes.

### How do I use this?
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
* Headers can be provided as a dictionary
* GET url parameters can be provided as a dictionary
* Cookies are preserved, and can be provided as "cookies" arg (cookiejars only)
* SSL is attempted automatically for URLs beginning with "https", and raises
  a UltraliteSSLError (distinct from and not deriving from UltraliteError)
  if an SSL handler cannot be successfully constructed; no silent SSL failures!
* Methods return Ultralite.UltraliteResponse objects which are requests-like:
    - UltraliteResponse.headers -> dict
    - UltraliteResponse.status_code -> int
    - UltraliteResponse.reason -> str
    - UltraliteResponse.cookies -> http.cookiejar.CookieJar
    - UltraliteResponse.content -> bytes
    - UltraliteResponse.text -> unicode decoding of UltraliteResponse.content
    - UltraliteResponse.raw -> http.client.HTTPResponse / urllib.error.XXX
    - UltraliteResponse.request -> urllib.request.Request
    - UltraliteResponse.raise_for_status() -> Raise Ultralite.UltraliteError if
      http response code is not within 2XX range, otherwise do nothing.
    - UltraliteResponse.json() -> attempt json-decoding UltraliteResponse.text

Additional features:
* UltraliteResponse.request_context -> urllib.request.OpenerDirector used to
  make the original request; can be re-used for subsequent manual requests,
  in future this may be streamlined to allow request chaining.
* UltraliteResponse.cookies_dict is a dictionary of name:value cookie pairs.
* UltraliteResponse objects support request chaining (with preserved context),
  so you can do (I'm aware this example has no clear use):
  `ultralite.get("http://twitter.com").get("http://twitter.com/me")`
* Chained requests that begin with HTTPS enforce it for subsequent calls:
  `ultralite.get("https://twitter.com").get("http://twitter.com/me") -> Error`

### Known Bugs
* SSL is not yet tested by the doctests suite; desired tests include:
    - SSL verification of a known-good (pinned?) certificate.
    - SSL failure on a self-signed cert.
    - SSL failure on a falsely signed cert.
    - SSL failure on no cert.
    - SSL failure on expired or premature cert.
* Cookies either don't work at all (?) or get lost on 30X redirects, because
  httpbin.org's cookies API seems to fail to set cookies, but features a redir.

### Desired Features
* POST / PUT / DELETE!
* POST with streaming upload
* Get with streaming download
* HTTP Basic Authentication, at least.
* Proxying

### Does this depend on anything?
Nope. This is valid pure-stdlib python as of Python 3.3+.

"""

import urllib.request
import urllib.parse
import urllib.error
import http.client
import http.cookiejar
import json


class Ultralite:

    class UltraliteError(Exception):
        pass

    class UltraliteSSLError(Exception):
        pass

    class UltraliteResponse:
        def __repr__(self):
            return r"UltraliteResponse<'{}', {}>".format(
                self.raw.url, self.status_code)

        def __init__(self, request, response, request_context):
            self.request = request
            self.raw = response
            self.request_context = request_context
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
        def cookies(self):
            if not hasattr(self, "_cookiejar"):
                self._cookiejar = http.cookiejar.CookieJar()
                self._cookiejar.extract_cookies(self.raw, self.request)
            return self._cookiejar

        @property
        def cookies_dict(self):
            return dict([(c.name, c.value) for c in self.cookies])

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

        def _ensure_child_ssl(self, url, skip_ssl=False):
            if self.request.using_ssl and not url.startswith("https"):
                if not skip_ssl:
                    raise Ultralite.UltraliteSSLError(
                        "Chained request using non-SSL on SSL-secured parent!")

        def _chain(self, url, method, *a, **kw):
            self._ensure_child_ssl(url)
            req = Ultralite.construct_request(method, url, *a, **kw)
            req.using_ssl = self.request.using_ssl
            return Ultralite.resolve_call(req, self.request_context)

        def head(self, url, *a, **kw):
            return self._chain(url, 'HEAD', *a, **kw)

        def get(self, url, *a, **kw):
            return self._chain(url, 'GET', *a, **kw)

        def post(self, url, *a, **kw):
            return self._chain(url, 'POST', *a, **kw)

        def put(self, url, *a, **kw):
            return self._chain(url, 'PUT', *a, **kw)

        def delete(self, url, *a, **kw):
            return self._chain(url, 'DELETE', *a, **kw)

    _default_headers = {}

    @classmethod
    def construct_request(self, method, url, *, params=None, headers={}):
        outbound_headers = self._default_headers.copy()
        outbound_headers.update(headers)
        if params is not None:
            url += "?{}".format(urllib.parse.urlencode(params))
        return urllib.request.Request(url, headers=headers, method=method)

    @classmethod
    def create_ssl_handler(self):
        try:
            import ssl
            ssl_context = ssl.create_default_context()
            sslHandler = urllib.request.HTTPSHandler(context=ssl_context)
            return sslHandler
        except Exception as E:
            raise Ultralite.UltraliteSSLError(  # HALT AND CATCH FIRE
                "Failed to establish SSL context: {}".format(E))

    @classmethod
    def call_method(self,
                    method,
                    url,
                    *,
                    headers={},
                    cookies=None,
                    params=None):
        # Construct request separately to context, etcetera; may help
        # when implementing request chaining later on.
        req = self.construct_request(method,
                                     url,
                                     params=params,
                                     headers=headers)
        # Construct handlers
        handlers = []
        if url.startswith("https"):
            # Will raise UltraliteSSLError if it fails to make a handler.
            handlers.append(self.create_ssl_handler())
            req.using_ssl = True
        else:
            req.using_ssl = False
        if cookies is not None:
            if not isinstance(cookies, http.cookiejar.CookieJar):
                raise TypeError("cookies must be a Cookiejar instance.")
            cookiehandler = urllib.request.HTTPCookieProcessor(cookies)
            handlers.append(cookiehandler)
        # Apply handlers
        opener = urllib.request.build_opener(*handlers)
        return self.resolve_call(req, opener)

    @classmethod
    def resolve_call(self, req, opener):
        try:
            resp = opener.open(req)
        except urllib.error.URLError as e:
            resp = e
        except urllib.error.HTTPError as e:
            resp = e
        return Ultralite.UltraliteResponse(req, resp, opener)

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

    >>> r = Ultralite.get('http://www.twitter.com')
    >>> r.status_code
    200
    >>> len(list(iter(r.cookies))) > 0
    True
    >>> '_twitter_sess' in r.cookies_dict
    True
    >>> 'guest_id' in r.cookies_dict
    True

    >>> r = Ultralite.get('http://httpbin.org/cookies/set',
    ...                   params={'foo':'bar'})
    >>> isinstance(r.cookies, http.cookiejar.CookieJar)
    True
    >>> dict(r.cookies).get('foo')
    'bar'

    >>> r = Ultralite.get('https://www.twitter.com')
    >>> r2 = r.get('https://www.twitter.com/onetruecathal')
    >>> r2.status_code
    200
    >>> r2.get('http://www.twitter.com/onetruecathal')
    Traceback (most recent call last):
    UltraliteSSLError: Chained request using non-SSL on SSL-secured parent!

    Doctests over.
    TODO:
        * Need more robust testing of oddities like cookies (httpbin fail?)
        * Need to test SSL: valid (pinned?) cert versus local self-signed?
    """
    doctest.run_docstring_examples(Ultralite, globals(), verbose=False)
else:
    # If imported as a module, alias the top-level functions a-la requests.
    get = Ultralite.get
    head = Ultralite.head
    post = Ultralite.post
    put = Ultralite.put
    delete = Ultralite.delete
