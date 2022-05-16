from fastapi import APIRouter, Depends, UploadFile
from starlette.requests import Request
from csv import DictReader

from . import oauth, templates, flash
from .auth import manager
from ..database import get_db
from ..models import Board, BColumn, Task

router = APIRouter(tags=["auth"])


@router.post("/import/{board_id}")
async def import_board(board_id: int, request: Request, file: UploadFile, user=Depends(manager), db=Depends(get_db)):
    with open("file_to_import.csv", "w", encoding="UTF-8") as import_file:
        import_file.write((await file.read()).decode("UTF-8"))
    with open("file_to_import.csv", "r", encoding="UTF-8") as import_file:
        reader = DictReader(import_file)
        headers = reader.fieldnames
        col_links = {}
        for col_name in headers:
            column = BColumn(name=col_name, board_id=board_id, color_id=1)
            db.add(column)
            col_links[col_name] = column
        for row in reader:
            row = dict(row)
            for col_name in row:
                if row.get(col_name):
                    task = Task(text=row.get(col_name), column_id=col_links[col_name].id, author_id=user.id)
                    db.add(task)
        db.commit()
        flash(request, "Задачи добавлены", category="alert alert-success")
        return templates.TemplateResponse("export_import.html", {"request": request})


@router.get("/import/{board_id}")
def import_board(board_id: int, request: Request, user=Depends(manager), db=Depends(get_db)):
    board = db.query(Board).filter(Board.id == board_id).first()
    can_edit = board.author.id == user.id or any([user.id == collab.user_id for collab in board.collaborators])
    if not can_edit:
        return templates.TemplateResponse("no_board.html", {"request": request})
    return templates.TemplateResponse("export_import.html", {"request": request, "board": board})
