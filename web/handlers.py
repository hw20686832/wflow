#!/usr/bin/env python3
import sys
import os
import json
import configparser
from typing import Optional, Dict, Any
from datetime import datetime

import tornado.web
import tornado.escape
from sqlalchemy.orm import Session

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db_manager import DatabaseManager
from web.auth_service import AuthService


class BaseHandler(tornado.web.RequestHandler):
    def initialize(self, db_manager: DatabaseManager, auth_service: AuthService):
        self.db_manager = db_manager
        self.auth_service = auth_service

    def set_default_headers(self):
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header("Access-Control-Allow-Headers", "x-requested-with, Content-Type, Authorization")
        self.set_header("Access-Control-Allow-Methods", "POST, GET, PUT, DELETE, OPTIONS")

    def options(self):
        self.set_status(204)
        self.finish()

    def get_current_user(self) -> Optional[Dict[str, Any]]:
        auth_header = self.request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return None
        
        token = auth_header[7:]
        user = self.auth_service.get_user_by_token(token)
        if user:
            return user.to_dict()
        return None

    def write_json(self, data: Dict[str, Any], status: int = 200):
        self.set_status(status)
        self.set_header("Content-Type", "application/json")
        self.write(json.dumps(data, ensure_ascii=False, default=str))
        self.finish()

    def write_error(self, status_code: int, **kwargs):
        self.set_header("Content-Type", "application/json")
        if "exc_info" in kwargs:
            exc_info = kwargs["exc_info"]
            error_message = str(exc_info[1]) if exc_info else "Internal server error"
        else:
            error_message = "Internal server error"
        
        self.write_json({
            "error": error_message,
            "status": status_code
        }, status_code)


class AuthHandler(BaseHandler):
    def post(self):
        try:
            data = tornado.escape.json_decode(self.request.body)
            username = data.get('username')
            password = data.get('password')
            
            if not username or not password:
                self.write_json({"error": "Username and password are required"}, 400)
                return
            
            result = self.auth_service.login(username, password)
            if result:
                self.write_json({
                    "message": "Login successful",
                    "token": result['token'],
                    "user": result['user']
                })
            else:
                self.write_json({"error": "Invalid credentials"}, 401)
        except Exception as e:
            self.write_json({"error": str(e)}, 500)


class RegisterHandler(BaseHandler):
    def post(self):
        try:
            data = tornado.escape.json_decode(self.request.body)
            username = data.get('username')
            password = data.get('password')
            email = data.get('email')
            
            if not all([username, password, email]):
                self.write_json({"error": "Username, password and email are required"}, 400)
                return
            
            user = self.auth_service.register(username, password, email)
            if user:
                self.write_json({
                    "message": "Registration successful",
                    "user": user.to_dict()
                }, 201)
            else:
                self.write_json({"error": "Username or email already exists"}, 409)
        except Exception as e:
            self.write_json({"error": str(e)}, 500)


class LogoutHandler(BaseHandler):
    def post(self):
        try:
            auth_header = self.request.headers.get("Authorization")
            if not auth_header or not auth_header.startswith("Bearer "):
                self.write_json({"error": "No token provided"}, 401)
                return
            
            token = auth_header[7:]
            self.auth_service.logout(token)
            self.write_json({"message": "Logout successful"})
        except Exception as e:
            self.write_json({"error": str(e)}, 500)


class UserHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self):
        user = self.get_current_user()
        self.write_json({"user": user})


class HealthHandler(BaseHandler):
    def get(self):
        if self.db_manager.test_connection():
            self.write_json({"status": "healthy", "database": "connected"})
        else:
            self.write_json({"status": "unhealthy", "database": "disconnected"}, 503)
