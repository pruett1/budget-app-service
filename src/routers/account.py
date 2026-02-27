from fastapi import APIRouter, Depends, Request, Response, status
from urllib3 import request

from src.helpers.dependencies import get_account_db, get_item_db, get_session_manager, get_logger, get_plaid_client
from src.helpers.encryption import pwd_hash, encrypt, decrypt
from src.requests.bodies import createAccountRequest, loginRequest, exchangePublicTokenRequest

import uuid
import re

router = APIRouter()

@router.post('/create')
async def create_account(request: createAccountRequest, response: Response, 
                         account_db = Depends(get_account_db), item_db = Depends(get_item_db),
                         logger = Depends(get_logger)):
    
    if account_db.find_by_field("user", request.username):
        response.status_code = status.HTTP_400_BAD_REQUEST
        logger.warning("Username already exists: %s", request.username)
        return "Username already exists"
    if request.email and not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', request.email.strip()):
        response.status_code = status.HTTP_400_BAD_REQUEST
        logger.warning("Invalid email format: %s", request.email)
        return "Invalid email format"
    if account_db.find_by_field("email", request.email):
        response.status_code = status.HTTP_400_BAD_REQUEST
        logger.warning("Email already exists: %s", request.email)
        return "Email already exists"

    account_data = {"user": request.username, "user_id": str(uuid.uuid4()), "email": request.email, "password": pwd_hash(request.password)}
    account_db.insert(account_data)
    item_db.insert(account_data['user_id'])
    logger.info("Successfully created account for user: %s", request.username)
    return "Account created successfully"

@router.post('/login')
async def login(request: loginRequest, response: Response, account_db = Depends(get_account_db), 
                session_manager = Depends(get_session_manager), plaid = Depends(get_plaid_client)):
    account = account_db.validate_credentials(request.username, pwd_hash(request.password))

    if account:
        try:
            link_token = await plaid.create_link_token(account['user_id'])
            return {"jwt_token": session_manager.create(account['user_id']), "link_token": link_token}
        except Exception as e:
            response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
            return "Failed to create link token"
    else:
        response.status_code = status.HTTP_401_UNAUTHORIZED
        return "Invalid credentials"
    
@router.post('/exchange_public_token')
async def exchange_public_token(request: exchangePublicTokenRequest, response: Response,
                                session_manager = Depends(get_session_manager),
                                item_db = Depends(get_item_db),
                                plaid = Depends(get_plaid_client),
                                logger = Depends(get_logger)):
    try:
        user_id = session_manager.validate(request.jwt_token)
    except ValueError:
        response.status_code = status.HTTP_401_UNAUTHORIZED
        return "Invalid or expired session token"
    
    try:
        access_token, item_id = await plaid.items.exchange_public_token(request.public_token)
        item_data = await plaid.items.get(access_token)
        item_products = item_data['item']['products']
        item_consented_products = item_data['item']['consented_products']
        item_data = {"products": item_products, "consented_products": item_consented_products}

        try:
            item_db.append_item(user_id, encrypt(item_id), encrypt(access_token), data=item_data)
            response.status_code = status.HTTP_204_NO_CONTENT
        except ValueError:
            response.status_code = status.HTTP_400_BAD_REQUEST
            return "Item already exists for user"
    except Exception as e:
        logger.error("Error exchanging public token: %s", str(e))
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return "Failed to exchange public token"


@router.get('/logout')
async def logout(request: Request, response: Response, session_manager = Depends(get_session_manager)):
    session_token = request.headers.get('Authorization')[7:]  # Remove "Bearer " prefix
    session_manager.invalidate(session_token)
    response.status_code = status.HTTP_204_NO_CONTENT