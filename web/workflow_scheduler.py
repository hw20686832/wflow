#!/usr/bin/env python3
import sys
import os
import yaml
import tempfile
import configparser
from typing import Optional, Dict, Any, List
from datetime import datetime
from pathlib import Path

import schedule
from sqlalchemy.orm import Session

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.models import Workflow, Task, TaskExecution, TaskLog
from database.db_manager import DatabaseManager
from lib import utils


class WorkflowScheduler:
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.config = self._load_config()
        self.log = utils.get_log("WorkflowScheduler")
        
    def _load_config(self) -> configparser.ConfigParser:
        config = configparser.ConfigParser()
        config.read('conf/common.conf')
        return config
    
    def _generate_workflow_yaml(self, workflow: Workflow) -> str:
        workflow_data = {
            'name': workflow.name,
            'schedule': workflow.schedule,
            'executor': workflow.executor,
            'is_async': workflow.is_async,
            'logdir': workflow.logdir or f'var/log/{workflow.name}',
            'mailto': workflow.mailto,
            'resume': workflow.resume,
            'env': workflow.env,
            'type': workflow.type,
            'tasks': []
        }
        
        for task in workflow.tasks:
            task_data = {
                'name': task.name,
                'command': task.command,
                'retry_count': task.retry_count,
                'retry_interval': task.retry_interval
            }
            
            if task.deps:
                task_data['deps'] = task.deps
            
            workflow_data['tasks'].append(task_data)
        
        return yaml.dump(workflow_data, default_flow_style=False)
    
    def _save_workflow_config(self, workflow: Workflow) -> str:
        workflow_yaml = self._generate_workflow_yaml(workflow)
        
        workflow_dir = Path('conf/workflows')
        workflow_dir.mkdir(parents=True, exist_ok=True)
        
        config_path = workflow_dir / f'{workflow.name}_{workflow.id}.yml'
        
        with open(config_path, 'w', encoding='utf-8') as f:
            f.write(workflow_yaml)
        
        return str(config_path)
    
    def execute_workflow(self, workflow_id: int) -> Dict[str, Any]:
        session = self.db_manager.get_session()
        
        try:
            workflow = session.query(Workflow).filter(
                Workflow.id == workflow_id
            ).first()
            
            if not workflow:
                return {'success': False, 'error': 'Workflow not found'}
            
            config_path = self._save_workflow_config(workflow)
            
            self.log.info(f"Executing workflow: {workflow.name} (ID: {workflow.id})")
            
            execution_ids = []
            
            for task in workflow.tasks:
                execution = TaskExecution(
                    task_id=task.id,
                    workflow_id=workflow_id,
                    status='pending'
                )
                session.add(execution)
                session.flush()
                execution_ids.append(execution.id)
            
            session.commit()
            
            self._run_workflow_tasks(workflow, execution_ids)
            
            return {
                'success': True,
                'workflow_id': workflow_id,
                'execution_ids': execution_ids,
                'message': 'Workflow execution started'
            }
            
        except Exception as e:
            session.rollback()
            self.log.error(f"Failed to execute workflow: {e}")
            return {'success': False, 'error': str(e)}
        finally:
            session.close()
    
    def _run_workflow_tasks(self, workflow: Workflow, execution_ids: List[int]):
        try:
            tasks = workflow.tasks
            
            if workflow.type == 'serialFlow':
                self._run_serial_tasks(tasks, execution_ids)
            elif workflow.type == 'parallelFlow':
                self._run_parallel_tasks(tasks, execution_ids)
            else:
                self.log.warning(f"Unknown workflow type: {workflow.type}")
                self._run_serial_tasks(tasks, execution_ids)
                
        except Exception as e:
            self.log.error(f"Failed to run workflow tasks: {e}")
    
    def _run_serial_tasks(self, tasks: List[Task], execution_ids: List[int]):
        session = self.db_manager.get_session()
        
        try:
            for i, task in enumerate(tasks):
                if i < len(execution_ids):
                    execution_id = execution_ids[i]
                    self._execute_single_task(session, task, execution_id)
                    
                    execution = session.query(TaskExecution).filter(
                        TaskExecution.id == execution_id
                    ).first()
                    
                    if execution and execution.status == 'failed' and task.retry_count > 0:
                        for retry in range(task.retry_count):
                            self.log.info(f"Retrying task {task.name}, attempt {retry + 1}")
                            import time
                            time.sleep(task.retry_interval)
                            
                            execution.retry_count = retry + 1
                            session.commit()
                            
                            self._execute_single_task(session, task, execution_id)
                            
                            execution = session.query(TaskExecution).filter(
                                TaskExecution.id == execution_id
                            ).first()
                            
                            if execution and execution.status == 'success':
                                break
                            
                            if execution and execution.status == 'failed':
                                break
                                
        except Exception as e:
            self.log.error(f"Failed to run serial tasks: {e}")
        finally:
            session.close()
    
    def _run_parallel_tasks(self, tasks: List[Task], execution_ids: List[int]):
        import threading
        
        def run_task(task, execution_id):
            session = self.db_manager.get_session()
            try:
                self._execute_single_task(session, task, execution_id)
            except Exception as e:
                self.log.error(f"Failed to run task {task.name}: {e}")
            finally:
                session.close()
        
        threads = []
        for i, task in enumerate(tasks):
            if i < len(execution_ids):
                thread = threading.Thread(
                    target=run_task,
                    args=(task, execution_ids[i])
                )
                threads.append(thread)
                thread.start()
        
        for thread in threads:
            thread.join()
    
    def _execute_single_task(self, session: Session, task: Task, execution_id: int):
        import subprocess
        import tempfile
        
        try:
            execution = session.query(TaskExecution).filter(
                TaskExecution.id == execution_id
            ).first()
            
            if not execution:
                return
            
            execution.status = 'running'
            execution.start_time = datetime.utcnow()
            session.commit()
            
            command = task.command
            if isinstance(command, str):
                command = command.split()
            
            log_file = tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix='.log')
            log_file_path = log_file.name
            
            try:
                process = subprocess.Popen(
                    command,
                    stdout=log_file,
                    stderr=subprocess.STDOUT,
                    shell=False
                )
                exit_code = process.wait()
                
                log_file.close()
                
                with open(log_file_path, 'r', encoding='utf-8') as f:
                    log_content = f.read()
                
                task_log = TaskLog(
                    execution_id=execution_id,
                    log_content=log_content
                )
                session.add(task_log)
                
                execution.status = 'success' if exit_code == 0 else 'failed'
                execution.end_time = datetime.utcnow()
                execution.exit_code = exit_code
                
                if exit_code != 0:
                    execution.error_message = f"Task failed with exit code {exit_code}"
                
                session.commit()
                
            except Exception as e:
                execution.status = 'failed'
                execution.end_time = datetime.utcnow()
                execution.error_message = str(e)
                session.commit()
                
            finally:
                if os.path.exists(log_file_path):
                    os.unlink(log_file_path)
                    
        except Exception as e:
            self.log.error(f"Failed to execute task {task.name}: {e}")
    
    def schedule_workflow(self, workflow_id: int) -> Dict[str, Any]:
        session = self.db_manager.get_session()
        
        try:
            workflow = session.query(Workflow).filter(
                Workflow.id == workflow_id,
                Workflow.is_active == True
            ).first()
            
            if not workflow:
                return {'success': False, 'error': 'Workflow not found or inactive'}
            
            if not workflow.schedule:
                return {'success': False, 'error': 'Workflow has no schedule'}
            
            config_path = self._save_workflow_config(workflow)
            
            self.log.info(f"Scheduling workflow: {workflow.name} (ID: {workflow.id})")
            
            return {
                'success': True,
                'workflow_id': workflow_id,
                'schedule': workflow.schedule,
                'message': 'Workflow scheduled successfully'
            }
            
        except Exception as e:
            self.log.error(f"Failed to schedule workflow: {e}")
            return {'success': False, 'error': str(e)}
        finally:
            session.close()
    
    def get_workflow_status(self, workflow_id: int) -> Dict[str, Any]:
        session = self.db_manager.get_session()
        
        try:
            executions = session.query(TaskExecution).filter(
                TaskExecution.workflow_id == workflow_id
            ).order_by(TaskExecution.created_at.desc()).limit(10).all()
            
            status_summary = {
                'pending': 0,
                'running': 0,
                'success': 0,
                'failed': 0,
                'skipped': 0
            }
            
            for execution in executions:
                status_summary[execution.status] += 1
            
            return {
                'success': True,
                'workflow_id': workflow_id,
                'status_summary': status_summary,
                'recent_executions': [exec.to_dict() for exec in executions]
            }
            
        except Exception as e:
            self.log.error(f"Failed to get workflow status: {e}")
            return {'success': False, 'error': str(e)}
        finally:
            session.close()
