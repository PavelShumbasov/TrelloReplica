from fastapi import APIRouter, Depends
from starlette.requests import Request

from website.database import get_db
from website.models import TgUser
from website.routers import templates, flash
from website.routers.auth import manager

TOKEN = ""
router = APIRouter(tags=["bot"])


@router.get("/subscribe_on_events")
def subscribe_on_events(request: Request, user=Depends(manager), db=Depends(get_db)):
    tg_user = db.query(TgUser).filter(TgUser.user_id == user.id).first()
    return templates.TemplateResponse("subscribe_on_events.html", {"request": request, "tg_user": tg_user})


@router.post("/subscribe_on_events")
def subscribe_on_events(request: Request, user=Depends(manager), db=Depends(get_db)):
    tg_id = (await request.form()).get("tg_id")
    tg_user = db.query(TgUser).filter(TgUser.user_id == user.id).first()
    if not tg_user:
        tg_user = TgUser(user_id=user.id, tg_id=tg_id, is_subscribed=True)
    else:
        tg_user.tg_id = tg_id
    return templates.TemplateResponse("subscribe_on_events.html", {"request": request, "tg_user": tg_user})


@router.get("/unsubscribe_on_events")
def unsubscribe_on_events(request: Request, user=Depends(manager), db=Depends(get_db)):
    tg_user = db.query(TgUser).filter(TgUser.user_id == user.id).first()
    if not tg_user:
        flash(request, "Вы не добавили свой Telegram аккаунт", "alert alert-danger")
    else:
        flash(request, "Вы отписались от обновлений", "alert alert-danger")
        tg_user.is_subscribed = False
    return templates.TemplateResponse("subscribe_on_events.html", {"request": request, "tg_user": tg_user})

