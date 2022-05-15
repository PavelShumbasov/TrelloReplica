from sqlalchemy import Column, Integer, ForeignKey, String, Date, Boolean, Text
from .database import Base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func


class User(Base):
    __tablename__ = 'user'
    id = Column(Integer, nullable=False, unique=True, primary_key=True, autoincrement=True)
    username = Column(String(64))
    email = Column(String(64))
    password = Column(String(256))

    boards = relationship("Board", back_populates="author")
    tasks = relationship("Task", back_populates="author")
    tg_user = relationship("TgUser", back_populates="user")
    collaborators = relationship("Collaborator", back_populates="user", foreign_keys="Collaborator.user_id")

    def __repr__(self):  # Перегрузка текстового представления
        return f"<User({self.id},{self.username})>"


class Board(Base):
    __tablename__ = "board"
    id = Column(Integer, nullable=False, unique=True, primary_key=True, autoincrement=True)
    name = Column(String(64))
    date_created = Column(Date(), default=func.now())
    is_private = Column(Boolean, default=True)
    author_id = Column(Integer, ForeignKey("user.id", ondelete="CASCADE"), nullable=False)
    theme_id = Column(Integer, ForeignKey("theme.id", ondelete="CASCADE"), nullable=False)

    author = relationship("User", back_populates="boards")
    theme = relationship("Theme", back_populates="boards")
    b_columns = relationship("BColumn", back_populates="board", cascade="all, delete")
    tasks = relationship("Task", back_populates="board", cascade="all, delete")
    collaborators = relationship("Collaborator", back_populates="board", foreign_keys="Collaborator.board_id")

    def __repr__(self):
        return f"<Board({self.id},{self.name})>"


class Theme(Base):
    __tablename__ = "theme"
    id = Column(Integer, nullable=False, unique=True, primary_key=True, autoincrement=True)
    name = Column(String(64))
    info = Column(Text)

    boards = relationship("Board", back_populates="theme")

    def __repr__(self):
        return f"<Theme({self.id},{self.name})>"


class BColumn(Base):
    __tablename__ = "b_column"
    id = Column(Integer, nullable=False, unique=True, primary_key=True, autoincrement=True)
    name = Column(String(64))
    board_id = Column(Integer, ForeignKey("board.id", ondelete="CASCADE"), nullable=False)
    color_id = Column(Integer, ForeignKey("color.id", ondelete="CASCADE"), nullable=False)

    board = relationship("Board", back_populates="b_columns")
    color = relationship("Color", back_populates="b_column")
    tasks = relationship("Task", back_populates="b_column", cascade="all, delete")

    def __repr__(self):
        return f"<BColumn({self.id},{self.name})>"


class Color(Base):
    __tablename__ = "color"
    id = Column(Integer, nullable=False, unique=True, primary_key=True, autoincrement=True)
    value = Column(String(20))
    description = Column(String(15))

    b_column = relationship("BColumn", back_populates="color")

    def __repr__(self):
        return f"<Color({self.id},{self.value})>"


class Task(Base):
    __tablename__ = "task"
    id = Column(Integer, nullable=False, unique=True, primary_key=True, autoincrement=True)
    text = Column(String(128))
    date_created = Column(Date(), default=func.now())
    author_id = Column(Integer, ForeignKey("user.id", ondelete="CASCADE"), nullable=False)
    column_id = Column(Integer, ForeignKey("b_column.id", ondelete="CASCADE"), nullable=False)
    board_id = Column(Integer, ForeignKey("board.id", ondelete="CASCADE"), nullable=False)
    date_deadline = Column(Date(), default=None)

    author = relationship("User", back_populates="tasks")
    b_column = relationship("BColumn", back_populates="tasks")
    board = relationship("Board", back_populates="tasks")
    tag = relationship("Tag", back_populates="task", cascade="all, delete")

    def __repr__(self):
        return f"<Task({self.id},{self.text})>"


class Tag(Base):
    __tablename__ = "tag"
    id = Column(Integer, nullable=False, unique=True, primary_key=True, autoincrement=True)
    text = Column(String(15), default="Нет тэга")
    task_id = Column(Integer, ForeignKey("task.id", ondelete="CASCADE"), default=None)

    task = relationship("Task", back_populates="tag")

    def __repr__(self):
        return f"<Tag({self.id},{self.text})>"


class TgUser(Base):
    __tablename__ = "tg_user"
    id = Column(Integer, nullable=False, unique=True, primary_key=True, autoincrement=True)
    tg_id = Column(Integer, nullable=False, unique=True)
    user_id = Column(Integer, ForeignKey("user.id", ondelete="CASCADE"), nullable=False, unique=True)
    is_subscribed = Column(Boolean, default=False)

    user = relationship("User", back_populates="tg_user")

    def __repr__(self):
        return f"<TgUser({self.tg_id},{self.user_id})>"


class Collaborator(Base):
    __tablename__ = "collaborator"
    id = Column(Integer, nullable=False, unique=True, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("user.id", ondelete="CASCADE"), nullable=False)
    board_id = Column(Integer, ForeignKey("board.id", ondelete="CASCADE"), nullable=False)

    user = relationship("User", back_populates="collaborators", foreign_keys=[user_id])
    board = relationship("Board", back_populates="collaborators", foreign_keys=[board_id])

    def __repr__(self):
        return f"<Collaborator({self.user_id},{self.board_id})>"
