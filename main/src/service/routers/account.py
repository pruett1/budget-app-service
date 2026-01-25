from fastapi import APIRouter, Depends
from pydantic import BaseModel
from main.src.service.helpers.dependencies import get_account_db, get_session_manager
from main.src.service.helpers.encryption import pwd_encrypt

router = APIRouter()
class CreateAccountRequest(BaseModel):
    username: str
    email: str
    password: str

class loginRequest(BaseModel):
    username: str
    password: str

@router.post('/create')
async def create_account(request: CreateAccountRequest, account_db = Depends(get_account_db)):
    account_data = {"user": request.username, "email": request.email, "password": pwd_encrypt(request.password)}
    account_db.insert(account_data)
    return {"message": "Account created successfully"}

@router.post('/login')
async def login(request: loginRequest, account_db = Depends(get_account_db), session_manager = Depends(get_session_manager)):
    account = account_db.find_by_field("user", request.username)
    if account and account['password'] == pwd_encrypt(request.password):
        return session_manager.create()
    else:
        return "Invalid credentials", 401