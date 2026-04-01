from contextlib import asynccontextmanager
from fastapi import FastAPI

from .routes import drug, locker, detect, log
from .utils import db


@asynccontextmanager
async def lifespan(app: FastAPI):
    await db.connect_db()
    yield
    await db.close_db()


app = FastAPI(lifespan=lifespan)

app.include_router(drug.router)
app.include_router(locker.router)
app.include_router(detect.router)
app.include_router(log.router)
