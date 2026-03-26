#!/usr/bin/env python3
import sys
import os
import json
import subprocess
import tempfile
from typing import Optional, Dict, Any
from datetime import datetime

import tornado.web
import tornado.escape
from sqlalchemy.orm import Session

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.models import Workflow, Task, TaskExecution, TaskLog
from database.db_manager import DatabaseManager
from web.workflow_scheduler import WorkflowScheduler
from web.handlers import BaseHandler


class ExecutionHandler(BaseHandler):
    @tornado.web.authenticated
    def post(self, workflow_id: int):
        user = self.get_current_user()
        session = self.db_manager.get_session()
        
        try:
            workflow = session.query(Workflow).filter(
                Workflow.id == workflow_id,
                Workflow.user_id == user['id']
            ).first()
            
            if not workflow:
                self.write_json({"error": "Workflow not found"}, 404)
                return
            
            tasks = session.query(Task).filter(
                Task.workflow_id == workflow_id
            ).all()
            
            if not tasks:
                self.write_json({"error": "No tasks found in workflow"}, 400)
                return
            
            scheduler = WorkflowScheduler(self.db_manager)
            result = scheduler.execute_workflow(workflow_id)
            
            if result['success']:
                self.write_json({
                    "message": "Workflow execution started",
                    "execution_ids": result['execution_ids']
                })
            else:
                self.write_json({"error": result['error']}, 500)
                
        except Exception as e:
            session.rollback()
            self.write_json({"error": str(e)}, 500)
        finally:
            session.close()


class TaskExecutionStatusHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self, workflow_id: int, execution_id: int):
        user = self.get_current_user()
        session = self.db_manager.get_session()
        
        try:
            execution = session.query(TaskExecution).filter(
                TaskExecution.id == execution_id,
                TaskExecution.workflow_id == workflow_id
            ).first()
            
            if not execution:
                self.write_json({"error": "Execution not found"}, 404)
                return
            
            execution_data = execution.to_dict()
            execution_data['logs'] = [log.to_dict() for log in execution.logs]
            self.write_json({"execution": execution_data})
            
        except Exception as e:
            self.write_json({"error": str(e)}, 500)
        finally:
            session.close()


class WorkflowExecutionsHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self, workflow_id: int):
        user = self.get_current_user()
        session = self.db_manager.get_session()
        
        try:
            workflow = session.query(Workflow).filter(
                Workflow.id == workflow_id,
                Workflow.user_id == user['id']
            ).first()
            
            if not workflow:
                self.write_json({"error": "Workflow not found"}, 404)
                return
            
            executions = session.query(TaskExecution).filter(
                TaskExecution.workflow_id == workflow_id
            ).order_by(TaskExecution.created_at.desc()).limit(100).all()
            
            self.write_json({"executions": [exec.to_dict() for exec in executions]})
            
        except Exception as e:
            self.write_json({"error": str(e)}, 500)
        finally:
            session.close()
