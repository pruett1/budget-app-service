class MockAccountDB:
    def __init__(self):
        self.accounts = [] # list of account dicts
        
    def find_by_field(self, field, value):
        print(f"Searching for account with {field}={value} in MockAccountDB with accounts: {self.accounts}")
        for account in self.accounts:
            if account.get(field) == value:
                return account
        return None
    
    def insert(self, account: dict):
        print("Inserting account into MockAccountDB:", account)
        self.accounts.append(account)

    def validate_credentials(self, username: str, password: str) -> dict | None:
        for account in self.accounts:
            if account['user'] == username and account['password'] == password:
                return account
        return None
    
    def clear(self):
        self.accounts = []

class MockItemDB:
    def __init__(self):
        self.items = {} # dict mapping user_id to list of items

    def insert(self, user_id: str):
        print("Inserting user_id into MockItemDB:", user_id)
        if user_id not in self.items:
            self.items[user_id] = []

    def append_item(self, user_id: str, item_id: str, access_token: str, data: dict|None = None):
        if user_id not in self.items:
            self.items[user_id] = []
        for item in self.items[user_id]:
            if item['item_id'] == item_id:
                raise ValueError("Item already exists for user")
        self.items[user_id].append({'item_id': item_id, 'access_token': access_token, 'item_data': data})

    def clear(self):
        self.items = {}