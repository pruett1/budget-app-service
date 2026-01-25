from fastapi import Request

def get_session_manager(request: Request):
    return request.app.state.sessionManager

def get_account_db(request: Request):
    return request.app.state.accountDB