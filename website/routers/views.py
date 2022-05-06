from fastapi import APIRouter, Depends
from starlette import status
from starlette.requests import Request
from starlette.responses import RedirectResponse

from . import templates, flash
from .auth import manager
from ..database import get_db
from ..models import Board, User, Theme, Task, BColumn
from ..schemas import BoardForm

router = APIRouter(tags=["views"])


@router.get("/")
def home(request: Request, user=Depends(manager), db=Depends(get_db)):
    return templates.TemplateResponse("home.html", {"request": request})


@router.get("/my_boards")
def my_boards(request: Request, user=Depends(manager), db=Depends(get_db)):
    boards = db.query(Board).filter(Board.author_id == User.id).all()
    return templates.TemplateResponse("my_boards.html", {"request": request, "boards": boards})


@router.get("/add_board")
def add_board(request: Request, user=Depends(manager), db=Depends(get_db)):
    themes = db.query(Theme).all()
    return templates.TemplateResponse("add_board.html", {"request": request, "themes": themes})


@router.post("/add_board")
def add_board(request: Request, user=Depends(manager), db=Depends(get_db), board: BoardForm = Depends(BoardForm)):
    print(request)
    new_board = Board(name=board.name, author=user.id, is_private=(board.is_private == ""), theme=board.theme_id)
    db.add(new_board)
    db.commit()
    return RedirectResponse(url="/my_boards", status_code=status.HTTP_302_FOUND)


@router.get("/board/{id}")
def view_board(id: int, request: Request, current_user=Depends(manager), db=Depends(get_db)):
    board = Board.query.filter_by(id=id).first()
    if board:
        can_delete = board.author == current_user.id

    if not board or (board.author != current_user.id and board.is_private):
        return templates.TemplateResponse("no_board.html",
                                          {"request": request})
    columns = BColumn.query.filter_by(board_id=id).all()
    tasks = Task.query.filter_by(board_id=id).all()
    return templates.TemplateResponse("view_board.html",
                                      {"board": board, "columns": columns, "can_delete": can_delete})


@router.post("/board/{id}")
def view_board(id: int, request: Request, current_user=Depends(manager), db=Depends(get_db)):
    if current_user.id == board.author:
        text = request.form.get("text")
        new_task = Task(text=text, author=current_user.id, board_id=id)
        db.add(new_task)
        db.commit()
