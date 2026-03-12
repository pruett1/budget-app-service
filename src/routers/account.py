from fastapi import APIRouter, Depends, Request, Response, status

from src.helpers.dependencies import get_account_db, get_item_db, get_session_manager, get_logger, get_plaid_client
from src.helpers.encryption import pwd_hash, encrypt, decrypt
from src.requests.bodies import createAccountRequest, loginRequest

import uuid
import re

router = APIRouter()

@router.post('/create')
async def create_account(request_body: createAccountRequest, request: Request, response: Response, 
                         account_db = Depends(get_account_db), item_db = Depends(get_item_db),
                         logger = Depends(get_logger)):
    logger.debug("Account Create Attempt", path='/create', route='/account')
    
    if account_db.find_by_field("user", request_body.username):
        response.status_code = status.HTTP_400_BAD_REQUEST
        logger.warning("Username already exists", user=request_body.username)
        return {"error": "Username already exists"}
    if request_body.email and not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', request_body.email.strip()):
        response.status_code = status.HTTP_400_BAD_REQUEST
        logger.warning("Invalid email format", email=request_body.email)
        return {"error": "Invalid email format"}
    if account_db.find_by_field("email", request_body.email):
        response.status_code = status.HTTP_400_BAD_REQUEST
        logger.warning("Email already exists", email=request_body.email)
        return {"error": "Email already exists"}

    account_data = {
        "user": request_body.username, 
        "user_id": str(uuid.uuid4()), 
        "email": request_body.email, 
        "password": pwd_hash(request_body.password)
    }
    
    account_db.insert(account_data)
    item_db.insert(account_data['user_id'])
    logger.debug("Successfully created account for user", user=request_body.username)
    return {"message": "Account created successfully"}

@router.post('/login')
async def login(request_body: loginRequest, request: Request, response: Response, 
                account_db = Depends(get_account_db), session_manager = Depends(get_session_manager), 
                plaid = Depends(get_plaid_client), logger = Depends(get_logger)):
    logger.debug("Login Attempt", user=request_body.username, path='/login', route='/account')

    account = account_db.validate_credentials(request_body.username, pwd_hash(request_body.password))

    if account:
        try:
            link_token = await plaid.create_link_token(account['user_id'])
            return {"jwt_token": session_manager.create(account['user_id']), "link_token": link_token}
        except Exception as e:
            logger.error("Exception while creating link token", exception=str(e))
            response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
            return {"error": "Failed to create link token"}
    else:
        response.status_code = status.HTTP_401_UNAUTHORIZED
        return {"error": "Invalid credentials"}

@router.get('/logout')
async def logout(request: Request, response: Response, session_manager = Depends(get_session_manager), logger=Depends(get_logger)):
    logger.debug("Logging Out", path='/logout', route='/account')
    auth = request.headers.get('Authorization')
    if not auth:
        logger.warning("Logout attempted without Authorization header", path='/logout', route='/account')
        response.status_code = status.HTTP_400_BAD_REQUEST
        return {"error": "Missing Authorization header"}
    
    try:
        scheme, session_token = auth.split(' ')
        if scheme.lower() != 'bearer':
            logger.warning("Logout attempted with invalid Authorization header scheme", path='/logout', route='/account')
            response.status_code = status.HTTP_400_BAD_REQUEST
            return {"error": "Invalid Authorization header scheme (must be Bearer)"}
    except ValueError:
        logger.warning("Logout attempted with malformed Authorization header", path='/logout', route='/account')
        response.status_code = status.HTTP_400_BAD_REQUEST
        return {"error": "Malformed Authorization header"}

    session_manager.invalidate(session_token)
    response.status_code = status.HTTP_204_NO_CONTENT