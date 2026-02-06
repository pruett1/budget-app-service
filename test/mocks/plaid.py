class MockPlaid:
    async def create_link_token(self, user_id: str) -> str:
        print("MockPlaid: create_link_token called with user_id:", user_id)
        return "mock_link_token"
    
    async def exchange_public_token(self, public_token: str) -> tuple[str, str]:
        print("MockPlaid: exchange_public_token called with public_token:", public_token)
        return ("mock_access_token", "mock_item_id")