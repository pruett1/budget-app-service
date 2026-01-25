import uuid
import time

class SessionManager:
    def __init__(self):
        self.sessions = {}

    def create(self):
        new_session = str(uuid.uuid4())
        self.sessions[new_session] = time.time() + 3600 # Session valid for 1 hour
        return new_session
    
    def validate(self, session_id: str) -> bool:
        if session_id in self.sessions:
            if time.time() < self.sessions[session_id]:
                return True
            else:
                del self.sessions[session_id] # Session expired, remove it
        return False
    
    def cleanup(self):
        current = time.time()
        expired_sessions = [sid for sid, expiry in self.sessions.items() if expiry < current]
        for sid in expired_sessions:
            del self.sessions[sid]