import json
from datetime import datetime

from fastapi import APIRouter, Depends
from starlette import status
from starlette.requests import Request
from starlette.responses import RedirectResponse

from . import templates, flash
from .auth import manager
from .bot import task_added_message, task_deleted_message, task_updated_message, collaborator_added_message, \
    as_collaborator_added_message, collaborator_deleted_message, col_added_message, col_deleted_message
from ..database import get_db
from ..models import Board, User, Theme, Task, BColumn, Color, Tag, Collaborator, TgUser
from ..schemas import BoardForm, ColumnForm, TaskForm, TaskEditForm, CollaboratorForm

router = APIRouter(tags=["views"])


@router.get("/")
def home(request: Request, user=Depends(manager), db=Depends(get_db)):
    boards = db.query(Board).where((Board.is_private == False)
                                   | ((Board.is_private == True) & (Board.author_id == user.id))).all()
    print(boards)
    return templates.TemplateResponse("home.html", {"request": request, "boards": boards})


@router.get("/my_boards")
def my_boards(request: Request, user=Depends(manager), db=Depends(get_db)):
    boards = db.query(Board).filter(Board.author_id == user.id).all()
    collaborators = db.query(Collaborator).filter(Collaborator.user_id == user.id).all()
    for collab in collaborators:
        boards.append(collab.board)

    return templates.TemplateResponse("my_boards.html", {"request": request, "boards": boards})


@router.get("/add_board")
def add_board(request: Request, user=Depends(manager), db=Depends(get_db)):
    themes = db.query(Theme).all()
    return templates.TemplateResponse("add_board.html", {"request": request, "themes": themes})


@router.post("/add_board")
async def add_board(request: Request, user=Depends(manager), db=Depends(get_db)):
    board = BoardForm(**await request.form())
    new_board = Board(name=board.name, author_id=user.id, is_private=board.is_private, theme_id=board.theme_id)
    db.add(new_board)
    db.commit()
    return RedirectResponse(url="/my_boards", status_code=status.HTTP_302_FOUND)


@router.get("/board/{id}")
def view_board(id: int, request: Request, current_user=Depends(manager), db=Depends(get_db)):
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
def delete_board(id: int, request: Request, current_user=Depends(manager), db=Depends(get_db)):
    board = db.query(Board).filter(Board.id == id).first()
    can_delete = False
    if board:
        can_delete = board.author.id == current_user.id

    if not board or not can_delete:
        return templates.TemplateResponse("no_board.html",
                                          {"request": request})

    db.delete(board)
    db.commit()

    return RedirectResponse(url=f"/my_boards", status_code=status.HTTP_302_FOUND)


@router.post("/add_column/{id}")
def add_column(id: int, request: Request, current_user=Depends(manager), db=Depends(get_db),
               column: ColumnForm = Depends(ColumnForm)):
    new_column = BColumn(name=column.name, color_id=column.color_id, board_id=id)
    db.add(new_column)
    db.commit()

    collaborators_id = set([collab.user_id for collab in new_column.board.collaborators])
    collaborators_id.add(current_user.id)
    tg_users = db.query(TgUser).where(TgUser.user_id.in_(collaborators_id) & TgUser.is_subscribed == True).all()
    for tg_user in tg_users:
        col_added_message(tg_user.id, new_column.board.name, new_column.name)

    return RedirectResponse(url=f"/board/{id}", status_code=status.HTTP_302_FOUND)


@router.get("/delete_column/{column_id}")
def delete_column(column_id: int, request: Request, current_user=Depends(manager), db=Depends(get_db)):
    column = db.query(BColumn).filter(BColumn.id == column_id).first()
    board_id = column.board_id
    can_delete = column.board.author.id == current_user.id or any(
        [current_user.id == collab.user_id for collab in column.board.collaborators])

    if not can_delete:
        return templates.TemplateResponse("no_board.html", {"request": request})
    db.delete(column)
    db.commit()

    collaborators_id = set([collab.user_id for collab in column.board.collaborators])
    collaborators_id.add(current_user.id)
    tg_users = db.query(TgUser).where(TgUser.user_id.in_(collaborators_id) & TgUser.is_subscribed == True).all()
    for tg_user in tg_users:
        col_deleted_message(tg_user.id, column.board.name, column.name)

    return RedirectResponse(url=f"/board/{board_id}", status_code=status.HTTP_302_FOUND)


@router.post("/add_task/{board_id}/{column_id}")
def add_task(board_id: int, column_id: int, request: Request, current_user=Depends(manager), db=Depends(get_db),
             task: TaskForm = Depends(TaskForm)):
    new_task = Task(text=task.text, author_id=current_user.id, board_id=board_id, column_id=column_id)
    db.add(new_task)
    db.commit()
    collaborators_id = set([collab.user_id for collab in new_task.board.collaborators])
    collaborators_id.add(current_user.id)
    tg_users = db.query(TgUser).where(TgUser.user_id.in_(collaborators_id) & TgUser.is_subscribed == True).all()
    # print(tg_users)
    for tg_user in tg_users:
        task_added_message(tg_user.id, new_task.board.name, new_task.b_column.name, new_task.text)
    return RedirectResponse(url=f"/board/{board_id}", status_code=status.HTTP_302_FOUND)


@router.get("/delete_task/{task_id}")
def delete_task(task_id: int, request: Request, current_user=Depends(manager), db=Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id).first()
    board_id = task.board_id
    can_delete = task.board.author.id == current_user.id or any(
        [current_user.id == collab.user_id for collab in task.board.collaborators])
    if not can_delete:
        return templates.TemplateResponse("no_board.html", {"request": request})
    collaborators_id = set([collab.user_id for collab in task.board.collaborators])
    collaborators_id.add(current_user.id)
    tg_users = db.query(TgUser).where(TgUser.user_id.in_(collaborators_id) & TgUser.is_subscribed == True).all()

    for tg_user in tg_users:
        task_deleted_message(tg_user.id, task.board.name, task.b_column.name)
    db.delete(task)
    db.commit()
    return RedirectResponse(url=f"/board/{board_id}", status_code=status.HTTP_302_FOUND)


@router.get("/edit_task/{task_id}")
def edit_task(task_id: int, request: Request, current_user=Depends(manager), db=Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id).first()
    can_delete = task.board.author.id == current_user.id or any(
        [current_user.id == collab.user_id for collab in task.board.collaborators])

    if not can_delete:
        return templates.TemplateResponse("no_board.html", {"request": request})
    return templates.TemplateResponse("edit_task.html", {"request": request, "task": task})


@router.post("/edit_task/{id}")
async def edit_task(id: int, request: Request, current_user=Depends(manager), db=Depends(get_db)):
    task = db.query(Task).filter(Task.id == id).first()
    text = (await request.form()).get("text")
    tag_form = (await request.form()).get("tag", "No tag")
    deadline = (await request.form()).get("deadline")
    if tag_form != "No tag":
        tag = db.query(Tag).filter(Tag.task_id == task.id).first()
        if tag:
            tag.text = tag_form
            print(task.tag)
        else:
            new_tag = Tag(task_id=id, text=tag_form)
            db.add(new_tag)
    if deadline == "":
        deadline = None
    else:
        deadline = datetime.strptime(deadline, "%Y-%m-%d")
    task.date_deadline = deadline

    task.text = text

    collaborators_id = set([collab.user_id for collab in task.board.collaborators])
    collaborators_id.add(current_user.id)
    tg_users = db.query(TgUser).where(TgUser.user_id.in_(collaborators_id) & TgUser.is_subscribed == True).all()
    for tg_user in tg_users:
        task_updated_message(tg_user.id, task.board.name, task.b_column.name)

    db.commit()
    return templates.TemplateResponse("edit_task.html", {"request": request, "task": task})


@router.get("/add_collaborator/{board_id}")
def add_collaborator(board_id: int, request: Request, current_user=Depends(manager), db=Depends(get_db)):
    board = db.query(Board).filter(Board.id == board_id).first()
    if current_user.id != board.author_id:
        return templates.TemplateResponse("no_board.html", {"request": request})
    return templates.TemplateResponse("add_collaborator.html", {"request": request, "board": board})


@router.post("/add_collaborator/{board_id}")
def add_collaborator(board_id: int, request: Request, current_user=Depends(manager), db=Depends(get_db),
                     collaborator=Depends(CollaboratorForm)):
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
        tg_user_id = db.query(TgUser).where(TgUser.user_id == new_collaborator.user_id).first().tg_id
        as_collaborator_added_message(tg_user_id, board.name)
        db.add(new_collaborator)
        db.commit()

    collaborators_id = set([collab.user_id for collab in board.collaborators])
    collaborators_id.add(current_user.id)
    tg_users = db.query(TgUser).where(TgUser.user_id.in_(collaborators_id) & TgUser.is_subscribed == True).all()
    for tg_user in tg_users:
        collaborator_added_message(tg_user.id, board.name, tg_user.user.username)
    return templates.TemplateResponse("add_collaborator.html", {"request": request, "board": board})


@router.get("/delete_collaborator/{board_id}/{collaborator_id}")
def delete_collaborator(board_id: int, collaborator_id: int, request: Request, current_user=Depends(manager),
                        db=Depends(get_db)):
    board = db.query(Board).filter(Board.id == board_id).first()
    if current_user.id != board.author_id:
        return templates.TemplateResponse("no_board.html", {"request": request})
    collaborator = db.query(Collaborator).filter(
        Collaborator.user_id == collaborator_id and Collaborator.board_id == board_id).first()
    if not collaborator:
        flash(request, "Такого пользователя нет", category="alert alert-danger")
    else:
        flash(request, "Пользователь успешно удален", category="alert alert-success")

        collaborators_id = set([collab.user_id for collab in board.collaborators])
        collaborators_id.add(current_user.id)
        tg_users = db.query(TgUser).where(TgUser.user_id.in_(collaborators_id) & TgUser.is_subscribed == True).all()
        for tg_user in tg_users:
            collaborator_deleted_message(tg_user.id, board.name, tg_user.user.username)

        db.delete(collaborator)
        db.commit()
    return templates.TemplateResponse("add_collaborator.html", {"request": request, "board": board})


@router.post("/find_board")
async def find_board(request: Request, db=Depends(get_db), current_user=Depends(manager)):
    name = (await request.form()).get('name')
    board = db.query(Board).filter(
        Board.name == name and (Board.is_private is True or Board.author_id == current_user.id)).first()
    if board:
        answer = {"result": '<a href=' + f'/board/{board.id}' + '> Найденная доска<a>'}
    else:
        answer = {"result": "Такой доски нет"}

    return json.dumps(answer)
