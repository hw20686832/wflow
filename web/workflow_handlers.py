#!/usr/bin/env python3
import sys
import os
import json
import yaml
import tempfile
import zipfile
from typing import Optional, Dict, Any
from datetime import datetime

import tornado.web
import tornado.escape
from sqlalchemy.orm import Session

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.models import Workflow, Task, TaskExecution, TaskLog
from database.db_manager import DatabaseManager
from web.handlers import BaseHandler


class WorkflowHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self, workflow_id: Optional[int] = None):
        user = self.get_current_user()
        session = self.db_manager.get_session()
        
        try:
            if workflow_id:
                workflow = session.query(Workflow).filter(
                    Workflow.id == workflow_id,
                    Workflow.user_id == user['id']
                ).first()
                
                if not workflow:
                    self.write_json({"error": "Workflow not found"}, 404)
                    return
                
                workflow_data = workflow.to_dict()
                workflow_data['tasks'] = [task.to_dict() for task in workflow.tasks]
                self.write_json({"workflow": workflow_data})
            else:
                workflows = session.query(Workflow).filter(
                    Workflow.user_id == user['id']
                ).all()
                
                workflows_data = []
                for workflow in workflows:
                    wf_data = workflow.to_dict()
                    wf_data['task_count'] = len(workflow.tasks)
                    workflows_data.append(wf_data)
                
                self.write_json({"workflows": workflows_data})
        except Exception as e:
            self.write_json({"error": str(e)}, 500)
        finally:
            session.close()

    @tornado.web.authenticated
    def post(self):
        user = self.get_current_user()
        session = self.db_manager.get_session()
        
        try:
            data = tornado.escape.json_decode(self.request.body)
            name = data.get('name')
            description = data.get('description')
            schedule = data.get('schedule')
            executor = data.get('executor', 'local')
            async_flag = data.get('async', False)
            logdir = data.get('logdir')
            mailto = data.get('mailto')
            resume = data.get('resume', False)
            env = data.get('env')
            workflow_type = data.get('type', 'serialFlow')
            
            if not name:
                self.write_json({"error": "Workflow name is required"}, 400)
                return
            
            workflow = Workflow(
                user_id=user['id'],
                name=name,
                description=description,
                schedule=schedule,
                executor=executor,
                async=async_flag,
                logdir=logdir,
                mailto=mailto,
                resume=resume,
                env=env,
                type=workflow_type
            )
            
            session.add(workflow)
            session.commit()
            session.refresh(workflow)
            
            self.write_json({
                "message": "Workflow created successfully",
                "workflow": workflow.to_dict()
            }, 201)
        except Exception as e:
            session.rollback()
            self.write_json({"error": str(e)}, 500)
        finally:
            session.close()

    @tornado.web.authenticated
    def put(self, workflow_id: int):
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
            
            data = tornado.escape.json_decode(self.request.body)
            
            for field in ['name', 'description', 'schedule', 'executor', 'async', 
                         'logdir', 'mailto', 'resume', 'env', 'type', 'is_active']:
                if field in data:
                    setattr(workflow, field, data[field])
            
            workflow.updated_at = datetime.utcnow()
            session.commit()
            session.refresh(workflow)
            
            self.write_json({
                "message": "Workflow updated successfully",
                "workflow": workflow.to_dict()
            })
        except Exception as e:
            session.rollback()
            self.write_json({"error": str(e)}, 500)
        finally:
            session.close()

    @tornado.web.authenticated
    def delete(self, workflow_id: int):
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
            
            session.delete(workflow)
            session.commit()
            
            self.write_json({"message": "Workflow deleted successfully"})
        except Exception as e:
            session.rollback()
            self.write_json({"error": str(e)}, 500)
        finally:
            session.close()


class TaskHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self, workflow_id: int, task_id: Optional[int] = None):
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
            
            if task_id:
                task = session.query(Task).filter(
                    Task.id == task_id,
                    Task.workflow_id == workflow_id
                ).first()
                
                if not task:
                    self.write_json({"error": "Task not found"}, 404)
                    return
                
                self.write_json({"task": task.to_dict()})
            else:
                tasks = session.query(Task).filter(
                    Task.workflow_id == workflow_id
                ).all()
                
                self.write_json({"tasks": [task.to_dict() for task in tasks]})
        except Exception as e:
            self.write_json({"error": str(e)}, 500)
        finally:
            session.close()

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
            
            data = tornado.escape.json_decode(self.request.body)
            name = data.get('name')
            command = data.get('command')
            deps = data.get('deps')
            retry_count = data.get('retry_count', 0)
            retry_interval = data.get('retry_interval', 0)
            
            if not name or not command:
                self.write_json({"error": "Task name and command are required"}, 400)
                return
            
            task = Task(
                workflow_id=workflow_id,
                name=name,
                command=command,
                deps=deps,
                retry_count=retry_count,
                retry_interval=retry_interval
            )
            
            session.add(task)
            session.commit()
            session.refresh(task)
            
            self.write_json({
                "message": "Task created successfully",
                "task": task.to_dict()
            }, 201)
        except Exception as e:
            session.rollback()
            self.write_json({"error": str(e)}, 500)
        finally:
            session.close()

    @tornado.web.authenticated
    def put(self, workflow_id: int, task_id: int):
        user = self.get_current_user()
        session = self.db_manager.get_session()
        
        try:
            task = session.query(Task).filter(
                Task.id == task_id,
                Task.workflow_id == workflow_id
            ).first()
            
            if not task:
                self.write_json({"error": "Task not found"}, 404)
                return
            
            data = tornado.escape.json_decode(self.request.body)
            
            for field in ['name', 'command', 'deps', 'retry_count', 'retry_interval']:
                if field in data:
                    setattr(task, field, data[field])
            
            task.updated_at = datetime.utcnow()
            session.commit()
            session.refresh(task)
            
            self.write_json({
                "message": "Task updated successfully",
                "task": task.to_dict()
            })
        except Exception as e:
            session.rollback()
            self.write_json({"error": str(e)}, 500)
        finally:
            session.close()

    @tornado.web.authenticated
    def delete(self, workflow_id: int, task_id: int):
        user = self.get_current_user()
        session = self.db_manager.get_session()
        
        try:
            task = session.query(Task).filter(
                Task.id == task_id,
                Task.workflow_id == workflow_id
            ).first()
            
            if not task:
                self.write_json({"error": "Task not found"}, 404)
                return
            
            session.delete(task)
            session.commit()
            
            self.write_json({"message": "Task deleted successfully"})
        except Exception as e:
            session.rollback()
            self.write_json({"error": str(e)}, 500)
        finally:
            session.close()


class TaskExecutionHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self, workflow_id: int, task_id: int, execution_id: Optional[int] = None):
        user = self.get_current_user()
        session = self.db_manager.get_session()
        
        try:
            if execution_id:
                execution = session.query(TaskExecution).filter(
                    TaskExecution.id == execution_id,
                    TaskExecution.workflow_id == workflow_id,
                    TaskExecution.task_id == task_id
                ).first()
                
                if not execution:
                    self.write_json({"error": "Execution not found"}, 404)
                    return
                
                execution_data = execution.to_dict()
                execution_data['logs'] = [log.to_dict() for log in execution.logs]
                self.write_json({"execution": execution_data})
            else:
                executions = session.query(TaskExecution).filter(
                    TaskExecution.workflow_id == workflow_id,
                    TaskExecution.task_id == task_id
                ).order_by(TaskExecution.created_at.desc()).all()
                
                self.write_json({"executions": [exec.to_dict() for exec in executions]})
        except Exception as e:
            self.write_json({"error": str(e)}, 500)
        finally:
            session.close()


class ImportExportHandler(BaseHandler):
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
            
            workflow_data = {
                'name': workflow.name,
                'description': workflow.description,
                'schedule': workflow.schedule,
                'executor': workflow.executor,
                'async': workflow.async,
                'logdir': workflow.logdir,
                'mailto': workflow.mailto,
                'resume': workflow.resume,
                'env': workflow.env,
                'type': workflow.type,
                'tasks': [task.to_dict() for task in workflow.tasks]
            }
            
            self.set_header("Content-Type", "application/json")
            self.set_header("Content-Disposition", f"attachment; filename={workflow.name}.json")
            self.write(json.dumps(workflow_data, ensure_ascii=False, indent=2))
            self.finish()
        except Exception as e:
            self.write_json({"error": str(e)}, 500)
        finally:
            session.close()

    @tornado.web.authenticated
    def post(self):
        user = self.get_current_user()
        session = self.db_manager.get_session()
        
        try:
            data = tornado.escape.json_decode(self.request.body)
            workflow_data = data.get('workflow')
            
            if not workflow_data:
                self.write_json({"error": "Workflow data is required"}, 400)
                return
            
            workflow = Workflow(
                user_id=user['id'],
                name=workflow_data.get('name'),
                description=workflow_data.get('description'),
                schedule=workflow_data.get('schedule'),
                executor=workflow_data.get('executor', 'local'),
                async=workflow_data.get('async', False),
                logdir=workflow_data.get('logdir'),
                mailto=workflow_data.get('mailto'),
                resume=workflow_data.get('resume', False),
                env=workflow_data.get('env'),
                type=workflow_data.get('type', 'serialFlow')
            )
            
            session.add(workflow)
            session.flush()
            
            for task_data in workflow_data.get('tasks', []):
                task = Task(
                    workflow_id=workflow.id,
                    name=task_data.get('name'),
                    command=task_data.get('command'),
                    deps=task_data.get('deps'),
                    retry_count=task_data.get('retry_count', 0),
                    retry_interval=task_data.get('retry_interval', 0)
                )
                session.add(task)
            
            session.commit()
            session.refresh(workflow)
            
            self.write_json({
                "message": "Workflow imported successfully",
                "workflow": workflow.to_dict()
            }, 201)
        except Exception as e:
            session.rollback()
            self.write_json({"error": str(e)}, 500)
        finally:
            session.close()
