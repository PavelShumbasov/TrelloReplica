from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

DATABASE_URL = "sqlite:///./database.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
session_maker = sessionmaker(bind=engine, autocommit=False, autoflush=False)  # Объект, который создает сессии с бд

Base = declarative_base()


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
