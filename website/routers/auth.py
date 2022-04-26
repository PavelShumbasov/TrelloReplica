from fastapi import APIRouter, Request, Depends
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from typing import Any
from ..models import User
from ..schemas import UserAuth
from ..database import get_db

router = APIRouter(tags=["auth"])
templates = Jinja2Templates(directory="website/templates")


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
async def sign_up(user: UserAuth = Depends(UserAuth), db: Session = Depends(get_db)):
    email_exists = db.query(User).filter(User.email == user.email).first()
    username_exists = db.query(User).filter(User.username == user.username).first()

    if email_exists:
        flash(user.dict(), 'Email is already in use.', category='alert alert-danger')
    elif username_exists:
        flash(user.dict(), 'Username is already in use.', category='alert alert-danger')
    elif user.password1 != user.password2:
        flash(user.dict(), 'Password do not match!', category='alert alert-danger')
    elif len(user.username) < 5:
        flash(user.dict(), 'Username is too short.', category='alert alert-danger')
    elif len(user.password1) < 6:
        flash(user.dict(), 'Password is too short.', category='alert alert-danger')
    elif len(user.email) < 4:
        flash(user.dict(), "Email is invalid.", category='alert alert-danger')
    else:
        new_user = User(email=user.email, username=user.username, password=user.generate_password_hash(
            user.password1, method='sha256'))
        db.add(new_user)
        db.commit()
        # login_user(new_user, remember=True)
        flash(user.dict(), 'User created!', category='alert alert-success')

    return templates.TemplateResponse("signup.html", {"request": user.dict()})
