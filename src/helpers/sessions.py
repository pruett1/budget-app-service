import json
import time
from env.envs import Env
import base64
import hmac
import hashlib
from logging import Logger

class SessionManager:
    def __init__(self, env: str, logger: Logger):
        self.sessions = set()
        config = Env(env)['session']
        self.session_duration = config['DURATION_SECONDS']
        self.secret_key = config['SECRET_KEY']
        self.cleanup_interval = config['CLEANUP_INTERVAL_SECONDS']
        self.header_b64 = base64.urlsafe_b64encode(bytes(str(config['HEADER']), encoding='utf-8')).rstrip(b'=').decode()
        self.alg = config['HEADER']['algorithm']
        self.logger = logger
        self.logger.info("SessionManager initialized")

    def create(self, user_id: str) -> str:
        payload = self.create_payload(user_id)
        signature = hmac.new(self.secret_key.encode(), f"{self.header_b64}.{payload}".encode(), getattr(hashlib, self.alg.lower()) ).hexdigest()
        signature_b64 = base64.urlsafe_b64encode(bytes(signature, encoding='utf-8')).rstrip(b'=').decode()
        session_token = f"{self.header_b64}.{payload}.{signature_b64}"
        self.sessions.add(session_token)
        return session_token

    def create_payload(self, user_id: str) -> str:
        iat = int(time.time())
        exp = iat + self.session_duration
        payload = {"id": user_id, "iat": iat, "exp": exp}
        payload_str = base64.urlsafe_b64encode(bytes(str(payload), encoding='utf-8')).rstrip(b'=').decode()
        return payload_str
    
    def validate(self, session_token: str) -> str:
        self.logger.info("Validating session token")
        # if session_token not in self.sessions:
        #     raise ValueError("Invalid session token")

        try:
            header_b64, payload_b64, signature_b64 = session_token.split('.')
            self.logger.debug("Session token parsed successfully")
        except ValueError:
            self.logger.error("Invalid session token format")
            raise ValueError("Invalid session token format")
        
        expected_sig = hmac.new(self.secret_key.encode(), f"{header_b64}.{payload_b64}".encode(), getattr(hashlib, self.alg.lower()) ).hexdigest()
        expected_sig_b64 = base64.urlsafe_b64encode(bytes(expected_sig, encoding='utf-8')).rstrip(b'=').decode()

        if not hmac.compare_digest(signature_b64, expected_sig_b64):
            self.logger.error("Invalid session token signature")
            raise ValueError("Invalid session token signature")
        
        payload_str = base64.urlsafe_b64decode(payload_b64 + '==').decode().replace("'", '"')
        payload = json.loads(payload_str)

        if payload['exp'] < int(time.time()):
            self.invalidate(session_token)
            self.logger.error("Session token has expired")
            raise ValueError("Session token has expired")
        
        self.logger.info("Valid session token")
        return payload['id']
    
    def invalidate(self, session_id: str):
        self.logger.debug("Invalidating specified session token")
        if session_id in self.sessions:
            self.sessions.remove(session_id)
    
    def cleanup(self):
        current = time.time()
        expired_sessions = []

        for sid in self.sessions:
            try:
                _, payload_b64, _ = sid.split('.')
                payload_str = base64.urlsafe_b64decode(payload_b64 + '==').decode()
                payload = json.loads(payload_str)
                if payload['exp'] < current:
                    expired_sessions.append(sid)
            except:
                expired_sessions.append(sid)

        self.logger.debug(f"Cleaning up {len(expired_sessions)} expired sessions")
        for sid in expired_sessions:
            self.sessions.remove(sid)