from main.db.mongo import DB
from main.src.models.account import Account

class AccountDB:
    def __init__(self, env: str):
        self.collection = DB(env).get_db().accounts

    def insert(self, id: str, account_data: str):
        print(f"Inserting account with id: {id} and data: {account_data}")
        account_record = {"test_id": id, "data": account_data}
        print(f"Account record to insert: {account_record}")
        self.collection.insert_one(account_record)
        print("Insertion complete.")

    def find_by_id(self, id: str):
        entry = self.collection.find_one({"test_id": id})
        del entry['_id']
        return entry
    
    def update_account(self, id: str, account_data: str):
        self.collection.update_one({"test_id": id}, {"$set": {"data": account_data}})
        return "Account updated successfully"