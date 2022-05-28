from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from ..models import User, TgUser
from ..schemas import UserAuth
from ..database import get_db, DBContext
from werkzeug.security import generate_password_hash, check_password_hash
from fastapi_login import LoginManager
from starlette.requests import Request
from starlette.responses import HTMLResponse, RedirectResponse
from authlib.integrations.starlette_client import OAuthError
from . import oauth, templates, flash
from datetime import timedelta

router = APIRouter(tags=["auth"])  # Создаем подприложение


# Класс-исключение, которое будет выбрасываться, если пользователь неавторизован
class NotAuthenticatedException(Exception):
    pass


# Обработчик исключения "не авторизованный пользователь"
def exc_handler(request, exc):
    return RedirectResponse(url='/login')


# Модуль fastapi_login внутри использует json web-tokens
SECRET = "secret-key"  # Секретный ключ для поддержки сессии между клиентом и сервером
manager = LoginManager(SECRET, "/login", use_cookie=True)
manager.cookie_name = "auth_info"
manager.not_authenticated_exception = NotAuthenticatedException


@manager.user_loader()
def load_user(username: str, db: Session = None):
    """Описание поведения для получения пользователя из бд LoginManager"""
    if db is None:
        with DBContext() as db:
            return db.query(User).filter(User.username == username).first()
    return db.query(User).filter(User.username == username).first()


@router.get("/sign_up")
async def sign_up(request: Request):
    """Отрисовка страницы регистрации"""
    return templates.TemplateResponse("signup.html", {"request": request})


@router.post("/sign_up")
async def sign_up(request: Request, user: UserAuth = Depends(UserAuth), db: Session = Depends(get_db)):
    """Валидация регистрационных данных и создание пользователя"""
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
        tg_user = TgUser(user_id=new_user.id, tg_id=None)
        db.add(tg_user)
        db.commit()

        flash(request, 'User created!', category='alert alert-success')

        access_token = manager.create_access_token(
            data={"sub": user.username})  # Создание токена доступа Логин менеджером для авторизации пользователя
        resp = RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)
        manager.set_cookie(resp, access_token)
        return resp

    return templates.TemplateResponse("signup.html", {"request": request})


@router.get("/login")
async def login(request: Request):
    """Отрисовка шаблона для авторизации"""
    return templates.TemplateResponse("login.html", {"request": request})


@router.post("/login")
async def login(request: Request, data: OAuth2PasswordRequestForm = Depends()):
    """Авторизация пользователя."""
    username = data.username
    password = data.password
    remember_me = (await request.form()).get("remember_me")
    user = load_user(username)

    token_time = None
    if remember_me:
        token_time = timedelta(weeks=4)

    if not user:
        flash(request, 'No such username', category='alert alert-danger')
        return templates.TemplateResponse("login.html", {"request": request})

    elif not check_password_hash(user.password, password):
        flash(request, 'Incorrect password', category='alert alert-danger')
        return templates.TemplateResponse("login.html", {"request": request})
    else:
        access_token = manager.create_access_token(data={"sub": username}, expires=token_time)
        resp = RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)
        manager.set_cookie(resp, access_token)
    return resp


@router.get('/logout', response_class=HTMLResponse)
def logout(request: Request, user: User = Depends(manager)):
    """Выход из аккаунта. Переход на страница login, очистка cookies"""
    resp = RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    manager.set_cookie(resp, "")
    return resp


@router.get('/login_google')
async def login_google(request: Request):
    """OAUTH2 с помощью Google."""
    redirect_uri = request.url_for('auth')
    return await oauth.google.authorize_redirect(request, redirect_uri)


@router.get('/auth')
async def auth(request: Request, db: Session = Depends(get_db)):
    """Авторизация на сайте с помощью токена из гугл. Заменяем гугл-токен на нашу альтернативу"""
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

    access_token = manager.create_access_token(data={"sub": username}, expires=timedelta(weeks=4))
    resp = RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)
    manager.set_cookie(resp, access_token)

    return resp


@router.get("/edit")
async def edit(request: Request, user: User = Depends(manager)):
    """Отрисовка шаблона для редактирования профиля"""
    return templates.TemplateResponse("edit_profile.html", {"request": request, "user": user})


@router.post("/edit")
async def edit(request: Request, user: UserAuth = Depends(UserAuth), db: Session = Depends(get_db),
               current_user: User = Depends(manager)):
    """Валидация данных и редактирование аккаунта"""
    email_exists = db.query(User).filter(User.email == user.email).first()
    username_exists = db.query(User).filter(User.username == user.username).first()

    if email_exists and email_exists.email != current_user.email:
        flash(request, 'Email is already in use.', category='alert alert-danger')
    elif username_exists and username_exists.username != current_user.username:
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
        updated_user = db.query(User).filter(User.id == current_user.id).first()
        updated_user.email = user.email
        updated_user.username = user.username
        updated_user.password = generate_password_hash(user.password1, method='sha256')
        db.commit()
        flash(request, 'User updated!', category="alert alert-info")

        access_token = manager.create_access_token(data={"sub": updated_user.username})
        resp = RedirectResponse(url="/edit", status_code=status.HTTP_302_FOUND)
        manager.set_cookie(resp, access_token)
        return resp

    return templates.TemplateResponse("edit_profile.html", {"request": request})
