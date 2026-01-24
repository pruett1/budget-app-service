from fastapi import FastAPI, APIRouter
from main.db.account_db import AccountDB
from pydantic import BaseModel
from main.src.service.routers import account

app = FastAPI()
accountDB = AccountDB("sandbox")

@app.get('/ping')
async def ping():
    return "pong"

app.include_router(account.router, prefix="/account")