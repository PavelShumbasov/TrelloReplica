from fastapi import APIRouter, Depends
from starlette.requests import Request
from requests import post as req_post

from website.database import get_db
from website.models import TgUser
from website.routers import templates, flash
from website.routers.auth import manager

TOKEN = "5360985085:AAEx-eXJ2WHsHXLMZzBPxWhBNbJNU77wKyQ"
BASE_URL = f"https://api.telegram.org/bot{TOKEN}/"
router = APIRouter(tags=["bot"])


@router.get("/subscribe_on_events")
def subscribe_on_events(request: Request, user=Depends(manager), db=Depends(get_db)):
    tg_user = db.query(TgUser).filter(TgUser.user_id == user.id).first()
    is_subscribed = False
    if tg_user:
        is_subscribed = tg_user.is_subscribed
    return templates.TemplateResponse("subscribe_on_events.html",
                                      {"request": request, "tg_user": tg_user, "is_subscribed": is_subscribed})


@router.post("/subscribe_on_events")
async def subscribe_on_events(request: Request, user=Depends(manager), db=Depends(get_db)):
    tg_id = (await request.form()).get("tg_id")
    tg_user = db.query(TgUser).filter(TgUser.user_id == user.id).first()
    is_subscribed = False
    if not tg_user:
        tg_user = TgUser(user_id=user.id, tg_id=tg_id, is_subscribed=True)
        db.add(tg_user)
        flash(request, "Вы успешно добавили свой аккаунт", "alert alert-success")
    else:
        tg_user.tg_id = tg_id
        tg_user.is_subscribed = True
        is_subscribed = True
        flash(request, "Вы успешно обновили свой аккаунт", "alert alert-success")
    db.commit()
    return templates.TemplateResponse("subscribe_on_events.html",
                                      {"request": request, "tg_user": tg_user, "is_subscribed": is_subscribed})


@router.get("/unsubscribe_from_events")
def unsubscribe_from_events(request: Request, user=Depends(manager), db=Depends(get_db)):
    tg_user = db.query(TgUser).filter(TgUser.user_id == user.id).first()
    if not tg_user:
        flash(request, "Вы не добавили свой Telegram аккаунт", "alert alert-danger")
    else:
        flash(request, "Вы отписались от обновлений", "alert alert-success")
        tg_user.is_subscribed = False
        db.commit()
    return templates.TemplateResponse("subscribe_on_events.html",
                                      {"request": request, "tg_user": tg_user, "is_subscribed": tg_user.is_subscribed})


def send_messages(text, tg_user_id):
    response = req_post(BASE_URL + "sendMessage", data={"chat_id": tg_user_id, "text": text})


def task_added_message(tg_user_id, board_name, col_name, task_name):
    send_messages(f"➕ На доске {board_name} в столбце {col_name} создана новая задача '{task_name}'", tg_user_id)


def task_updated_message(tg_user_id, board_name, col_name):
    send_messages(f"🔵 На доске {board_name} обновлена задача в столбце {col_name}", tg_user_id)


def task_deleted_message(tg_user_id, board_name, col_name):
    send_messages(f"❌ На доске {board_name} удалена задача в столбце {col_name}", tg_user_id)


def col_added_message(tg_user_id, board_name, col_name):
    send_messages(f"➕ На доске {board_name} добавлен столбец {col_name}", tg_user_id)


def col_deleted_message(tg_user_id, board_name, col_name):
    send_messages(f"❌ На доске {board_name} удален столбец {col_name}", tg_user_id)


def collaborator_added_message(tg_user_id, board_name, user_name):
    send_messages(f"➕ На доску {board_name} добавлен новый участник {user_name}", tg_user_id)


def collaborator_deleted_message(tg_user_id, board_name, user_name):
    send_messages(f"❌ С доски {board_name} удален участник {user_name}", tg_user_id)


def as_collaborator_added_message(tg_user_id, board_name):
    send_messages(f"➕ Вы были добавлены на доску {board_name}", tg_user_id)


def board_deleted_message(tg_user_id, board_name):
    send_messages(f"❌ Доска {board_name} была удалена", tg_user_id)