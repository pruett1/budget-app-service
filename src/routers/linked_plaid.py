from fastapi import APIRouter, Depends, Response, status

from src.helpers.dependencies import get_item_db, get_logger, get_plaid_client, require_user
from src.helpers.encryption import decrypt
from src.requests.bodies import ExchangePublicTokenRequest, ItemDeleteRequest, ItemUpdateRequest

router = APIRouter()

@router.post('/exchange_public_token')
async def exchange_public_token(request_body: ExchangePublicTokenRequest, response: Response,
                                user_id = Depends(require_user),
                                item_db = Depends(get_item_db),
                                plaid = Depends(get_plaid_client),
                                logger = Depends(get_logger)):
    logger.debug("Plaid Public Token Exchange", path='/exchange_public_token', route='/plaid')
    
    try:
        access_token, item_id = await plaid.items.exchange_public_token(request_body.public_token)
        logger.debug("item_id: %s", item_id, path='/exchange_public_token', route='/plaid')

        item_data = await plaid.items.get(access_token)

        item_products = item_data['item'].get('products')
        item_consented_products = item_data['item'].get('consented_products')
        item_creation_date = item_data['item'].get('created_at')
        institution_name = item_data['item'].get('institution_name')
        item_data = {"products": item_products, "consented_products": item_consented_products,
                     "creation_date": item_creation_date, "institution_name": institution_name}

        try:
            item_db.append_item(user_id, item_id, access_token, data=item_data)
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
async def get_linked_accounts(response: Response, 
                              user_id = Depends(require_user),
                              item_db = Depends(get_item_db), 
                              logger = Depends(get_logger)):
    logger.debug("Getting all linked accounts for user", path='/accounts/get', route='/plaid')
    
    linked_items = item_db.get_items(user_id)

    if len(linked_items) == 0:
        response.status_code = status.HTTP_204_NO_CONTENT
        return linked_items
    
    response_json = []

    for item in linked_items:
        item_data = item['item_data']
        item_data.update( {"id": item['item_id']} )
        response_json.append(item_data)
    
    response.status_code = status.HTTP_200_OK
    return response_json

@router.put('/accounts/delete')
async def delete_linked_account(request_body: ItemDeleteRequest, response: Response, 
                                user_id = Depends(require_user),
                                item_db = Depends(get_item_db),
                                plaid = Depends(get_plaid_client),
                                logger = Depends(get_logger)):
    logger.debug(f"Deleting item for user: {user_id}", path='/accounts/delete', route='/plaid')

    try:
        access_token = item_db.get_item(user_id, request_body.item_id)['access_token']
        access_token = decrypt(access_token)
    except:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return {"error": "Could not find item_id for user"}

    try:
        code = request_body.reason.code if request_body.reason else None
        note = request_body.reason.note if request_body.reason.note else None
        await plaid.items.remove(access_token, code, note)
    except:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return {"error": "Plaid failed to delete item from user"}

    try:
        item_db.remove_item(user_id, request_body.item_id)
        response.status_code = status.HTTP_204_NO_CONTENT
    except:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return {"error": "Failed to delete item from user"}
    
@router.put('/accounts/update')
async def update_account(request_body: ItemUpdateRequest, response: Response,
                         user_id = Depends(require_user),
                         item_db = Depends(get_item_db),
                         plaid = Depends(get_plaid_client),
                         logger = Depends(get_logger)):
    logger.debug(f"Updating items for user: {user_id}", path='/accounts/update', route='/plaid')
    item_id = request_body.item_id

    if not request_body.item_data: #only item_id is passed then cycle access_token
        try:
            access_token = item_db.get_item(user_id, item_id)['access_token']
            access_token = decrypt(access_token)
        except:
            response.status_code = status.HTTP_400_BAD_REQUEST
            return {"error": "Could not find item_id for user"}
        
        try:
            new_access_token = await plaid.items.invalidate_access_token(access_token)
        except:
            response.status_code = status.HTTP_400_BAD_REQUEST
            return {"error": "Failed to invalidate access token"}
        
        try:
            item_db.update_item_field(user_id, item_id, "access_token", new_access_token)
            response.status_code = status.HTTP_204_NO_CONTENT
        except:
            # TODO: might want to consider deleting item from db if fail to update access token
            # no way to recover item without valid access token so...
            # should probably add some retry logic as well
            response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
            return {"error": "Failed to update access token in item db"}

    else: #item_data is passed, update item_data in db with new item_data
        new_item_data = request_body.item_data

        try:
            item_data = item_db.get_item(user_id, item_id)['item_data']
            logger.debug(f"got item_data: {item_data}")
        except:
            response.status_code = status.HTTP_400_BAD_REQUEST
            return {"error": "Could not find item_id for user"}
        
        for k,v in new_item_data:
            logger.debug(f"{k}: {v}, {type(k)}: {type(v)}, {type(item_data)}")
            if k and v:
                item_data[k] = v

        logger.debug(f"updated item_data: {item_data}")

        try:
            item_db.update_item_field(user_id, item_id, "item_data", item_data)
            response.status_code = status.HTTP_204_NO_CONTENT
        except:
            response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
            return {"error": "Failed to update access token in item db"}