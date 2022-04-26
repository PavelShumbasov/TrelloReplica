from fastapi import FastAPI
from starlette.staticfiles import StaticFiles
from starlette.middleware import Middleware
from starlette.middleware.sessions import SessionMiddleware

from website.routers import auth
from website import models
from website.database import engine

middleware = [
    Middleware(SessionMiddleware, secret_key='super-secret')
]
app_ = FastAPI(middleware=middleware)
app_.include_router(auth.router)
models.Base.metadata.create_all(engine)
# app_.mount("website/static/", StaticFiles(directory='static', html=True), name="static")
