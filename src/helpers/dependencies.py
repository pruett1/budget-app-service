from fastapi import Request

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