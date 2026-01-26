from fastapi import APIRouter, Depends, Request, Response, status

from main.src.service.helpers.dependencies import get_account_db, get_session_manager, get_logger
from main.src.service.helpers.encryption import pwd_encrypt
from main.src.service.helpers.request_bodies import createAccountRequest, loginRequest

import uuid
import re

router = APIRouter()

@router.post('/create')
async def create_account(request: createAccountRequest, response: Response, account_db = Depends(get_account_db)):
    if account_db.find_by_field("user", request.username):
        response.status_code = status.HTTP_400_BAD_REQUEST
        return "Username already exists"
    if request.email and not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', request.email.strip()):
        response.status_code = status.HTTP_400_BAD_REQUEST
        return "Invalid email format"
    if account_db.find_by_field("email", request.email):
        response.status_code = status.HTTP_400_BAD_REQUEST
        return "Email already exists"

    account_data = {"user": request.username, "user_id": str(uuid.uuid4()), "email": request.email, "password": pwd_encrypt(request.password)}
    account_db.insert(account_data)
    return {"message": "Account created successfully"}

@router.post('/login')
async def login(request: loginRequest, account_db = Depends(get_account_db), session_manager = Depends(get_session_manager)):
    account = account_db.validate_credentials(request.username, pwd_encrypt(request.password))
    if account:
        return {"token": session_manager.create(account['user_id'])}
    else:
        return "Invalid credentials", 401
    
@router.get('/details')
async def get_account_details(request: Request, response: Response, session_manager = Depends(get_session_manager), account_db = Depends(get_account_db)):
    auth = request.headers.get('Authorization')[7:]  # Remove "Bearer " prefix
    try:
        user_id = session_manager.validate(auth)
    except ValueError:
        response.status_code = status.HTTP_401_UNAUTHORIZED
        return "Invalid or expired session token"
    account = account_db.find_by_field("user_id", user_id)
    return account


@router.get('/logout')
async def logout(session_token: str, session_manager = Depends(get_session_manager)):
    session_manager.invalidate(session_token) 