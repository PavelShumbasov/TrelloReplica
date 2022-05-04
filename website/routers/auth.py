from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from typing import Any
from ..models import User
from ..schemas import UserAuth
from ..database import get_db, DBContext
from werkzeug.security import generate_password_hash, check_password_hash
from fastapi_login import LoginManager
from starlette.requests import Request
from starlette.responses import HTMLResponse, RedirectResponse
from authlib.integrations.starlette_client import OAuthError
from . import oauth

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
def load_user(username: str, db: Session = None):
    if db is None:
        with DBContext() as db:
            return db.query(User).filter(User.username == username).first()
    return db.query(User).filter(User.username == username).first()


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

        flash(request, 'User created!', category='alert alert-success')

        access_token = manager.create_access_token(data={"sub": user.username})
        resp = RedirectResponse(url="/ok", status_code=status.HTTP_302_FOUND)
        manager.set_cookie(resp, access_token)
        return resp

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

    elif not check_password_hash(user.password, password):
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


@router.get("/ok")
async def ok(request: Request):
    return "ok"


@router.get("/private")
def get_private_endpoint(user=Depends(manager)):
    print(user)
    return "You are an authentciated user"


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

    user_email = token.get('userinfo', {}).get('email')
    username = token.get('userinfo', {}).get("given_name")

    user = db.query(User).filter(User.email == user_email).first()

    if not user:
        user = User(email=user_email, username=username, password=None)
        db.add(user)
        db.commit()

    access_token = manager.create_access_token(data={"sub": username})
    resp = RedirectResponse(url="/ok", status_code=status.HTTP_302_FOUND)
    manager.set_cookie(resp, access_token)

    return resp
