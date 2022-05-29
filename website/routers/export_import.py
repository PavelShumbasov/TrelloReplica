from fastapi import APIRouter, Depends, UploadFile
from sqlalchemy.orm import Session
from starlette.requests import Request
from csv import DictReader, DictWriter

from starlette.responses import FileResponse

from . import templates, flash
from .auth import manager
from .bot import import_to_board_message
from .views import get_participants_tg_id
from ..database import get_db
from ..models import Board, BColumn, Task, User

router = APIRouter(tags=["auth"])

ENCODING = "utf-8-sig"


@router.post("/import/{board_id}")
async def import_board(
    board_id: int,
    request: Request,
    file: UploadFile,
    user: User = Depends(manager),
    db: Session = Depends(get_db),
):
    """Импорт данных в доску из csv файла (Excel)"""
    board = db.query(Board).filter(Board.id == board_id).first()

    # Открываем файл, который пришел по сети и сохраняем его локально
    with open("file_to_import.csv", "w", encoding=ENCODING) as import_file:
        import_file.write((await file.read()).decode(ENCODING))
    # Открываем локально сохраненный файл
    with open("file_to_import.csv", "r", encoding=ENCODING) as import_file:
        reader = DictReader(import_file, delimiter=";")
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
            col_links[col_name] = (
                db.query(BColumn).filter(BColumn.name == col_name).first()
            )

        for row in reader:
            row = dict(row)
            for col_name in row:
                if row.get(col_name):
                    task = (
                        db.query(Task)
                        .filter(
                            (Task.text == row.get(col_name))
                            & (Task.column_id == col_links[col_name].id)
                        )
                        .first()
                    )
                    if not task:
                        task = Task(
                            text=row.get(col_name),
                            column_id=col_links[col_name].id,
                            author_id=user.id,
                            board_id=board_id,
                        )
                        db.add(task)
        db.commit()
        flash(request, "Задачи добавлены", category="alert alert-success")

        tg_users = get_participants_tg_id(db, board, user)
        for tg_user in tg_users:
            import_to_board_message(tg_user.tg_id, board.name, user.username)
        return templates.TemplateResponse(
            "export_import.html", {"request": request, "board": board}
        )


@router.get("/import/{board_id}")
def import_board(
    board_id: int,
    request: Request,
    user: User = Depends(manager),
    db: Session = Depends(get_db),
):
    """Отрисовка страницу для импорта / экспорта доски"""
    board = db.query(Board).filter(Board.id == board_id).first()
    can_edit = board.author.id == user.id or any(
        [user.id == collab.user_id for collab in board.collaborators]
    )
    if not can_edit:
        return templates.TemplateResponse("no_board.html", {"request": request})
    return templates.TemplateResponse(
        "export_import.html", {"request": request, "board": board}
    )


@router.get("/export/{board_id}")
async def export_board(
    board_id: int, request: Request, user=Depends(manager), db=Depends(get_db)
):
    """Получаем файл с нашей доски в формате csv"""
    board = db.query(Board).filter(Board.id == board_id).first()

    with open(
        f"board_to_export.csv", "w", encoding=ENCODING, newline=""
    ) as export_file:
        columns = board.b_columns
        headers = [col.name for col in columns]
        writer = DictWriter(export_file, fieldnames=headers, delimiter=";")
        writer.writeheader()
        tasks = [col.tasks for col in columns]
        max_len = len(max(tasks, key=lambda x: len(x)))

        for i in range(max_len):
            row = {}
            for j, col in enumerate(columns):
                if len(tasks[j]) > i:
                    row[col.name] = tasks[j][i].text

            writer.writerow(row)

    return FileResponse(
        "board_to_export.csv", media_type="file/txt", filename=f"{board.name}.csv"
    )
