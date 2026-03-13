from src.db.mongo import DB
from datetime import datetime, UTC
from src.helpers.encryption import encrypt, decrypt

class ItemDB:
    def __init__(self, env: str, logger, db_factory = DB):
        self.collection = db_factory(env).get_db().items
        self.logger = logger
        self.logger.info("ItemDB initialized.")

    def insert(self, user_id: str) -> None:
        if not user_id or not isinstance(user_id, str):
            raise ValueError("Invalid user_id provided for insertion.")

        self.logger.debug("Inserting new item...")
        try:
            self.collection.insert_one({"user_id": user_id, "items": []})
        except Exception as e:
            self.logger.error("Failed to insert new item: %s", e)
            raise

    def append_item(self, user_id: str, item_id: str, access_token: str, data: dict|None = None) -> None:
        if not user_id or not item_id or not access_token or not isinstance(user_id, str) or not isinstance(item_id, str) or not isinstance(access_token, str):
            raise ValueError("Invalid user_id, item_id, or access_token provided for appending item")
        
        if not self.collection.find_one({"user_id": user_id}):
            raise ValueError("User_id not found")

        if self.collection.find_one({"user_id": user_id, "items": {"$elemMatch": {"item_id": item_id}}}):
            raise ValueError("Item already exists")

        try:
            self.collection.update_one({"user_id": user_id}, 
                                   {"$push": 
                                        {"items": 
                                            {
                                                "item_id": item_id, 
                                                "access_token": encrypt(access_token),
                                                "last_updatated": None,  
                                                "item_data": data
                                            }
                                        }
                                    })
        except Exception as e:
            self.logger.error("Failed to append item: %s", e)
            raise
        
    def get_items(self, user_id: str) -> list:
        if not user_id or not isinstance(user_id, str):
            raise ValueError("Invalid user_id provided for retrieving items")

        self.logger.debug("Retrieving items for user_id: %s", user_id)
        record = self.collection.find_one({"user_id": user_id})
        if record:
            return record.get("items")
        else:
            self.logger.warning("No user found")
            return []
        
    def get_item(self, user_id: str, item_id: str):
        if not user_id or not isinstance(user_id, str):
            raise ValueError("Invalid user_id provided for retrieving item")
        if not item_id or not isinstance(item_id, str):
            raise ValueError("Invalid item_id provided for retrieving item")
        
        self.logger.debug(f"Retrieving item {item_id} for user: {user_id}")
        record = self.collection.find_one({"user_id": user_id})
        if record and "items" in record:
            for item in record["items"]:
                if item.get("item_id") == item_id:
                    return item
            self.logger.warning("Item not found")
            return None
        else:
            self.logger.warning("User not found")
            return None

        
    def remove_item(self, user_id: str, item_id: str) -> None:
        if not user_id or not item_id or not isinstance(user_id, str) or not isinstance(item_id, str):
            raise ValueError("Invalid user_id or item_id provided for removing item")

        self.logger.debug("Removing item_id: %s from user_id: %s", item_id, user_id)
        try:
            self.collection.update_one({"user_id": user_id}, {"$pull": {"items": {"item_id": item_id}}})
        except Exception as e:
            self.logger.error("Failed to remove item: %s", e)
            raise
        
    def update_item_field(self, user_id: str, item_id: str, field: str, new_value: str|dict) -> None:
        if not user_id or not item_id or not field or not new_value or not isinstance(user_id, str) or not isinstance(item_id, str) or not isinstance(field, str) or not isinstance(new_value, (str, dict)):
            self.logger.error("Invalid input provided for updating item field", user_id=user_id, item_id=item_id, field=field, new_value=new_value)
            raise ValueError("Invalid user_id, item_id, or new_access_token provided for updating access token")

        self.logger.debug("Updating %s for item_id: %s of user_id: %s", field, item_id, user_id)

        if field == "access_token":
            if not isinstance(new_value, str):
                self.logger.error("New access token must be a string", new_value=new_value)
                raise ValueError("New access token must be a string")
            new_value = encrypt(new_value)

        try:
            self.collection.update_one(
                {"user_id": user_id, "items.item_id": item_id},
                {"$set": {f"items.$.{field}": new_value}}
            )
        except Exception as e:
            self.logger.error("Failed to update access token: %s", e)
            raise

        self.collection.update_one(
            {"user_id": user_id, "items.item_id": item_id},
            {"$set": {"items.$.last_updated": datetime.now(UTC).isoformat()}}
        )

    def close(self):
        self.collection.database.client.close()