from fastapi import APIRouter, Depends, UploadFile
from starlette.requests import Request
from csv import DictReader, DictWriter

from . import oauth, templates, flash
from .auth import manager
from ..database import get_db
from ..models import Board, BColumn, Task

router = APIRouter(tags=["auth"])


@router.post("/import/{board_id}")
async def import_board(board_id: int, request: Request, file: UploadFile, user=Depends(manager), db=Depends(get_db)):
    board = db.query(Board).filter(Board.id == board_id).first()

    with open("file_to_import.csv", "w", encoding="UTF-8") as import_file:
        import_file.write((await file.read()).decode("UTF-8"))
    with open("file_to_import.csv", "r", encoding="UTF-8") as import_file:
        reader = DictReader(import_file)
        headers = reader.fieldnames
        col_links = {}
        for col_name in headers:
            column = db.query(BColumn).filter(BColumn.name == col_name).first()
            if not column:
                column = BColumn(name=col_name, board_id=board_id, color_id=1)
                db.add(column)
                db.commit()
            col_links[col_name] = column

        for col_name in headers:
            col_links[col_name] = db.query(BColumn).filter(BColumn.name == col_name).first()

        for row in reader:
            row = dict(row)
            for col_name in row:
                if row.get(col_name):
                    task = Task(text=row.get(col_name), column_id=col_links[col_name].id, author_id=user.id,
                                board_id=board_id)
                    db.add(task)
        db.commit()
        flash(request, "Задачи добавлены", category="alert alert-success")
        return templates.TemplateResponse("export_import.html", {"request": request, "board": board})


@router.get("/import/{board_id}")
def import_board(board_id: int, request: Request, user=Depends(manager), db=Depends(get_db)):
    board = db.query(Board).filter(Board.id == board_id).first()
    can_edit = board.author.id == user.id or any([user.id == collab.user_id for collab in board.collaborators])
    if not can_edit:
        return templates.TemplateResponse("no_board.html", {"request": request})
    return templates.TemplateResponse("export_import.html", {"request": request, "board": board})


@router.get("/export/{board_id}")
async def export_board(board_id: int, request: Request, user=Depends(manager), db=Depends(get_db)):
    board = db.query(Board).filter(Board.id == board_id).first()

    with open(f"{board.name}.csv", "w", encoding="UTF-8", newline="") as export_file:
        columns = board.b_columns
        headers = [col.name for col in columns]
        writer = DictWriter(export_file, fieldnames=headers)
        writer.writeheader()
        tasks = [col.tasks for col in columns]
        writer.writerows(zip(tasks[0]))
        # print(tasks, len(columns))
        # task_with_cols = [[] for _ in range(len(columns))]
        # print(task_with_cols)
        # for i, col in enumerate(columns):
        #     print(i)
        #     task_with_cols[i] = []
        #     for task in tasks[i]:
        #         task_with_cols[i].append({col.name: task.text})
        # print(task_with_cols)
        # zipped_tasks = list(zip(task_with_cols))
        # print(zipped_tasks)
        # for row in zipped_tasks:
        #     row = row[0].update(row[1:])
        # writer.writerows(zipped_tasks)
        return "ok"
