from typing import Any, List

from starlette.config import Config
from authlib.integrations.starlette_client import OAuth
from starlette.requests import Request
from starlette.templating import Jinja2Templates
from fastapi import WebSocket

config = Config('.env')  # Получаем кофигурационные переменные (токены для гугл аккаунта)
oauth = OAuth(config)  # Создаем объект для гугл авторизации из полученных токенов
CONF_URL = 'https://accounts.google.com/.well-known/openid-configuration'

# Конфигурация объекта для авторизации через гугл
oauth.register(
    name='google',
    server_metadata_url=CONF_URL,
    client_kwargs={
        'scope': 'openid email profile'
    }
)

# Объект для отрисовки шаблонов с помощью Jinja2Templates
templates = Jinja2Templates(directory="website/templates")


def flash(request: Request, message: Any, category: str = "primary") -> None:
    """Функция, которая вставляет новую информацию в запрос для отрисовки уведомлений"""
    if "_messages" not in request.session:
        request.session["_messages"] = []
    request.session["_messages"].append({"message": message, "category": category})


def get_flashed_messages(request: Request):
    """Получение данных с запроса"""
    return request.session.pop("_messages") if "_messages" in request.session else []


# Регистрация функции внутри шаблонов
templates.env.globals['get_flashed_messages'] = get_flashed_messages


class ConnectionManager:
    """Объект, который хранит данные о подключенных соединениях и отсоединяет их в случае отключения."""

    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)


connection_manager = ConnectionManager()
