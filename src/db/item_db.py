from src.db.mongo import DB
from logging import Logger

class ItemDB:
    def __init__(self, env: str, logger: Logger, db_factory = DB):
        self.collection = db_factory(env).get_db().items
        self.logger = logger
        self.logger.info("ItemDB initialized.")

    def insert(self, user_id: str) -> None:
        self.logger.info("Inserting new account...")
        try:
            self.collection.insert_one({"user_id": user_id, "items": []})
        except Exception as e:
            self.logger.error("Failed to insert new account: %s", e)
            raise

    def append_item(self, user_id: str, item_id: str, access_token: str) -> None:
        if self.collection.find_one({"user_id": user_id, "items": {"$elemMatch": {"item_id": item_id}}}):
            self.logger.warning("Item already exists for user_id")
            raise ValueError("Item already exists")

        self.logger.info("Appending new item to user_id: %s", user_id)
        try:
            self.collection.update_one({"user_id": user_id}, 
                                   {"$push": {"items": {"item_id": item_id, "access_token": access_token}}})
        except Exception as e:
            self.logger.error("Failed to append item: %s", e)
            raise
        
    def get_items(self, user_id: str) -> list:
        self.logger.info("Retrieving items for user_id: %s", user_id)
        record = self.collection.find_one({"user_id": user_id})
        if record:
            return record.get("items")
        else:
            self.logger.error("No user found")
            return []
        
    def remove_item(self, user_id: str, item_id: str) -> None:
        self.logger.info("Removing item_id: %s from user_id: %s", item_id, user_id)
        try:
            self.collection.update_one({"user_id": user_id}, {"$pull": {"items": {"item_id": item_id}}})
        except Exception as e:
            self.logger.error("Failed to remove item: %s", e)
            raise
        
    def update_item_access_token(self, user_id: str, item_id: str, new_access_token: str) -> None:
        self.logger.info("Updating access token for item_id: %s of user_id: %s", item_id, user_id)
        try:
            self.collection.update_one(
                {"user_id": user_id, "items.item_id": item_id},
                {"$set": {"items.$.access_token": new_access_token}}
            )
        except Exception as e:
            self.logger.error("Failed to update access token: %s", e)
            raise

    def close(self):
        self.collection.database.client.close()