#!/usr/bin/env python3
import sys
import os
import argparse
from typing import Optional

import pymysql
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.exc import SQLAlchemyError

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.loader import get_config

Base = declarative_base()


class DatabaseManager:
    def __init__(self, config_loader=None):
        self.config = config_loader or get_config()
        self.engine = None
        self.SessionLocal = None

    def get_connection_string(self) -> str:
        return self.config.get_database_url()

    def connect(self):
        try:
            mysql_params = self.config.get_mysql_connection_params()
            self.engine = create_engine(
                self.get_connection_string(),
                pool_pre_ping=True,
                pool_recycle=mysql_params.get('pool_recycle', 3600),
                echo=False
            )
            self.SessionLocal = sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=self.engine
            )
            return True
        except Exception as e:
            print(f"Failed to connect to database: {e}")
            return False

    def init_database(self):
        try:
            schema_file = os.path.join(
                os.path.dirname(__file__), 
                'schema.sql'
            )
            
            if not os.path.exists(schema_file):
                print(f"Schema file not found: {schema_file}")
                return False

            with open(schema_file, 'r', encoding='utf-8') as f:
                schema_sql = f.read()

            with self.engine.connect() as conn:
                conn.execute(text(schema_sql))
                conn.commit()
            
            print("Database schema initialized successfully")
            return True
        except Exception as e:
            print(f"Failed to initialize database: {e}")
            return False

    def test_connection(self) -> bool:
        try:
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return True
        except Exception as e:
            print(f"Database connection test failed: {e}")
            return False

    def get_session(self):
        return self.SessionLocal()


def main():
    parser = argparse.ArgumentParser(description='Database management utility')
    parser.add_argument(
        '--init', action='store_true',
        help='Initialize database schema'
    )
    parser.add_argument(
        '--test', action='store_true',
        help='Test database connection'
    )
    
    args = parser.parse_args()
    
    db_manager = DatabaseManager()
    
    if not db_manager.connect():
        sys.exit(1)
    
    if args.test:
        if db_manager.test_connection():
            print("Database connection successful")
            sys.exit(0)
        else:
            sys.exit(1)
    
    if args.init:
        if db_manager.init_database():
            print("Database initialization completed")
            sys.exit(0)
        else:
            sys.exit(1)


if __name__ == '__main__':
    main()
