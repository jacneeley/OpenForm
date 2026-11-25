"""repository layer for interacting with sqlite file"""
import os
from datetime import datetime, timezone
from typing import Annotated

from dotenv import load_dotenv
from fastapi import Depends
from sqlmodel import Session, select

from model.models import get_session, Choices, Submission

load_dotenv()
DB_SESSION = Annotated[Session, Depends(get_session)]


def get_choices(session: DB_SESSION) -> list[Choices]:
    return session.exec(select(Choices)).all()


def submit_choice(session: DB_SESSION, choice):
    choice_rec = session.exec(select(Choices).where(
        Choices.choice == choice)).first()
    if not choice_rec:
        return False

    choice_rec.count = choice_rec.count + 1
    choice_data = choice_rec.model_dump(exclude_unset=True)
    choice_rec.sqlmodel_update(choice_data)
    session.add(choice_rec)

    return True


def submit_auth(auth: dict[str, str]) -> bool:
    user = os.environ['USER']
    pwd = os.environ['USER_CRED']

    return auth['username'] == user and auth['password'] == pwd


def log_client_host(cip: str, choice: str, session: DB_SESSION) -> bool:
    db_submission = session.get(Submission, cip)
    if db_submission:
        return False

    sub = Submission(user_addr=cip, user_choice=choice,
                     create_time=datetime.now(timezone.utc))

    db_submission = Submission.model_validate(sub)
    session.add(db_submission)

    return True


def get_client_ip(cip: str, session: DB_SESSION) -> bool:
    submission = session.get(Submission, cip)
    if not submission:
        return False

    return cip == submission.user_addr


def rollback(session: DB_SESSION):
    session.rollback()


def commit_and_refresh(session: DB_SESSION) -> None:
    session.commit()

    choices = get_choices(session)
    for c in choices:
        session.refresh(c)

    submissions = session.exec(select(Submission)).all()
    for s in submissions:
        session.refresh(s)
