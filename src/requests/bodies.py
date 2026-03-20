from pydantic import BaseModel

class CreateAccountRequest(BaseModel):
    username: str
    email: str
    password: str

class LoginRequest(BaseModel):
    username: str
    password: str

class ExchangePublicTokenRequest(BaseModel):
    public_token: str

class DeleteReason(BaseModel):
    code: str
    note: str | None = None

class ItemDeleteRequest(BaseModel):
    item_id: str
    reason: DeleteReason | None = None

class ItemDataUpdate(BaseModel):
    products: list[str] | None = None
    consented_products: list[str] | None = None
    institution_name: str | None = None
    nickname: str | None = None

class ItemUpdateRequest(BaseModel):
    item_id: str
    item_data: ItemDataUpdate | None = None