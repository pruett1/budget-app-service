from fastapi import FastAPI, Depends
from contextlib import asynccontextmanager

from src.helpers.logger import config_logger, get_struct_logger

from src.db.account_db import AccountDB
from src.db.item_db import ItemDB
from src.helpers.sessions import SessionManager
from src.helpers.plaid.client import Plaid

from src.routers import account, linked_plaid

from src.helpers.dependencies import require_user
from src.helpers.request_context_middleware import RequestContextMiddleware

@asynccontextmanager
async def lifespan(app: FastAPI): #pragma: no cover
    config_logger("uvicorn.error", file_name = "app.logs", backup = False)
    logger = get_struct_logger("uvicorn.error")

    logger.info("Initializing application resources...")
    logger.info("Setting up SessionManager and AccountDB...")
    logger.info("Debugging information: Application is starting up.")

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

app.add_middleware(RequestContextMiddleware)

@app.get('/ping')
async def ping():
    return {"message": "pong"}

app.include_router(account.router, prefix="/account")
app.include_router(linked_plaid.router, prefix="/plaid", dependencies=[Depends(require_user)])