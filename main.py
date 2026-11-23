"""This is the client and main driver. No need to abstract for something this simple."""
import os
from typing import Annotated
from dotenv import load_dotenv

from fastapi import FastAPI, Request, Form, HTTPException, Response, Depends
from fastapi.responses import RedirectResponse
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
import starlette.status as status
from fastapi.security import OAuth2PasswordRequestForm

from model.service import submit_choice, get_choices, submit_login, mng_client_host

load_dotenv()

app = FastAPI()
app.add_middleware(SessionMiddleware,
                   secret_key=os.environ["API_SESSION_SECRET"],
                   session_cookie="session",
                   max_age=10 * 60,  # 10 minutes
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
                 "password": form.password.strip()
                 }
        if not submit_login(creds, os.environ['ENC']):
            raise HTTPException(status_code=401, detail="Invalid Credentials")
        request.session['active_user'] = form.username

    return RedirectResponse(url=request.url_for("portal"), status_code=status.HTTP_302_FOUND)


@app.get("/form", response_class=HTMLResponse)
async def form(request: Request):
    choices = get_choices()
    user_addr = request.client.host
    enc = os.environ['ENC']
    if 'user_addr' in request.session or mng_client_host(user_addr, enc, get=True):
        return RedirectResponse(url=request.url_for("success"), status_code=status.HTTP_302_FOUND)

    return templates.TemplateResponse(request=request, name="form.html", context={"choices": choices})


@app.post("/form", response_class=HTMLResponse)
async def submit(request: Request, choice: Annotated[str, Form()]):
    if not choice:
        return templates.TemplateResponse(request=request, name="error.html")

    user_addr = request.client.host
    enc = os.environ['ENC']
    if 'user_addr' in request.session or mng_client_host(user_addr, enc, get=True):
        return RedirectResponse(url=request.url_for("success"), status_code=status.HTTP_302_FOUND)

    is_success = submit_choice(choice)
    if not is_success and mng_client_host(user_addr, enc):
        return RedirectResponse(url=request.url_for("error"), status_code=status.HTTP_400_BAD_REQUEST)

    request.session['user_addr'] = user_addr
    return RedirectResponse(url=request.url_for("success"), status_code=status.HTTP_302_FOUND)


@app.get("/portal", response_class=HTMLResponse)
async def portal(request: Request):
    if 'active_user' not in request.session or not request.session['active_user']:
        return RedirectResponse(url=request.url_for("login"), status_code=status.HTTP_302_FOUND)
    choices = get_choices(full=True)
    return templates.TemplateResponse(request=request, name="portal.html", context={"choices": choices})


@app.get("/success", response_class=HTMLResponse)
async def success(request: Request):
    return templates.TemplateResponse(request=request, name="success.html")


@app.get("/error", response_class=HTMLResponse)
async def error(request: Request):
    return templates.TemplateResponse(request=request, name="error.html")
