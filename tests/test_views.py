# from . import app, debug
from main import app
from fastapi.testclient import TestClient
from .test_data import *

client = TestClient(app, base_url="http://127.0.0.1:8000/")


def test_board():
    response = client.post("/login", allow_redirects=True, data=TEST_USER2_AUTH)
    assert response.status_code == 200

    response = client.get("/")
    assert response.status_code == 200
    assert "Главная" in response.text

    response = client.get("/my_boards")
    assert response.status_code == 200
    assert "Мои доски" in response.text

    response = client.get("/add_board")
    assert response.status_code == 200
    assert "Добавить новую доску" in response.text

    response = client.post("/add_board", allow_redirects=True, data=TEST_BOARD1)
    assert response.status_code == 200
    assert "Мои доски" in response.text
    assert TEST_BOARD1["name"] in response.text

    index_end = response.text.find(TEST_BOARD1["name"])
    while response.text[index_end] != '"':
        index_end -= 1
    index_start = index_end
    while response.text[index_start] != "/":
        index_start -= 1

    board_id = response.text[index_start + 1 : index_end]

    response = client.get(f"/board/{board_id}")
    assert response.status_code == 200
    assert "Просмотр доски" in response.text, board_id

    response = client.get("/delete_board/191919191919919191919")
    assert response.status_code == 200
    assert "Доска недоступна" in response.text

    response = client.post(
        f"/add_column/{board_id}",
        allow_redirects=True,
        data={"name": "TestColumn123", "color_id": 1},
    )
    assert response.status_code == 200
    assert "TestColumn123" in response.text
    index_start = response.text.find("edit_column/") + len("edit_column/")
    index_end = index_start + 2
    column_id = response.text[index_start:index_end]

    response = client.post(
        f"/add_task/{board_id}/{column_id}",
        allow_redirects=True,
        data={"text": "task1"},
    )
    assert response.status_code == 200
    assert "task1" in response.text
    index_start = response.text.find("edit_task/") + len("edit_task/")
    index_end = index_start + 3
    task_id = response.text[index_start:index_end]

    response = client.get(f"/edit_task/{task_id}")
    assert response.status_code == 200
    assert "Редактирование задания" in response.text

    response = client.post(
        f"/edit_task/{task_id}",
        allow_redirects=True,
        data={"text": "task12", "deadline": "2022-06-22"},
    )
    assert response.status_code == 200
    assert "Задача отредактирована" in response.text

    response = client.get(f"/delete_task/{task_id}")
    assert response.status_code == 200
    assert "task12" not in response.text

    response = client.get(f"/edit_board/{board_id}")
    assert response.status_code == 200
    assert "Редактирование доски" in response.text

    response = client.post(
        f"/edit_board/{board_id}",
        allow_redirects=True,
        data={"name": "board123", "theme_id": 1},
    )
    assert response.status_code == 200
    assert "Доска успешно отредактирована" in response.text

    response = client.get(f"/edit_column/{column_id}")
    assert response.status_code == 200
    assert "Редактирование колонки" in response.text

    response = client.post(
        f"/edit_column/{column_id}",
        allow_redirects=True,
        data={"name": "column123", "color_id": 1},
    )
    assert response.status_code == 200
    assert "Колонка успешно отредактирована" in response.text

    response = client.get(f"/delete_column/{column_id}")
    assert response.status_code == 200
    assert "column123" not in response.text

    response = client.get(f"/add_collaborator/{board_id}")
    assert response.status_code == 200
    assert "Добавить участника" in response.text

    response = client.post(
        f"/add_collaborator/{board_id}",
        allow_redirects=True,
        data={"username": "stUser3123123"},
    )
    assert response.status_code == 200
    assert "Такого пользователя нет" in response.text

    response = client.post(
        f"/add_collaborator/{board_id}",
        allow_redirects=True,
        data={"username": "TestUser3"},
    )
    assert response.status_code == 200
    assert "Пользователь успешно добавлен" in response.text

    response = client.post(
        f"/add_collaborator/{board_id}",
        allow_redirects=True,
        data={"username": "TestUser3"},
    )
    assert response.status_code == 200
    assert "Этот пользователь уже является участником" in response.text

    index_start = (
        response.text.find("delete_collaborator/") + len("delete_collaborator/") + 3
    )
    index_end = index_start + 3
    collaborator_id = response.text[index_start:index_end]

    response = client.get(f"/delete_collaborator/{board_id}/1242142313134")
    assert response.status_code == 200
    assert "Такого пользователя нет" in response.text

    response = client.get(f"/delete_collaborator/{board_id}/{collaborator_id}")
    assert response.status_code == 200
    assert "Пользователь успешно удален" in response.text

    # response = client.post("/find_board", allow_redirects=True, data={"name": "board123"})
    # assert response.status_code == 200
    # assert "Найденная доска" in response.text

    # response = client.post("/find_board", allow_redirects=True, data={"name": "123412341241243122134"})
    # assert response.status_code == 200
    # assert "Такой доски нет" in response.text

    response = client.get(f"/import/{board_id}")
    assert response.status_code == 200
    assert "Экспорт / импорт" in response.text

    response = client.get(f"/delete_board/{board_id}")
    assert response.status_code == 200
    assert "Мои доски" in response.text
    assert "board123" not in response.text


def test_theme():
    response = client.get("/view_themes")
    assert response.status_code == 200
    assert "Просмотр тем" in response.text

    response = client.get("/add_theme")
    assert response.status_code == 200
    assert "Добавление темы" in response.text

    response = client.post(
        "/add_theme",
        allow_redirects=True,
        data={"name": "TestTheme1", "description": "Доски на определенную тему"},
    )
    assert response.status_code == 200
    assert "Тема успешно создана" in response.text

    index_start = response.text.rfind("edit_theme/") + len("edit_theme/")
    index_end = index_start + 2
    theme_id = response.text[index_start:index_end]

    response = client.get(f"/edit_theme/{theme_id}")
    assert response.status_code == 200
    assert "Редактирование темы" in response.text

    response = client.post(
        f"/edit_theme/{theme_id}",
        allow_redirects=True,
        data={"name": "TestTheme1", "description": "Д"},
    )
    assert response.status_code == 200
    assert "Тема успешно отредактирована" in response.text


def test_subscribe():
    response = client.get("/subscribe_on_events")
    assert response.status_code == 200
    assert "Подписаться на обновления" in response.text

    response = client.get("/unsubscribe_from_events")
    assert response.status_code == 200
    assert "Вы отписались от обновлений" in response.text

    response = client.post(
        "/subscribe_on_events", allow_redirects=True, data={"tg_id": 123123123}
    )
    assert response.status_code == 200
    assert "Вы успешно обновили свой аккаунт" in response.text

    response = client.post(
        "/subscribe_on_events", allow_redirects=True, data={"tg_id": 123123134}
    )
    assert response.status_code == 200
    assert "Вы успешно обновили свой аккаунт" in response.text

    response = client.get("/unsubscribe_from_events")
    assert response.status_code == 200
    assert "Вы отписались от обновлений" in response.text


def test_delete_users():
    response = client.get("/delete_test_users")
    assert response.status_code == 200
    assert "OK" in response.text

    response = client.get("/delete_test_users")
    assert response.status_code == 200
    assert "no users" in response.text
