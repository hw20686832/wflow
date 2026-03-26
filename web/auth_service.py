#!/usr/bin/env python3
import sys
import os
from typing import Optional
from datetime import datetime, timedelta

import bcrypt
import jwt
from sqlalchemy.orm import Session

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.models import User, UserSession
from database.db_manager import DatabaseManager
from config.loader import get_config


class AuthService:
    def __init__(self, db_manager: DatabaseManager, config=None):
        self.db_manager = db_manager
        self.config = config or get_config()
        self.secret_key = self.config.get_str('session.secret_key', 'your-secret-key-change-this-in-production')
        self.session_expire_hours = self.config.get_int('session.expire_hours', 24)

    def hash_password(self, password: str) -> str:
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

    def verify_password(self, password: str, hashed_password: str) -> bool:
        return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))

    def generate_token(self, user_id: int) -> str:
        payload = {
            'user_id': user_id,
            'exp': datetime.utcnow() + timedelta(hours=self.session_expire_hours)
        }
        return jwt.encode(payload, self.secret_key, algorithm='HS256')

    def verify_token(self, token: str) -> Optional[dict]:
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=['HS256'])
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None

    def register(self, username: str, password: str, email: str) -> Optional[User]:
        session = self.db_manager.get_session()
        try:
            existing_user = session.query(User).filter(
                (User.username == username) | (User.email == email)
            ).first()
            
            if existing_user:
                return None
            
            hashed_password = self.hash_password(password)
            user = User(
                username=username,
                password=hashed_password,
                email=email
            )
            session.add(user)
            session.commit()
            session.refresh(user)
            return user
        except Exception as e:
            session.rollback()
            print(f"Registration error: {e}")
            return None
        finally:
            session.close()

    def login(self, username: str, password: str) -> Optional[dict]:
        session = self.db_manager.get_session()
        try:
            user = session.query(User).filter(User.username == username).first()
            
            if not user or not user.is_active:
                return None
            
            if not self.verify_password(password, user.password):
                return None
            
            token = self.generate_token(user.id)
            
            user_session = UserSession(
                user_id=user.id,
                session_token=token,
                expires_at=datetime.utcnow() + timedelta(hours=self.session_expire_hours)
            )
            session.add(user_session)
            session.commit()
            
            return {
                'token': token,
                'user': user.to_dict()
            }
        except Exception as e:
            session.rollback()
            print(f"Login error: {e}")
            return None
        finally:
            session.close()

    def logout(self, token: str) -> bool:
        session = self.db_manager.get_session()
        try:
            user_session = session.query(UserSession).filter(
                UserSession.session_token == token
            ).first()
            
            if user_session:
                session.delete(user_session)
                session.commit()
                return True
            return False
        except Exception as e:
            session.rollback()
            print(f"Logout error: {e}")
            return False
        finally:
            session.close()

    def get_user_by_token(self, token: str) -> Optional[User]:
        session = self.db_manager.get_session()
        try:
            payload = self.verify_token(token)
            if not payload:
                return None
            
            user = session.query(User).filter(User.id == payload['user_id']).first()
            return user
        except Exception as e:
            print(f"Get user error: {e}")
            return None
        finally:
            session.close()

    def cleanup_expired_sessions(self):
        session = self.db_manager.get_session()
        try:
            session.query(UserSession).filter(
                UserSession.expires_at < datetime.utcnow()
            ).delete()
            session.commit()
        except Exception as e:
            session.rollback()
            print(f"Cleanup sessions error: {e}")
        finally:
            session.close()
