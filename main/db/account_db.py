from main.db.mongo import DB
from logging import Logger

class AccountDB:
    def __init__(self, env: str, logger: Logger):
        self.collection = DB(env).get_db().accounts
        self.logger = logger
        self.logger.info("AccountDB initialized.")

    def insert(self, account_data: str):
        self.collection.insert_one(account_data)
        self.logger.info("Insertion complete.")

    def find_by_field(self, field: str, val: str):
        entry = self.collection.find_one({field: val})
        del entry['_id']
        return entry
    
    def update_account(self, id: str, account_data: str):
        self.collection.update_one({"test_id": id}, {"$set": {"data": account_data}})
        return "Account updated successfully"
    
    def close(self):
        self.collection.database.client.close()