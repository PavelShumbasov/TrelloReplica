from fastapi import APIRouter, Depends
from starlette import status
from starlette.requests import Request
from starlette.responses import RedirectResponse

from . import templates, flash
from .auth import manager
from ..database import get_db
from ..models import Board, User, Theme, Task, BColumn, Color, Tag
from ..schemas import BoardForm, ColumnForm, TaskForm, TaskEditForm

router = APIRouter(tags=["views"])


@router.get("/")
def home(request: Request, user=Depends(manager), db=Depends(get_db)):
    boards = db.query(Board).filter(Board.is_private == False).all()
    return templates.TemplateResponse("home.html", {"request": request, "boards": boards})


@router.get("/my_boards")
def my_boards(request: Request, user=Depends(manager), db=Depends(get_db)):
    boards = db.query(Board).filter(Board.author_id == User.id).all()
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
        can_delete = board.author.id == current_user.id

    if not board or (board.author.id != current_user.id and board.is_private):
        return templates.TemplateResponse("no_board.html",
                                          {"request": request})
    # columns = BColumn.query.filter_by(board_id=id).all()
    # tasks = Task.query.filter_by(board_id=id).all()
    colors = db.query(Color).all()
    print(board.b_columns)
    return templates.TemplateResponse("view_board.html",
                                      {"request": request, "board": board, "can_delete": can_delete, "colors": colors})


@router.post("/add_column/{id}")
def add_column(id: int, request: Request, current_user=Depends(manager), db=Depends(get_db),
               column: ColumnForm = Depends(ColumnForm)):
    new_column = BColumn(name=column.name, color_id=column.color_id, board_id=id)
    db.add(new_column)
    db.commit()
    return RedirectResponse(url=f"/board/{id}", status_code=status.HTTP_302_FOUND)


@router.get("/delete_column/{column_id}")
def delete_column(column_id: int, request: Request, current_user=Depends(manager), db=Depends(get_db)):
    column = db.query(BColumn).filter(BColumn.id == column_id).first()
    board_id = column.board_id
    if current_user.id != column.board.author_id:
        return templates.TemplateResponse("no_board.html", {"request": request})
    db.delete(column)
    db.commit()
    return RedirectResponse(url=f"/board/{board_id}", status_code=status.HTTP_302_FOUND)


@router.post("/add_task/{board_id}/{column_id}")
def add_task(board_id: int, column_id: int, request: Request, current_user=Depends(manager), db=Depends(get_db),
             task: TaskForm = Depends(TaskForm)):
    new_task = Task(text=task.text, author_id=current_user.id, board_id=board_id, column_id=column_id)
    db.add(new_task)
    db.commit()
    return RedirectResponse(url=f"/board/{board_id}", status_code=status.HTTP_302_FOUND)


@router.get("/delete_task/{task_id}")
def delete_task(task_id: int, request: Request, current_user=Depends(manager), db=Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id).first()
    board_id = task.board_id
    if current_user.id != task.board.author_id:
        return templates.TemplateResponse("no_board.html", {"request": request})
    db.delete(task)
    db.commit()
    return RedirectResponse(url=f"/board/{board_id}", status_code=status.HTTP_302_FOUND)


@router.get("/edit_task/{task_id}")
def edit_task(task_id: int, request: Request, current_user=Depends(manager), db=Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id).first()
    board_id = task.board_id
    if current_user.id != task.board.author_id:
        return templates.TemplateResponse("no_board.html", {"request": request})
    return templates.TemplateResponse("edit_task.html", {"request": request, "task": task})


@router.post("/edit_task/{id}")
def edit_task(id: int, request: Request, current_user=Depends(manager), db=Depends(get_db),
              task_edited=Depends(TaskEditForm)):
    task = db.query(Task).filter(Task.id == id).first()
    task.date_deadline = task_edited.deadline
    new_tag = Tag(task_id=id, text=task_edited.tag)
    task.text = task_edited.text
    # TODO: исправить добавление тэгов

    db.add(new_tag)
    db.commit()
    return templates.TemplateResponse("edit_task.html", {"request": request, "task": task})
