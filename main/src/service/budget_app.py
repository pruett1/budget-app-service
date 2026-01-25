from fastapi import FastAPI, APIRouter
from contextlib import asynccontextmanager
from main.db.account_db import AccountDB
from pydantic import BaseModel
from main.src.service.routers import account
from main.src.service.helpers.sessions import SessionManager

@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.sessionManager = SessionManager()
    app.state.accountDB = AccountDB("sandbox")
    yield
    app.state.accountDB.close()

app = FastAPI(lifespan=lifespan)

@app.get('/ping')
async def ping():
    return "pong"

app.include_router(account.router, prefix="/account")