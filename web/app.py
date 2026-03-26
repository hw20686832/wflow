#!/usr/bin/env python3
import sys
import os
import logging

import tornado.web
import tornado.ioloop

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db_manager import DatabaseManager
from web.auth_service import AuthService
from web.handlers import (
    AuthHandler, RegisterHandler, LogoutHandler, UserHandler, HealthHandler
)
from web.workflow_handlers import (
    WorkflowHandler, TaskHandler, TaskExecutionHandler, ImportExportHandler
)
from web.execution_handlers import (
    ExecutionHandler, TaskExecutionStatusHandler, WorkflowExecutionsHandler
)
from config.loader import get_config


def make_app(db_manager: DatabaseManager, auth_service: AuthService, config):
    return tornado.web.Application([
        (r"/api/health", HealthHandler, dict(db_manager=db_manager, auth_service=auth_service)),
        (r"/api/auth/login", AuthHandler, dict(db_manager=db_manager, auth_service=auth_service)),
        (r"/api/auth/register", RegisterHandler, dict(db_manager=db_manager, auth_service=auth_service)),
        (r"/api/auth/logout", LogoutHandler, dict(db_manager=db_manager, auth_service=auth_service)),
        (r"/api/user", UserHandler, dict(db_manager=db_manager, auth_service=auth_service)),
        
        (r"/api/workflows", WorkflowHandler, dict(db_manager=db_manager, auth_service=auth_service)),
        (r"/api/workflows/(\d+)", WorkflowHandler, dict(db_manager=db_manager, auth_service=auth_service)),
        (r"/api/workflows/(\d+)/tasks", TaskHandler, dict(db_manager=db_manager, auth_service=auth_service)),
        (r"/api/workflows/(\d+)/tasks/(\d+)", TaskHandler, dict(db_manager=db_manager, auth_service=auth_service)),
        (r"/api/workflows/(\d+)/tasks/(\d+)/executions", TaskExecutionHandler, dict(db_manager=db_manager, auth_service=auth_service)),
        (r"/api/workflows/(\d+)/tasks/(\d+)/executions/(\d+)", TaskExecutionHandler, dict(db_manager=db_manager, auth_service=auth_service)),
        
        (r"/api/workflows/(\d+)/execute", ExecutionHandler, dict(db_manager=db_manager, auth_service=auth_service)),
        (r"/api/workflows/(\d+)/executions", WorkflowExecutionsHandler, dict(db_manager=db_manager, auth_service=auth_service)),
        (r"/api/workflows/(\d+)/executions/(\d+)", TaskExecutionStatusHandler, dict(db_manager=db_manager, auth_service=auth_service)),
        
        (r"/api/workflows/(\d+)/export", ImportExportHandler, dict(db_manager=db_manager, auth_service=auth_service)),
        (r"/api/workflows/import", ImportExportHandler, dict(db_manager=db_manager, auth_service=auth_service)),
        
        (r"/(.*)", tornado.web.StaticFileHandler, dict(path="frontend/dist", default_filename="index.html")),
    ], debug=config.get_bool('app.debug', False))


def main():
    config = get_config()
    
    logging.basicConfig(
        level=getattr(logging, config.get_str('logging.level', 'INFO')),
        format=config.get_str('logging.format', '%(asctime)s [%(name)s] %(levelname)s: %(message)s')
    )
    logger = logging.getLogger(__name__)
    
    server_config = config.get('server', {})
    host = server_config.get('host', '0.0.0.0')
    port = server_config.get('port', 8888)
    
    logger.info("Initializing database manager...")
    db_manager = DatabaseManager(config)
    
    if not db_manager.connect():
        logger.error("Failed to connect to database")
        sys.exit(1)
    
    logger.info("Initializing auth service...")
    auth_service = AuthService(db_manager, config)
    
    logger.info("Creating Tornado application...")
    app = make_app(db_manager, auth_service, config)
    
    logger.info(f"Starting server on {host}:{port}")
    app.listen(port, host)
    
    tornado.ioloop.IOLoop.current().start()


if __name__ == '__main__':
    main()
