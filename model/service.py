"""This will handle redis logic"""

from base64 import b64encode
from model import repo

"""
TODO: 
    '__cache' will get removed after redis is added.
    so uses of 'global' and associated checks will go with it.

"redis" lol
"""
__cache = {"A": 0, "B": 0}


def get_choices(full: bool = False) -> list[str]:
    global __cache
    if not __cache:
        __cache = repo.get_choices()

    if full:
        return __cache

    return __cache.keys() if __cache.keys() else []


def submit_choice(choice: str = ""):
    try:
        global __cache
        __cache[choice] = __cache.get(choice, 0) + 1
        return repo.submit_choice(__cache)
    except Exception as e:
        print(e)
        return False


def submit_login(auth: dict[str, str], enc: str) -> bool:
    try:
        if not auth or ("username" not in auth or "password" not in auth):
            return False

        auth['username'] = b64encode(
            auth['username'].encode(enc)).decode(enc)
        auth['password'] = b64encode(
            auth['password'].encode(enc)).decode(enc)

        return repo.submit_auth(auth)
    except Exception as e:
        print(e)
        return False


def mng_client_host(cip: str, enc: str, get: bool = False) -> bool:
    try:
        if not cip:
            return False

        crypt = b64encode(cip.encode(enc)).decode(enc)

        if get:
            return repo.get_client_ip(crypt)

        return repo.log_client_host(crypt)

    except Exception as e:
        print(e)
        return False
