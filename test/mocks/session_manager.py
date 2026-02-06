class MockSessionManager:
    def create(self, user_id: str) -> str:
        return user_id + ":mock_session_token"
    
    def validate(self, session_token: str) -> str:
        if session_token.endswith(":mock_session_token"):
            return session_token.split(":")[0]
        else:
            raise ValueError("Invalid session token")
        
    def invalidate(self, session_id: str):
        pass