import uvicorn
from fastapi import FastAPI
from starlette.staticfiles import StaticFiles
from starlette.middleware import Middleware
from starlette.middleware.sessions import SessionMiddleware

from website.routers import auth, views, export_import, bot
from website.routers.auth import NotAuthenticatedException, exc_handler
from website import models
from website.database import engine

middleware = [
    Middleware(SessionMiddleware, secret_key='secret-key')
]
app = FastAPI(middleware=middleware)

# Подключение подприложений сайта
app.include_router(auth.router)
app.include_router(views.router)
app.include_router(export_import.router)
app.include_router(bot.router)

# Создание таблиц в базе данных
models.Base.metadata.create_all(engine)

# Подключение папки со статикой и обработка исключений неавторизованного пользователя
app.mount("/website/static", StaticFiles(directory='website/static'), name="static")
app.add_exception_handler(NotAuthenticatedException, exc_handler)

if __name__ == "__main__":
    uvicorn.run(app)
