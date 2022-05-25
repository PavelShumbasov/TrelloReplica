import json
from typing import Callable
from datetime import datetime

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from starlette import status
from starlette.requests import Request
from starlette.responses import RedirectResponse

from . import templates, flash, connection_manager
from .auth import manager
from .bot import task_added_message, task_deleted_message, task_updated_message, collaborator_added_message, \
    as_collaborator_added_message, collaborator_deleted_message, col_added_message, col_deleted_message, \
    board_deleted_message, send_notification
from ..database import get_db
from ..models import Board, User, Theme, Task, BColumn, Color, Tag, Collaborator, TgUser
from ..schemas import BoardForm, ColumnForm, TaskForm, CollaboratorForm, ThemeForm

router = APIRouter(tags=["views"])


@router.get("/")
def home(request: Request, user: User = Depends(manager), db: Session = Depends(get_db)):
    """Отрисовка шаблона главной страницы. Достаем все публичные доски"""
    boards = db.query(Board).where((Board.is_private == False)
                                   | ((Board.is_private == True) & (Board.author_id == user.id))).all()
    return templates.TemplateResponse("home.html", {"request": request, "boards": boards})


@router.get("/my_boards")
def my_boards(request: Request, user: User = Depends(manager), db: Session = Depends(get_db)):
    """Отображаем все доски текущего пользователя"""
    boards = db.query(Board).filter(Board.author_id == user.id).all()
    collaborators = db.query(Collaborator).filter(Collaborator.user_id == user.id).all()
    for collab in collaborators:
        boards.append(collab.board)

    return templates.TemplateResponse("my_boards.html", {"request": request, "boards": boards})


@router.get("/add_board")
def add_board(request: Request, user: User = Depends(manager), db: Session = Depends(get_db)):
    """Отрисовка шаблона добавления доски."""
    themes = db.query(Theme).all()
    return templates.TemplateResponse("add_board.html", {"request": request, "themes": themes})


@router.post("/add_board")
async def add_board(request: Request, user: User = Depends(manager), db: Session = Depends(get_db)):
    """Создание новой доски"""
    board = BoardForm(**await request.form())
    new_board = Board(name=board.name, author_id=user.id, is_private=board.is_private, theme_id=board.theme_id)
    db.add(new_board)
    db.commit()
    return RedirectResponse(url="/my_boards", status_code=status.HTTP_302_FOUND)


@router.get("/board/{id}")
async def view_board(id: int, request: Request, current_user: User = Depends(manager), db: Session = Depends(get_db)):
    """Просмотр доски, перетаскивание заданий"""
    board = db.query(Board).filter(Board.id == id).first()
    can_delete = False
    if board:
        can_delete = board.author.id == current_user.id or any(
            [current_user.id == collab.user_id for collab in board.collaborators])

    if not board or (not can_delete and board.is_private):
        return templates.TemplateResponse("no_board.html",
                                          {"request": request})

    colors = db.query(Color).all()
    return templates.TemplateResponse("view_board.html",
                                      {"request": request, "board": board, "can_delete": can_delete, "colors": colors,
                                       "user": current_user})


@router.get("/delete_board/{id}")
def delete_board(id: int, request: Request, current_user: User = Depends(manager), db: Session = Depends(get_db)):
    """Удаление доски"""
    board = db.query(Board).filter(Board.id == id).first()
    can_delete = False
    if board:
        can_delete = board.author.id == current_user.id

    if not board or not can_delete:
        return templates.TemplateResponse("no_board.html",
                                          {"request": request})
    collaborators = db.query(Collaborator).filter(Collaborator.board_id == board.id).all()
    for collaborator in collaborators:
        db.delete(collaborator)
    tg_users = get_participants_tg_id(db, board, current_user)
    send_notification(tg_users, board_deleted_message, board.name)

    db.delete(board)
    db.commit()

    return RedirectResponse(url="/my_boards", status_code=status.HTTP_302_FOUND)


@router.post("/add_column/{id}")
def add_column(id: int, request: Request, current_user: User = Depends(manager), db: Session = Depends(get_db),
               column: ColumnForm = Depends(ColumnForm)):
    """Добавление нового столбца в доске"""
    new_column = BColumn(name=column.name, color_id=column.color_id, board_id=id)
    db.add(new_column)
    db.commit()

    tg_users = get_participants_tg_id(db, new_column.board, current_user)
    send_notification(tg_users, col_added_message, new_column.board.name, new_column.name)

    return RedirectResponse(url=f"/board/{id}", status_code=status.HTTP_302_FOUND)


@router.get("/delete_column/{column_id}")
def delete_column(column_id: int, request: Request, current_user: User = Depends(manager),
                  db: Session = Depends(get_db)):
    """Удаление столбца из доски"""
    column = db.query(BColumn).filter(BColumn.id == column_id).first()
    board_id = column.board_id
    can_delete = column.board.author.id == current_user.id or any(
        [current_user.id == collab.user_id for collab in column.board.collaborators])

    if not can_delete:
        return templates.TemplateResponse("no_board.html", {"request": request})
    db.delete(column)
    db.commit()

    tg_users = get_participants_tg_id(db, column.board, current_user)
    send_notification(tg_users, col_deleted_message, column.board.name, column.name)

    return RedirectResponse(url=f"/board/{board_id}", status_code=status.HTTP_302_FOUND)


@router.post("/add_task/{board_id}/{column_id}")
def add_task(board_id: int, column_id: int, request: Request, current_user: User = Depends(manager),
             db: Session = Depends(get_db),
             task: TaskForm = Depends(TaskForm)):
    """Добавление задания в столбец"""
    new_task = Task(text=task.text, author_id=current_user.id, board_id=board_id, column_id=column_id)
    db.add(new_task)
    db.commit()

    tg_users = get_participants_tg_id(db, new_task.board, current_user)
    send_notification(tg_users, task_added_message, new_task.board.name, new_task.b_column.name, new_task.text)

    return RedirectResponse(url=f"/board/{board_id}", status_code=status.HTTP_302_FOUND)


@router.get("/delete_task/{task_id}")
def delete_task(task_id: int, request: Request, current_user: User = Depends(manager), db: Session = Depends(get_db)):
    """Удаление задания из столбца"""
    task = db.query(Task).filter(Task.id == task_id).first()
    board_id = task.board_id
    can_delete = task.board.author.id == current_user.id or any(
        [current_user.id == collab.user_id for collab in task.board.collaborators])
    if not can_delete:
        return templates.TemplateResponse("no_board.html", {"request": request})

    tg_users = get_participants_tg_id(db, task.board, current_user)
    send_notification(tg_users, task_deleted_message, task.board.name, task.b_column.name)

    db.delete(task)
    db.commit()
    return RedirectResponse(url=f"/board/{board_id}", status_code=status.HTTP_302_FOUND)


@router.get("/edit_task/{task_id}")
def edit_task(task_id: int, request: Request, current_user: User = Depends(manager), db: Session = Depends(get_db)):
    """Отрисовка страницы редактирования задания"""
    task = db.query(Task).filter(Task.id == task_id).first()
    can_delete = task.board.author.id == current_user.id or any(
        [current_user.id == collab.user_id for collab in task.board.collaborators])

    if not can_delete:
        return templates.TemplateResponse("no_board.html", {"request": request})
    return templates.TemplateResponse("edit_task.html", {"request": request, "task": task})


@router.post("/edit_task/{id}")
async def edit_task(id: int, request: Request, current_user: User = Depends(manager), db: Session = Depends(get_db)):
    """Редактирование задания. Валидация данных"""
    task = db.query(Task).filter(Task.id == id).first()
    text = (await request.form()).get("text")
    tag_form = (await request.form()).get("tag", "No tag")
    deadline = (await request.form()).get("deadline")
    if tag_form != "No tag":
        tag = db.query(Tag).filter(Tag.task_id == task.id).first()
        if tag:
            tag.text = tag_form
        else:
            new_tag = Tag(task_id=id, text=tag_form)
            db.add(new_tag)
    if deadline == "":
        deadline = None
    else:
        deadline = datetime.strptime(deadline, "%Y-%m-%d")

    task.date_deadline = deadline
    task.text = text
    flash(request, "Задача отредактирована", category="alert alert-success")

    tg_users = get_participants_tg_id(db, task.board, current_user)
    send_notification(tg_users, task_updated_message, task.board.name, task.b_column.name)

    db.commit()

    return templates.TemplateResponse("edit_task.html", {"request": request, "task": task})


@router.get("/add_collaborator/{board_id}")
def add_collaborator(board_id: int, request: Request, current_user: User = Depends(manager),
                     db: Session = Depends(get_db)):
    """Отрисовка страницы добавления нового участника"""
    board = db.query(Board).filter(Board.id == board_id).first()
    participants_id = [collab.user_id for collab in board.collaborators]
    participants_id.append(board.author_id)
    if current_user.id not in participants_id:
        return templates.TemplateResponse("no_board.html", {"request": request})
    return templates.TemplateResponse("add_collaborator.html",
                                      {"request": request, "board": board, "user": current_user})


@router.post("/add_collaborator/{board_id}")
def add_collaborator(board_id: int, request: Request, current_user: User = Depends(manager),
                     db: Session = Depends(get_db),
                     collaborator: Collaborator = Depends(CollaboratorForm)):
    """Добавление нового участника в доску. Валидация данных пользователя"""
    board = db.query(Board).filter(Board.id == board_id).first()
    if current_user.id != board.author_id:
        return templates.TemplateResponse("no_board.html", {"request": request})
    user = db.query(User).filter(User.username == collaborator.username).first()
    if not user:
        flash(request, "Такого пользователя нет", category="alert alert-danger")
    elif any([user.id == collab.user_id for collab in board.collaborators]):
        flash(request, "Этот пользователь уже является участником", category="alert alert-danger")
    else:
        flash(request, "Пользователь успешно добавлен", category="alert alert-success")
        new_collaborator = Collaborator(board_id=board.id, user_id=user.id)
        tg_user = db.query(TgUser).where(TgUser.user_id == new_collaborator.user_id).first()
        if tg_user:
            tg_user_id = tg_user.tg_id
            as_collaborator_added_message(tg_user_id, board.name)
            db.add(new_collaborator)
            db.commit()

        tg_users = get_participants_tg_id(db, board, current_user)
        for tg_user in tg_users:
            collaborator_added_message(tg_user.tg_id, board.name, new_collaborator.user.username)
    return templates.TemplateResponse("add_collaborator.html",
                                      {"request": request, "board": board, "user": current_user})


@router.get("/delete_collaborator/{board_id}/{collaborator_id}")
def delete_collaborator(board_id: int, collaborator_id: int, request: Request, current_user: User = Depends(manager),
                        db: Session = Depends(get_db)):
    """Удаление участника с доски"""
    board = db.query(Board).filter(Board.id == board_id).first()
    if current_user.id != board.author_id:
        return templates.TemplateResponse("no_board.html", {"request": request})
    collaborator = db.query(Collaborator).filter(
        Collaborator.user_id == collaborator_id and Collaborator.board_id == board_id).first()
    if not collaborator:
        flash(request, "Такого пользователя нет", category="alert alert-danger")
    else:
        flash(request, "Пользователь успешно удален", category="alert alert-success")

        tg_users = get_participants_tg_id(db, board, current_user)
        for tg_user in tg_users:
            collaborator_deleted_message(tg_user.tg_id, board.name, collaborator.user.username)

        db.delete(collaborator)
        db.commit()
    return templates.TemplateResponse("add_collaborator.html",
                                      {"request": request, "board": board, "user": current_user})


@router.post("/find_board")
async def find_board(request: Request, current_user: User = Depends(manager), db: Session = Depends(get_db)):
    """Поиск доски с помощью Ajax-запроса"""
    name = (await request.form()).get('name')
    board = db.query(Board).filter(
        Board.name == name and (Board.is_private is True or Board.author_id == current_user.id)).first()
    if board:
        answer = {"result": '<a href=' + f'/board/{board.id}' + '> Найденная доска<a>'}
    else:
        answer = {"result": "Такой доски нет"}

    return json.dumps(answer)


@router.get("/view_themes")
async def view_themes(request: Request, current_user: User = Depends(manager), db: Session = Depends(get_db)):
    """Отрисовка страницы просмотра тем"""
    themes = db.query(Theme).all()
    return templates.TemplateResponse("view_themes.html", {"request": request, "themes": themes})


@router.get("/add_theme")
async def add_theme(request: Request, current_user: User = Depends(manager)):
    """Отрисовки шаблона добавления тем"""
    return templates.TemplateResponse("add_theme.html", {"request": request})


@router.post("/add_theme")
async def add_theme(request: Request, theme_form: ThemeForm = Depends(ThemeForm), current_user: User = Depends(manager),
                    db: Session = Depends(get_db)):
    """Добавление темы. Валидация на наличие темы"""
    theme = db.query(Theme).filter(Theme.name == theme_form.name).first()

    if theme:
        flash(request, "Такая тема уже существует", category="alert alert-danger")
        return templates.TemplateResponse("add_theme.html", {"request": request})

    flash(request, "Тема успешно создана", category="alert alert-success")
    new_theme = Theme(name=theme_form.name, description=theme_form.description)
    db.add(new_theme)
    db.commit()

    return RedirectResponse(url="/view_themes", status_code=status.HTTP_302_FOUND)


@router.get("/edit_theme/{theme_id}")
async def edit_theme(theme_id: int, request: Request, current_user: User = Depends(manager),
                     db: Session = Depends(get_db)):
    """Отрисовка шаблона редактирования темы"""
    theme = db.query(Theme).filter(Theme.id == theme_id).first()

    if not theme:
        return templates.TemplateResponse("no_board.html", {"request": request})

    return templates.TemplateResponse("edit_theme.html", {"request": request, "theme": theme})


@router.post("/edit_theme/{theme_id}")
async def edit_theme(theme_id: int, request: Request, theme_form: ThemeForm = Depends(ThemeForm),
                     current_user: User = Depends(manager), db: Session = Depends(get_db)):
    """Редактирование темы. Валидация данных"""
    theme = db.query(Theme).filter(Theme.id == theme_id).first()

    if not theme:
        return templates.TemplateResponse("no_board.html", {"request": request})

    flash(request, "Тема успешно отредактирована", category="alert alert-success")
    theme.name = theme_form.name
    theme.description = theme_form.description
    db.commit()

    return templates.TemplateResponse("edit_theme.html", {"request": request, "theme": theme})


def change_task_column(db: Session, task_id: int, col_id_new: int):
    """Изменение колонки у задачи для перетаскивания задач с помощью мыши"""
    task = db.query(Task).filter(Task.id == task_id).first()
    task.column_id = col_id_new
    db.commit()


def get_participants_tg_id(db: Session, board: Board, current_user: User):
    """Получение tg_id всех участников доски"""
    collaborators_id = set([collab.user_id for collab in board.collaborators])
    collaborators_id.add(current_user.id)
    tg_users = db.query(TgUser).where(TgUser.user_id.in_(collaborators_id) & TgUser.is_subscribed == True).all()
    return tg_users


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, db: Session = Depends(get_db)):
    """Получение данных о перемещении задач с помощью веб-сокета"""
    await connection_manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            task, col = data.split()
            task_id = int(task[task.rfind("-") + 1:])
            col_id = int(col[col.rfind("-") + 1:])
            change_task_column(db, task_id, col_id)
    except WebSocketDisconnect:
        connection_manager.disconnect(websocket)
