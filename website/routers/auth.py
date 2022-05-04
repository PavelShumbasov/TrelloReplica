from fastapi import APIRouter, Request, Depends, status
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from typing import Any
from ..models import User
from ..schemas import UserAuth
from ..database import get_db
from werkzeug.security import generate_password_hash, check_password_hash
from fastapi_login import LoginManager  # Login-manager Class
from fastapi_login.exceptions import InvalidCredentialsException  # Exception class

from starlette.config import Config
from starlette.requests import Request
from starlette.middleware.sessions import SessionMiddleware
from starlette.responses import HTMLResponse, RedirectResponse
from authlib.integrations.starlette_client import OAuth, OAuthError
import json


config = Config('../../.env')
oauth = OAuth(config)
print(config)
print(oauth)

CONF_URL = 'https://accounts.google.com/.well-known/openid-configuration'
oauth.register(
    name='google',
    server_metadata_url=CONF_URL,
    client_kwargs={
        'scope': 'openid email profile'
    }
)

router = APIRouter(tags=["auth"])
templates = Jinja2Templates(directory="website/templates")


class NotAuthenticatedException(Exception):
    pass


def exc_handler(request, exc):
    return RedirectResponse(url='/login')


SECRET = "secret-key"
manager = LoginManager(SECRET, "/login", use_cookie=True)
manager.cookie_name = "auth_info"
manager.not_authenticated_exception = NotAuthenticatedException


@manager.user_loader()
def load_user(username: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == username).first()
    return user


def flash(request: Request, message: Any, category: str = "primary") -> None:
    if "_messages" not in request.session:
        request.session["_messages"] = []
    request.session["_messages"].append({"message": message, "category": category})


def get_flashed_messages(request: Request):
    return request.session.pop("_messages") if "_messages" in request.session else []


templates.env.globals['get_flashed_messages'] = get_flashed_messages


@router.get("/sign_up")
async def sign_up(request: Request):
    return templates.TemplateResponse("signup.html", {"request": request})


@router.post("/sign_up")
async def sign_up(request: Request, user: UserAuth = Depends(UserAuth), db: Session = Depends(get_db)):
    email_exists = db.query(User).filter(User.email == user.email).first()
    username_exists = db.query(User).filter(User.username == user.username).first()

    if email_exists:
        flash(request, 'Email is already in use.', category='alert alert-danger')
    elif username_exists:
        flash(request, 'Username is already in use.', category='alert alert-danger')
    elif user.password1 != user.password2:
        flash(request, 'Password do not match!', category='alert alert-danger')
    elif len(user.username) < 5:
        flash(request, 'Username is too short.', category='alert alert-danger')
    elif len(user.password1) < 6:
        flash(request, 'Password is too short.', category='alert alert-danger')
    elif len(user.email) < 4:
        flash(request, "Email is invalid.", category='alert alert-danger')
    else:
        new_user = User(email=user.email, username=user.username, password=generate_password_hash(
            user.password1, method='sha256'))
        db.add(new_user)
        db.commit()
        # login_user(new_user, remember=True)
        flash(request, 'User created!', category='alert alert-success')

    return templates.TemplateResponse("signup.html", {"request": request})


@router.get("/login")
async def login(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@router.post("/login")
async def login(request: Request, data: OAuth2PasswordRequestForm = Depends()):
    username = data.username
    password = data.password
    user = load_user(username)
    if not user:
        flash(request, 'No such username', category='alert alert-danger')
        return templates.TemplateResponse("login.html", {"request": request})
    elif password != user['password']:
        flash(request, 'Incorrect password', category='alert alert-danger')
        return templates.TemplateResponse("login.html", {"request": request})
    else:
        access_token = manager.create_access_token(data={"sub": username})
        resp = RedirectResponse(url="/ok", status_code=status.HTTP_302_FOUND)
        manager.set_cookie(resp, access_token)
    return resp


@router.get('/logout', response_class=HTMLResponse)
def logout(request: Request, user=Depends(manager)):
    resp = RedirectResponse(url="/ok", status_code=status.HTTP_302_FOUND)
    manager.set_cookie(resp, "")
    return resp


@router.post("/ok")
async def ok(request: Request):
    return "ok"


@router.get('/')
async def homepage(request: Request):
    user = request.session.get('user')
    if user:
        data = json.dumps(user)
        html = (
            f'<pre>{data}</pre>'
            '<a href="/logout">logout</a>'
        )
        return HTMLResponse(html)
    return HTMLResponse('<a href="/login">login</a>')


@router.get('/login_google')
async def login(request: Request):
    redirect_uri = request.url_for('auth')
    return await oauth.google.authorize_redirect(request, redirect_uri)


@router.get('/auth')
async def auth(request: Request, db: Session = Depends(get_db)):
    try:
        token = await oauth.google.authorize_access_token(request)
    except OAuthError as error:
        return HTMLResponse(f'<h1>{error.error}</h1>')
    user_email = token.get('email')
    username = token.get("name")

    user = db.query(User).filter(User.email == user_email).first()

    if not user:
        user = User(email=user_email, username=username, password=None)
        db.add(user)
        db.commit()

    access_token = manager.create_access_token(data={"sub": username})
    resp = RedirectResponse(url="/ok", status_code=status.HTTP_302_FOUND)
    manager.set_cookie(resp, access_token)

    return RedirectResponse(url='/ok')
