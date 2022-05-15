from typing import Optional
from datetime import date

from pydantic import BaseModel
from fastapi import Form


# Декоратор переименовывает поля в форме для того, чтобы можно было использовать pydantic-модели в запросе
def get_form_body(cls):
    cls.__signature__ = cls.__signature__.replace(
        parameters=[arg.replace(default=Form(...)) for arg in cls.__signature__.parameters.values()])
    return cls


@get_form_body
class UserAuth(BaseModel):
    email: str
    username: str
    password1: str
    password2: str


@get_form_body
class BoardForm(BaseModel):
    name: str
    is_private: bool = False
    theme_id: int


@get_form_body
class TaskForm(BaseModel):
    text: str


@get_form_body
class ColumnForm(BaseModel):
    name: str
    color_id: int


@get_form_body
class TaskEditForm(BaseModel):
    text: str
    tag: str
    deadline: date


@get_form_body
class CollaboratorForm(BaseModel):
    username: str