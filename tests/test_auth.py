from . import app, debug, Base, engine
from fastapi.testclient import TestClient
from .test_data import *


client = TestClient(app, base_url="http://127.0.0.1:8000/")


def sign_up_and_login(test_data_sighup, test_data_auth):
    response = client.post("/sign_up", allow_redirects=True, data=test_data_sighup)
    assert response.status_code == 200
    assert 'User created' in response.text

    response = client.post("/login", allow_redirects=False, data=test_data_auth)
    assert response.status_code == 302


def test_empty_db():
    response = client.get("/")
    assert response.status_code == 200, response.text
    assert "login" in response.text


def test_sign_up_and_login():
    sign_up_and_login(TEST_USER1_SIGNUP, TEST_USER1_AUTH)

    response = client.get("/")
    assert response.status_code == 200
    assert "Поиск доски" in response.text
    assert "Все публичные доски" in response.text
    assert "No boards" in response.text

    response = client.get("/my_boards")
    assert response.status_code == 200
    assert "Мои доски" in response.text


def test_sign_existing():
    response = client.post("/sign_up", data=TEST_USER1_SIGNUP)
    assert response.status_code == 200
    assert 'Email is already in use.' in response.text

    response = client.post("/sign_up", data=TEST_USER1_SIGNUP_CHANGED_EMAIL)
    assert response.status_code == 200
    assert 'Username is already in use.' in response.text

    response = client.post("/sign_up", data=TEST_USER2_NOT_MATCH_PASSWORD)
    assert response.status_code == 200
    assert 'Password do not match!' in response.text

    response = client.post("/sign_up", data=TEST_USER2_SHORT_USERNAME)
    assert response.status_code == 200
    assert 'Username is too short' in response.text

    response = client.post("/sign_up", data=TEST_USER2_SHORT_PASSWORD)
    assert response.status_code == 200
    assert 'Password is too short' in response.text

    response = client.post("/sign_up", data=TEST_USER2_SHORT_PASSWORD)
    assert response.status_code == 200
    assert 'Password is too short' in response.text

    response = client.post("/sign_up", data=TEST_USER2_SHORT_EMAIL)
    assert response.status_code == 200
    assert 'Email is invalid' in response.text

    response = client.post("/sign_up", allow_redirects=True, data=TEST_USER2_SIGNUP)
    assert response.status_code == 200
    assert 'User created' in response.text

    response = client.post("/login", allow_redirects=False, data=TEST_USER2_AUTH)
    assert response.status_code == 200

    response = client.get("/logout", allow_redirects=True)
    assert response.status_code == 200
    assert 'Авторизация' in response.text

    response = client.post("/login", allow_redirects=False, data={'username': 'testuser9999', 'password': '111111'})
    assert response.status_code == 200
    assert 'No such username' in response.text

    response = client.post("/login", allow_redirects=True, data={"username": "TestUser1", "password": "LonGPass"})
    assert response.status_code == 200
    debug(response.text)
    assert 'Incorrect password' in response.text

    response = client.post("/login", allow_redirects=False, data=TEST_USER2_AUTH)
    assert response.status_code == 200

    response = client.get("/")
    assert response.status_code == 200
    assert 'Главная' in response.text