from pydantic import BaseModel

class createAccountRequest(BaseModel):
    username: str
    email: str
    password: str

class loginRequest(BaseModel):
    username: str
    password: str