from fastapi import FastAPI, APIRouter
from contextlib import asynccontextmanager
import logging

from main.db.account_db import AccountDB
from main.db.item_db import ItemDB
from main.src.routers import account
from main.src.helpers.sessions import SessionManager
from main.src.helpers.plaid import Plaid

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger = logging.getLogger("uvicorn.error")
    logger.setLevel(logging.DEBUG)

    logger.warning("Initializing application resources...")
    logger.info("Setting up SessionManager and AccountDB...")
    logger.debug("Debugging information: Application is starting up.")

    app.state.sessionManager = SessionManager("sandbox", logger)
    app.state.accountDB = AccountDB("sandbox", logger)
    app.state.itemDB = ItemDB("sandbox", logger)
    app.state.plaid = Plaid("sandbox", logger)
    app.state.logger = logger
    yield
    app.state.accountDB.close()

app = FastAPI(lifespan=lifespan)

@app.get('/ping')
async def ping():
    return "pong"

app.include_router(account.router, prefix="/account")