def create_link_token_payload(client_id: str, secret: str, user_id: str) -> dict:
    return {
            "client_id": client_id,
            "secret": secret,
            "client_name": "pruett1-budget-app",
            "user": {
                "client_user_id": user_id
            },
            "products": ["transactions"],
            "additional_consented_products": ["investments", "liabilities"],
            "country_codes": ["US"],
            "language": "en"
        }

def exchange_public_token_payload(client_id: str, secret: str, public_token: str) -> dict:
    return {
        "client_id": client_id,
        "secret": secret,
        "public_token": public_token
    }

def item_payload(client_id: str, secret: str, access_token: str) -> dict:
    return {
        "client_id": client_id,
        "secret": secret,
        "access_token": access_token
    }