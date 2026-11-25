""""Business" Logic. Whatever that means."""

import os
import logging
from datetime import datetime, timezone
from base64 import b64encode
from model.models import Choices
from model import repo

logger = logging.getLogger("ServiceLogger")
logger.setLevel(logging.DEBUG)
TIME_FORMAT = "%m-%d-%Y"
logger.addHandler(logging.FileHandler(
    f".logs/{datetime.today().strftime(TIME_FORMAT)}.log"))


def get_choices(session, full: bool = False) -> list[Choices]:

    response = repo.get_choices(session)

    if full:
        return response

    return [c.choice for c in response]


def submit_choice(session, choice: str = ""):
    try:
        return repo.submit_choice(session, choice)
    except Exception as e:
        logger.error("%s - ERROR: %s", datetime.now(timezone.utc), str(e))
        raise e


def submit_login(auth: dict[str, str], enc: str) -> bool:
    try:
        if not auth or ("username" not in auth or "password" not in auth):
            return False

        auth['username'] = b64encode(
            auth['username'].encode(enc)).decode(enc)
        auth['password'] = b64encode(
            auth['password'].encode(enc)).decode(enc)
        auth['user_addr'] = b64encode(
            auth['user_addr'].encode(enc)).decode(enc)

        logger.info("%s - INFO: Log in attempt: %s",
                    datetime.now(timezone.utc), auth)

        return repo.submit_auth(auth)
    except Exception as e:
        logger.error("%s - ERROR: %s", datetime.now(timezone.utc), str(e))
        return False


def mng_client_host(session, cip: str, enc: str, choice: str = "", get: bool = False) -> bool:
    try:
        if not cip:
            return False

        crypt = b64encode(cip.encode(enc)).decode(enc)

        if get and not choice:
            logger.info("%s - INFO: fetching %s",
                        datetime.now(timezone.utc), crypt)
            return repo.get_client_ip(crypt, session)

        if choice:
            logger.info("%s - INFO: incoming submission - %s",
                        datetime.now(timezone.utc), {crypt, choice})
            return repo.log_client_host(crypt, choice, session)

        return False

    except Exception as e:
        logger.error("%s - ERROR: %s", datetime.now(timezone.utc), str(e))
        return False


def show_log(log_file: str | None = None):
    try:
        if not log_file:
            raise ValueError("No Log File Was Given.")

        if not os.path.isfile(f".logs/{log_file}.log"):
            return "Log File Was Not Found..."

        log_for_day = []
        with open(file=f".logs/{log_file}.log", OpenTextMode="r", encoding="UTF-8") as f:
            log_for_day = f.readlines()

        return "\n".join(log_for_day)

    except Exception as e:
        logger.error("%s - ERROR: %s", datetime.now(timezone.utc), str(e))
        return "An Error Occurred Attempting To Read Log File."


def rollback(transaction, session):
    try:
        enc = transaction['enc']
        transaction['user_addr'] = b64encode(
            transaction['user_addr'].encode(enc)).decode(enc)
        repo.rollback(session)
        logger.info("rolling back @ %s - Transaction: %s",
                    datetime.now(timezone.utc), transaction)

    except Exception as e:
        logger.error("%s - ERROR: %s", datetime.now(timezone.utc), str(e))
        raise e


def commit(session):
    try:
        logger.info(
            "committing and refreshing db @ %s", datetime.now(timezone.utc))
        repo.commit_and_refresh(session)
        logger.info("refresh complete.")
    except Exception as e:
        logger.error("%s - ERROR: %s", datetime.now(timezone.utc), str(e))
        raise e
