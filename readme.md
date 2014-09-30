
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
And all of this while passing flake8 and pyflakes.

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

