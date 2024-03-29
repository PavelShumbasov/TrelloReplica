from typing import Callable

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
    """Отрисовка страницы для подписки на уведомления"""
    tg_user = db.query(TgUser).filter(TgUser.user_id == user.id).first()
    is_subscribed = False
    if tg_user:
        is_subscribed = tg_user.is_subscribed
    return templates.TemplateResponse(
        "subscribe_on_events.html",
        {"request": request, "tg_user": tg_user, "is_subscribed": is_subscribed},
    )


@router.post("/subscribe_on_events")
async def subscribe_on_events(
    request: Request, user=Depends(manager), db=Depends(get_db)
):
    """Подписка на уведомления с помощью id для телеграма"""
    tg_id = (await request.form()).get("tg_id")
    tg_user = db.query(TgUser).filter(TgUser.user_id == user.id).first()
    is_subscribed = tg_user.is_subscribed if tg_user else False
    print(tg_id.isalpha())
    if not tg_id.isdigit() or len(tg_id) != 9:
        flash(request, "Введите корректный id", "alert alert-danger")
        return templates.TemplateResponse(
            "subscribe_on_events.html",
            {"request": request, "tg_user": tg_user, "is_subscribed": is_subscribed},
        )
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
    return templates.TemplateResponse(
        "subscribe_on_events.html",
        {"request": request, "tg_user": tg_user, "is_subscribed": is_subscribed},
    )


@router.get("/unsubscribe_from_events")
def unsubscribe_from_events(
    request: Request, user=Depends(manager), db=Depends(get_db)
):
    """Отписываемся от уведомлений бота"""
    tg_user = db.query(TgUser).filter(TgUser.user_id == user.id).first()
    is_subscribed = False
    if not tg_user:
        flash(request, "Вы не добавили свой Telegram аккаунт", "alert alert-danger")
    else:
        flash(request, "Вы отписались от обновлений", "alert alert-success")
        tg_user.is_subscribed = False
        db.commit()
    return templates.TemplateResponse(
        "subscribe_on_events.html",
        {
            "request": request,
            "tg_user": tg_user,
            "is_subscribed": is_subscribed,
        },
    )


def send_messages(text, tg_user_id):  # pragma: no cover
    """Универсальная функция, которая совершает запрос к телеграм бот API"""
    response = req_post(
        BASE_URL + "sendMessage", data={"chat_id": tg_user_id, "text": text}
    )


"""Описание сообщений для различных событий"""


def task_added_message(tg_user_id, board_name, col_name, task_name):  # pragma: no cover
    send_messages(
        f"➕ На доске {board_name} в столбце {col_name} создана новая задача '{task_name}'",
        tg_user_id,
    )


def task_updated_message(tg_user_id, board_name, col_name):  # pragma: no cover
    send_messages(
        f"🔵 На доске {board_name} обновлена задача в столбце {col_name}", tg_user_id
    )


def task_deleted_message(tg_user_id, board_name, col_name):  # pragma: no cover
    send_messages(
        f"❌ На доске {board_name} удалена задача в столбце {col_name}", tg_user_id
    )


def col_added_message(tg_user_id, board_name, col_name):  # pragma: no cover
    send_messages(f"➕ На доске {board_name} добавлен столбец {col_name}", tg_user_id)


def col_deleted_message(tg_user_id, board_name, col_name):  # pragma: no cover
    send_messages(f"❌ На доске {board_name} удален столбец {col_name}", tg_user_id)


def collaborator_added_message(tg_user_id, board_name, user_name):  # pragma: no cover
    send_messages(
        f"➕ На доску {board_name} добавлен новый участник {user_name}", tg_user_id
    )


def collaborator_deleted_message(tg_user_id, board_name, user_name):  # pragma: no cover
    send_messages(f"❌ С доски {board_name} удален участник {user_name}", tg_user_id)


def as_collaborator_added_message(tg_user_id, board_name):  # pragma: no cover
    send_messages(f"➕ Вы были добавлены на доску {board_name}", tg_user_id)


def board_deleted_message(tg_user_id, board_name):  # pragma: no cover
    send_messages(f"❌ Доска {board_name} была удалена", tg_user_id)


def import_to_board_message(tg_user_id, board_name, user_name):  # pragma: no cover
    send_messages(
        f"🔵 Доска {board_name} была обновлена пользователем {user_name} с помощью импорта",
        tg_user_id,
    )


def task_moved_message(tg_user_id, board_name, task_name, col_name):  # pragma: no cover
    send_messages(
        f"🔵 На доске {board_name} в колонку {col_name} была перемещена задача {task_name}",
        tg_user_id,
    )


def board_edit_message(tg_user_id, board_name, user_name):  # pragma: no cover
    send_messages(
        f"🔵 Доска {board_name} была изменена пользователем {user_name}",
        tg_user_id,
    )


def column_edit_message(
    tg_user_id, board_name, col_name, user_name
):  # pragma: no cover
    send_messages(
        f"🔵 На доске {board_name} была изменена колонка {col_name} пользователем {user_name}",
        tg_user_id,
    )


def task_deadline_message(
    tg_user_id, board_name, col_name, task_name
):  # pragma: no cover
    send_messages(
        f"🔵 На доске {board_name} в колонке {col_name} завтра наступает дедлайн задачи {task_name}",
        tg_user_id,
    )


def send_notification(
    tg_users: list, send_message: Callable, *params
):  # pragma: no cover
    """Отправка уведомлений в телеграм боте"""
    for tg_user in tg_users:
        send_message(tg_user.tg_id, *params)
