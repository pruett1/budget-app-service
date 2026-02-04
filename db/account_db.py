from db.mongo import DB
from logging import Logger

class AccountDB:
    def __init__(self, env: str, logger: Logger):
        self.collection = DB(env).get_db().accounts
        self.logger = logger
        self.logger.info("AccountDB initialized.")

    def insert(self, account_data: str):
        self.logger.info("Inserting new account...")
        self.collection.insert_one(account_data)
        self.logger.info("Insertion complete.")

    def find_by_field(self, field: str, val: str):
        entry = self.collection.find_one({field: val})
        if not entry:
            return None
        del entry['_id']
        del entry['password']
        return entry

    def validate_credentials(self, username: str, password: str) -> dict | None:
        account = self.collection.find_one({"user": username})
        if account and account['password'] == password:
            del account['_id']
            del account['password']
            return account
        return None
    
    def update_account(self, id: str, account_data: str):
        self.collection.update_one({"user_id": id}, {"$set": {"data": account_data}})
        return "Account updated successfully"
    
    def close(self):
        self.collection.database.client.close()