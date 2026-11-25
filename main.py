"""This is the client and main driver. No need to abstract for something this simple."""
import os
from typing import Annotated
from contextlib import asynccontextmanager

from dotenv import load_dotenv

from fastapi import FastAPI, Request, Form, HTTPException, Depends
from fastapi.responses import RedirectResponse
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.security import OAuth2PasswordRequestForm

from sqlmodel import Session

from starlette.middleware.sessions import SessionMiddleware
import starlette.status as status

from model.service import submit_choice, get_choices, submit_login, mng_client_host, rollback, commit, show_log
from model.models import startup_engine, get_session

load_dotenv()

SESSION_TIME = 10 * 60  # 10 minutes
DB_SESSION = Annotated[Session, Depends(get_session)]


@asynccontextmanager  # https://fastapi.tiangolo.com/advanced/events/#async-context-manager
async def lifespan(app: FastAPI):
    """https://fastapi.tiangolo.com/advanced/events/#lifespan"""
    startup_engine()
    yield


app = FastAPI(lifespan=lifespan)
app.add_middleware(SessionMiddleware,
                   secret_key=os.environ["API_SESSION_SECRET"],
                   session_cookie="session",
                   max_age=SESSION_TIME,
                   same_site="strict",
                   https_only=os.environ['HTTPS'],  # enable in production
                   )
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")


@app.get('/auth/login', response_class=HTMLResponse)
async def login(request: Request):
    return templates.TemplateResponse(request=request, name="login.html")


@app.post('/auth/login')
async def auth_login(request: Request, form: OAuth2PasswordRequestForm = Depends()):
    if 'active_user' not in request.session or not request.session['active_user']:
        creds = {"username": form.username.strip(),
                 "password": form.password.strip(),
                 "user_addr": request.client.host
                 }
        if not submit_login(creds, os.environ['ENC']):
            raise HTTPException(status_code=401, detail="Invalid Credentials")
        request.session['active_user'] = form.username

    if "return_to" in request.session:
        return_to = request.session.get("return_to", "")
        RedirectResponse(url=request.url_for(return_to),
                         status_code=status.HTTP_302_FOUND)
    return RedirectResponse(url=request.url_for("portal"), status_code=status.HTTP_302_FOUND)


@app.get("/form", response_class=HTMLResponse)
async def form(request: Request, session: DB_SESSION):
    choices = get_choices(session)
    user_addr = request.client.host
    enc = os.environ['ENC']
    if 'user_addr' in request.session or mng_client_host(session, user_addr, enc, get=True):
        request.session['user_addr'] = user_addr
        return RedirectResponse(url=request.url_for("success"), status_code=status.HTTP_302_FOUND)

    return templates.TemplateResponse(request=request, name="form.html", context={"choices": choices})


@app.post("/form", response_class=HTMLResponse)
async def submit(request: Request, choice: Annotated[str, Form()], session: DB_SESSION):
    if not choice:
        return templates.TemplateResponse(request=request, name="error.html")

    user_addr = request.client.host
    enc = os.environ['ENC']

    is_success = (mng_client_host(session=session, cip=user_addr,
                  enc=enc, choice=choice) and submit_choice(session, choice))
    if not is_success:
        transaction = {
            'user_addr': user_addr,
            'choice': choice,
            'enc': enc
        }
        rollback(transaction, session)
        return RedirectResponse(url=request.url_for("error"), status_code=status.HTTP_400_BAD_REQUEST)

    request.session['user_addr'] = user_addr
    commit(session)
    return RedirectResponse(url=request.url_for("success"), status_code=status.HTTP_302_FOUND)


@app.get("/portal", response_class=HTMLResponse)
async def portal(request: Request, session: DB_SESSION):
    if 'active_user' not in request.session or not request.session['active_user']:
        return RedirectResponse(url=request.url_for("login"), status_code=status.HTTP_302_FOUND)
    choices = get_choices(session, full=True)
    return templates.TemplateResponse(request=request, name="portal.html", context={"choices": choices})


@app.get("/success", response_class=HTMLResponse)
async def success(request: Request):
    return templates.TemplateResponse(request=request, name="success.html")


@app.get("/error", response_class=HTMLResponse)
async def error(request: Request):
    return templates.TemplateResponse(request=request, name="error.html")


@app.get("/log/{log_file}")
async def show_log_file(request: Request, log_file: str | None = None):
    if 'user_addr' not in request.session:
        request.session['return_to'] = f'/log/{log_file}'
        return RedirectResponse(url=request.url_for("login"), status_code=status.HTTP_302_FOUND)

    return show_log(log_file)


@app.get("/show_logs", response_class=HTMLResponse)
async def show_logs(request: Request):
    # TODO: just show all of the log files in a <ul> with <a> tags opening the file on click.
    pass


@app.get("/download")
async def download_form(request: Request):
    # TODO: allow admins to download submission data as csv
    pass
