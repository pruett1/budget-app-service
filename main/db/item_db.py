from main.db.mongo import DB
from logging import Logger

class ItemDB:
    def __init__(self, env: str, logger: Logger):
        self.collection = DB(env).get_db().items
        self.logger = logger
        self.logger.info("ItemDB initialized.")

    def insert(self, user_id: str) -> bool:
        self.logger.info("Inserting new account...")
        try:
            self.collection.insert_one({"user_id": user_id, "items": []})
            return True
        except Exception as e:
            self.logger.error("Failed to insert new account: %s", e)
            return False

    def append_item(self, user_id: str, item_id: str, access_token: str) -> bool:
        self.logger.info("Appending new item to user_id: %s", user_id)
        try:
            self.collection.update_one({"user_id": user_id}, 
                                   {"$push": {"items": {"item_id": item_id, "access_token": access_token}}})
            return True
        except Exception as e:
            self.logger.error("Failed to append item: %s", e)
            return False
        
    def get_items(self, user_id: str) -> list:
        self.logger.info("Retrieving items for user_id: %s", user_id)
        record = self.collection.find_one({"user_id": user_id})
        if record:
            return record.get("items")
        else:
            self.logger.error("No user found")
            return []
        
    def remove_item(self, user_id: str, item_id: str) -> bool:
        self.logger.info("Removing item_id: %s from user_id: %s", item_id, user_id)
        try:
            self.collection.update_one({"user_id": user_id}, {"$pull": {"items": {"item_id": item_id}}})
            return True
        except Exception as e:
            self.logger.error("Failed to remove item: %s", e)
            return False
        
    def update_item_access_token(self, user_id: str, item_id: str, new_access_token: str) -> bool:
        self.logger.info("Updating access token for item_id: %s of user_id: %s", item_id, user_id)
        try:
            self.collection.update_one(
                {"user_id": user_id, "items.item_id": item_id},
                {"$set": {"items.$.access_token": new_access_token}}
            )
            return True
        except Exception as e:
            self.logger.error("Failed to update access token: %s", e)
            return False

    def close(self):
        self.collection.database.client.close()