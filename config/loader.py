#!/usr/bin/env python3
import os
import yaml
from typing import Dict, Any, Optional
from pathlib import Path


class ConfigLoader:
    _instance = None
    _config: Optional[Dict[str, Any]] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._config is None:
            self._load_config()
    
    def _load_config(self):
        config_paths = [
            'config/settings.yml',
            'config/settings.dev.yml',
            'config/settings.prod.yml',
            '../config/settings.yml',
        ]
        
        config_file = None
        for path in config_paths:
            if os.path.exists(path):
                config_file = path
                break
        
        if config_file:
            with open(config_file, 'r', encoding='utf-8') as f:
                self._config = yaml.safe_load(f)
        else:
            self._config = self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        return {
            'app': {
                'name': 'wflow',
                'version': '1.0.0',
                'environment': 'development',
                'debug': True
            },
            'server': {
                'host': '0.0.0.0',
                'port': 8888,
                'workers': 4,
                'timeout': 30
            },
            'database': {
                'mysql': {
                    'host': 'localhost',
                    'port': 3306,
                    'user': 'root',
                    'password': '',
                    'database': 'wflow_db',
                    'charset': 'utf8mb4',
                    'pool_size': 20,
                    'max_overflow': 10,
                    'pool_timeout': 30,
                    'pool_recycle': 3600
                }
            },
            'redis': {
                'host': 'localhost',
                'port': 6379,
                'db': 0,
                'password': '',
                'max_connections': 50,
                'socket_timeout': 5,
                'socket_connect_timeout': 5
            },
            'session': {
                'secret_key': 'your-secret-key-change-this-in-production',
                'expire_hours': 24,
                'cookie_name': 'wflow_session',
                'cookie_secure': False,
                'cookie_httponly': True
            },
            'logging': {
                'level': 'INFO',
                'format': '%(asctime)s [%(name)s] %(levelname)s: %(message)s',
                'file': {
                    'enabled': True,
                    'path': 'var/log/app.log',
                    'max_bytes': 10485760,
                    'backup_count': 5
                },
                'console': {
                    'enabled': True
                }
            },
            'workflow': {
                'default_executor': 'local',
                'default_type': 'serialFlow',
                'log_dir': 'var/log/workflows',
                'config_dir': 'conf/workflows',
                'max_retries': 3,
                'default_retry_interval': 5
            },
            'celery': {
                'broker_url': 'redis://localhost:6379/0',
                'result_backend': 'redis://localhost:6379/0',
                'task_result_expires': 180,
                'worker_concurrency': 4,
                'worker_prefetch_multiplier': 4,
                'task_acks_late': True,
                'worker_prefetch_multiplier': 1
            }
        }
    
    def get(self, key: str, default: Any = None) -> Any:
        keys = key.split('.')
        value = self._config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def get_int(self, key: str, default: int = 0) -> int:
        value = self.get(key, default)
        try:
            return int(value)
        except (ValueError, TypeError):
            return default
    
    def get_str(self, key: str, default: str = '') -> str:
        value = self.get(key, default)
        return str(value) if value is not None else default
    
    def get_bool(self, key: str, default: bool = False) -> bool:
        value = self.get(key, default)
        return bool(value)
    
    def get_list(self, key: str, default: list = None) -> list:
        value = self.get(key, default)
        if isinstance(value, list):
            return value
        return default if default is not None else []
    
    def reload(self):
        self._load_config()
    
    def get_database_url(self) -> str:
        mysql_config = self.get('database.mysql', {})
        return (
            f"mysql+pymysql://{mysql_config.get('user', 'root')}:"
            f"{mysql_config.get('password', '')}@"
            f"{mysql_config.get('host', 'localhost')}:"
            f"{mysql_config.get('port', 3306)}/"
            f"{mysql_config.get('database', 'wflow_db')}"
            f"?charset={mysql_config.get('charset', 'utf8mb4')}"
        )
    
    def get_redis_url(self) -> str:
        redis_config = self.get('redis', {})
        password = redis_config.get('password', '')
        if password:
            return f"redis://:{password}@{redis_config.get('host', 'localhost')}:{redis_config.get('port', 6379)}/{redis_config.get('db', 0)}"
        return f"redis://{redis_config.get('host', 'localhost')}:{redis_config.get('port', 6379)}/{redis_config.get('db', 0)}"
    
    def get_mysql_connection_params(self) -> Dict[str, Any]:
        mysql_config = self.get('database.mysql', {})
        return {
            'host': mysql_config.get('host', 'localhost'),
            'port': mysql_config.get('port', 3306),
            'user': mysql_config.get('user', 'root'),
            'password': mysql_config.get('password', ''),
            'database': mysql_config.get('database', 'wflow_db'),
            'charset': mysql_config.get('charset', 'utf8mb4'),
            'pool_size': mysql_config.get('pool_size', 20),
            'max_overflow': mysql_config.get('max_overflow', 10),
            'pool_timeout': mysql_config.get('pool_timeout', 30),
            'pool_recycle': mysql_config.get('pool_recycle', 3600)
        }


def get_config() -> ConfigLoader:
    return ConfigLoader()


config = get_config()
