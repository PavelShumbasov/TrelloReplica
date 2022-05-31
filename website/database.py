from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

from website.config import settings
from website.models import Color

DATABASE_URL = settings.db_url

engine = create_engine(DATABASE_URL)
session_maker = sessionmaker(
    bind=engine, autocommit=False, autoflush=False
)  # Объект, который создает сессии с бд

Base = declarative_base()

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


class DBContext:
    """Контекст обращения к бд (если бд нет, то создать; если есть, то вернуть ссылку на нее)"""

    def __init__(self):
        self.db = session_maker()

    def __enter__(self):
        return self.db

    def __exit__(self, exc_type, exc_value, traceback):
        self.db.close()


def get_db():
    """Функция для получения текущей сессии к БД"""
    with DBContext() as db:
        yield db
