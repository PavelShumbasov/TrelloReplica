from typing import Any, List

from starlette.config import Config
from authlib.integrations.starlette_client import OAuth
from starlette.requests import Request
from starlette.templating import Jinja2Templates
from fastapi import WebSocket

from website.database import session_maker
from website.models import Color

config = Config(
    ".env"
)  # Получаем кофигурационные переменные (токены для гугл аккаунта)
oauth = OAuth(config)  # Создаем объект для гугл авторизации из полученных токенов
CONF_URL = "https://accounts.google.com/.well-known/openid-configuration"

# Конфигурация объекта для авторизации через гугл
oauth.register(
    name="google",
    server_metadata_url=CONF_URL,
    client_kwargs={"scope": "openid email profile"},
)

# Объект для отрисовки шаблонов с помощью Jinja2Templates
templates = Jinja2Templates(directory="website/templates")

session = session_maker()
is_color = session.query(Color).filter(Color.id == 1).first()

if not is_color:
    color_blue = Color(id=1, value="primary", description="Синий")
    session.add(color_blue)
    color_gray = Color(id=2, value="secondary", description="Серый")
    session.add(color_gray)
    color_green = Color(id=3, value="success", description="Зелёный")
    session.add(color_green)
    color_red = Color(id=4, value="danger", description="Красный")
    session.add(color_red)
    color_yellow = Color(id=5, value="warning", description="Жёлтый")
    session.add(color_yellow)
    color_light_blue = Color(id=6, value="info", description="Голубой")
    session.add(color_light_blue)
    color_black = Color(id=7, value="dark", description="Чёрный")
    session.add(color_black)
    session.commit()


def flash(request: Request, message: Any, category: str = "primary") -> None:
    """Функция, которая вставляет новую информацию в запрос для отрисовки уведомлений"""
    if "_messages" not in request.session:
        request.session["_messages"] = []
    request.session["_messages"].append({"message": message, "category": category})


def get_flashed_messages(request: Request):
    """Получение данных с запроса"""
    return request.session.pop("_messages") if "_messages" in request.session else []


# Регистрация функции внутри шаблонов
templates.env.globals["get_flashed_messages"] = get_flashed_messages


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
