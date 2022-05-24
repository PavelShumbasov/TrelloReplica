from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from website.database import Base, get_db
from main import app

SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)


class DBContext:
    def __init__(self):
        self.db = TestingSessionLocal()

    def __enter__(self):
        return self.db

    def __exit__(self, exc_type, exc_value, traceback):
        self.db.close()


def override_get_db():
    with DBContext() as db:
        yield db


app.dependency_overrides[get_db] = override_get_db


def debug(text):
    open("debug_file.txt", "w").write(str(text))
