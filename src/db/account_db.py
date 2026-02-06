from src.db.mongo import DB
from logging import Logger

class AccountDB:
    def __init__(self, env: str, logger: Logger, db_factory = DB):
        self.collection = db_factory(env).get_db().accounts
        self.logger = logger
        self.logger.info("AccountDB initialized.")

    def insert(self, account_data: dict):
        if account_data is None or not isinstance(account_data, dict):
            raise ValueError("Invalid account data provided for insertion.")
        
        self.logger.info("Inserting new account...")
        self.collection.insert_one(account_data)
        self.logger.info("Insertion complete.")

    def find_by_field(self, field: str, val: str):
        if not field or not val or not isinstance(field, str) or not isinstance(val, str):
            raise ValueError("Invalid field or value provided for search.")

        entry = self.collection.find_one({field: val})
        if not entry:
            return None
        del entry['_id']
        del entry['password']
        return entry

    def validate_credentials(self, username: str, password: str) -> dict | None:
        if not username or not password or not isinstance(username, str) or not isinstance(password, str):
            raise ValueError("Invalid username or password provided for validation.")

        account = self.collection.find_one({"user": username})
        if account and account['password'] == password:
            del account['_id']
            del account['password']
            return account
        return None
    
    def close(self):
        self.collection.database.client.close()