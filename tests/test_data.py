TEST_USER1_SIGNUP = {
    "email": "test@mail.ru",
    "username": "TestUser1",
    "password1": "LonGPassword12",
    "password2": "LonGPassword12",
}

TEST_USER1_AUTH = {"username": "TestUser1", "password": "LonGPassword12"}

TEST_USER1_SIGNUP_CHANGED_EMAIL = {
    "email": "test1@mail.ru",
    "username": "TestUser1",
    "password1": "LonGPassword12",
    "password2": "LonGPassword12",
}

TEST_USER2_NOT_MATCH_PASSWORD = {
    "email": "test1@mail.ru",
    "username": "TestUser2",
    "password1": "LonGPassword1212",
    "password2": "LonGPassword12",
}

TEST_USER2_SHORT_USERNAME = {
    "email": "test1@mail.ru",
    "username": "T",
    "password1": "LonGPassword12",
    "password2": "LonGPassword12",
}

TEST_USER2_SHORT_PASSWORD = {
    "email": "test1@mail.ru",
    "username": "TestUser2",
    "password1": "L12",
    "password2": "L12",
}

TEST_USER2_SHORT_EMAIL = {
    "email": ".ru",
    "username": "TestUser2",
    "password1": "LonGPassword12",
    "password2": "LonGPassword12",
}

TEST_USER2_SIGNUP = {
    "email": "test1@mail.ru",
    "username": "TestUser2",
    "password1": "LonGPassword12",
    "password2": "LonGPassword12",
}

TEST_USER2_AUTH = {"username": "TestUser2", "password": "LonGPassword12"}

EDIT_USER1_NOT_MATCH_PASSWORD = {
    "email": "test1@mail.ru",
    "username": "TestUser2",
    "password1": "LonGPassword121",
    "password2": "LonGPassword12",
}

TEST_USER3_SIGNUP = {
    "email": "test2@mail.ru",
    "username": "TestUser3",
    "password1": "LonGPassword12",
    "password2": "LonGPassword12",
}

EDIT_USER_EMAIL_IN_USE = {
    "email": "test2@mail.ru",
    "username": "TestUser4",
    "password1": "LonGPassword12",
    "password2": "LonGPassword12",
}

EDIT_USER_USERNAME_IN_USE = {
    "email": "test1@mail.ru",
    "username": "TestUser3",
    "password1": "LonGPassword12",
    "password2": "LonGPassword12",
}

EDIT_USER_USERNAME_SHORT = {
    "email": "test1@mail.ru",
    "username": "Tes",
    "password1": "LonGPassword12",
    "password2": "LonGPassword12",
}

EDIT_USER_PASSWORD_SHORT = {
    "email": "test1@mail.ru",
    "username": "TestUser2",
    "password1": "Lon",
    "password2": "Lon",
}

EDIT_USER_EMAIL_INCORRECT = {
    "email": "te",
    "username": "TestUser2",
    "password1": "LonGPassword12",
    "password2": "LonGPassword12",
}

EDIT_USER1 = {
    "email": "test1@mail.ru",
    "username": "TestUser2",
    "password1": "LonGPassword12",
    "password2": "LonGPassword12",
}

TEST_BOARD1 = {"name": "TestBoard", "is_private": False, "theme_id": 1}
