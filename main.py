import uvicorn
from fastapi import FastAPI
from starlette.staticfiles import StaticFiles
from starlette.middleware import Middleware
from starlette.middleware.sessions import SessionMiddleware

from website.routers import auth, views
from website.routers.auth import NotAuthenticatedException, exc_handler
from website import models
from website.database import engine

middleware = [
    Middleware(SessionMiddleware, secret_key='secret-key')
]
app = FastAPI(middleware=middleware)
app.include_router(auth.router)
app.include_router(views.router)
models.Base.metadata.create_all(engine)
app.mount("/website/static", StaticFiles(directory='website/static'), name="static")
app.add_exception_handler(NotAuthenticatedException, exc_handler)

uvicorn.run(app)
