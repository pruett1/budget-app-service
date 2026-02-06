from fastapi import FastAPI, APIRouter
from contextlib import asynccontextmanager
import logging

from src.db.account_db import AccountDB
from src.db.item_db import ItemDB
from src.routers import account
from src.helpers.sessions import SessionManager
from src.helpers.plaid import Plaid

@asynccontextmanager
async def lifespan(app: FastAPI): #pragma: no cover
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
    app.state.itemDB.close()
    await app.state.plaid.close()

app = FastAPI(lifespan=lifespan)

@app.get('/ping')
async def ping():
    return "pong"

app.include_router(account.router, prefix="/account")