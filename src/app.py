from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager

import re

from src.helpers.logger import config_logger, get_struct_logger, request_id_ctx

from src.db.account_db import AccountDB
from src.db.item_db import ItemDB
from src.helpers.sessions import SessionManager
from src.helpers.plaid.client import Plaid

from src.routers import account, linked_plaid

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

@app.middleware("http")
async def add_request_id(request: Request, call_next):
    request_id = request.headers.get('request-id')

    if not request_id or not re.match(r'^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$', request_id):
        return JSONResponse(status_code=400, content={"error": "Missing or invalid request-id header (must be UUIDv4)"})

    request_id_ctx.set(request_id)

    response = await call_next(request)
    response.headers["request-id"] = request_id # echo back request id
    return response

@app.get('/ping')
async def ping():
    return {"message": "pong"}

app.include_router(account.router, prefix="/account")
app.include_router(linked_plaid.router, prefix="/plaid")