"""repository layer for interacting with sqlite file"""
import os

from dotenv import load_dotenv

load_dotenv()

# TODO: replace with actual sqlite code - in memory for now.
__sqlite = {"choices": {},
            "ip_addr": {}}


def get_choices() -> dict:
    # query = "select * from choices
    # TODO: get data from sqlite3 after i create that.
    return {"A": 0, "B": 0}


def submit_choice(choices: dict):
    # do sqlite stuff here
    print(choices)
    return True


def submit_auth(auth: dict[str, str]) -> bool:
    user = os.environ['USER']
    pwd = os.environ['USER_CRED']

    return auth['username'] == user and auth['password'] == pwd


def log_client_host(cip: str) -> bool:
    global __sqlite
    __sqlite['ip_addr'][cip] = cip
    return True


def get_client_ip(cip: str) -> str:
    global __sqlite
    return "" != __sqlite['ip_addr'].get(cip, "")
