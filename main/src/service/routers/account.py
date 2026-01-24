from fastapi import APIRouter
from pydantic import BaseModel
from main.db.account_db import AccountDB

router = APIRouter()
account_db = AccountDB("sandbox")

class CreateAccountRequest(BaseModel):
    id: int
    username: str
    email: str
    password: str

@router.post('/create')
async def create_account(request: CreateAccountRequest):
    id = request.id
    account_data = request.username + "," + request.email + "," + request.password
    account_db.insert(str(id), account_data)
    return {"message": "Account created successfully"}

@router.get('/id/{id}')
async def get_account_by_id(id: str):
    account = account_db.find_by_id(id)
    if account:
        return account
    else:
        return {"message": "Account not found"}