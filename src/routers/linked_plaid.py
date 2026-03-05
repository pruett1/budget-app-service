from fastapi import APIRouter, Depends, Request, Response, status

from src.helpers.dependencies import get_account_db, get_item_db, get_session_manager, get_logger, get_plaid_client
from src.helpers.encryption import pwd_hash, encrypt, decrypt
from src.requests.bodies import exchangePublicTokenRequest

router = APIRouter()

@router.post('/exchange_public_token')
async def exchange_public_token(request_body: exchangePublicTokenRequest, request: Request, response: Response,
                                session_manager = Depends(get_session_manager),
                                item_db = Depends(get_item_db),
                                plaid = Depends(get_plaid_client),
                                logger = Depends(get_logger)):
    logger.debug("Plaid Public Token Exchange", path='/exchange_public_token', route='/plaid')

    try:
        user_id = session_manager.validate(request.headers.get('Authorization')[7:])
    except ValueError:
        logger.warning("Invalid or expired JWT token tried", path='/exchange_public_token', route='/plaid')
        response.status_code = status.HTTP_401_UNAUTHORIZED
        return {"error": "Invalid or expired session token"}
    
    try:
        access_token, item_id = await plaid.items.exchange_public_token(request_body.public_token)
        item_data = await plaid.items.get(access_token)
        item_products = item_data['item']['products']
        item_consented_products = item_data['item']['consented_products']
        item_creation_date = item_data['item']['created_at']
        institution_name = item_data['item']['institution_name']
        item_data = {"products": item_products, "consented_products": item_consented_products,
                     "creation_date": item_creation_date, "institution_name": institution_name}

        try:
            item_db.append_item(user_id, encrypt(item_id), encrypt(access_token), data=item_data)
            response.status_code = status.HTTP_204_NO_CONTENT
        except ValueError:
            logger.error("Item already exists for user", path='/exchange_public_token', route='/plaid')
            response.status_code = status.HTTP_400_BAD_REQUEST
            return {"error": "Item already exists for user"}
    except Exception as e:
        logger.error(f"Error exchanging public token: {str(e)}", path='/exchange_public_token', route='/plaid')
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return {"error": "Failed to exchange public token"}


@router.get('/accounts/get')
async def get_linked_accounts(request: Request, response: Response, session_manager = Depends(get_session_manager),
                              items_db = Depends(get_item_db), logger = Depends(get_logger)):
    logger.debug("Getting all linked accounts for user", path='/accounts/get', route='/plaid')

    try:
        user_id = session_manager.validate(request.headers.get('Authorization')[7:])
    except ValueError:
        logger.warning("Invalid or expired JWT token tried", path='/accounts/get', route='/plaid')
        response.status_code = status.HTTP_401_UNAUTHORIZED
        return {"error": "Invalid or expired session token"}
    
    linked_items = items_db.get_items(user_id)

    if len(linked_items) == 0:
        response.status_code = status.HTTP_204_NO_CONTENT
        return linked_items
    
    response_json = []

    for item in linked_items:
        response_json.append(item["item_data"].update( {"id": item['item_id']} ))
    
    response.status_code = status.HTTP_200_OK
    return response_json