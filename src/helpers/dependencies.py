from fastapi import Request, HTTPException, status
from src.helpers.request_context_middleware import request_ctx

def get_session_manager(request: Request):
    return request.app.state.sessionManager

def get_account_db(request: Request):
    return request.app.state.accountDB

def get_item_db(request: Request):
    return request.app.state.itemDB

def get_logger(request: Request):
    return request.app.state.logger

def get_plaid_client(request: Request):
    return request.app.state.plaid

def require_user():
    ctx = request_ctx.get()
    if not ctx or not ctx.user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, 
                            detail={"error": "Protected route requires valid authentication"})
    return ctx.user_id