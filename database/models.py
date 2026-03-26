#!/usr/bin/env python3
from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, JSON, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), nullable=False, unique=True, index=True)
    password = Column(String(255), nullable=False)
    email = Column(String(100), nullable=False, unique=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    
    workflows = relationship("Workflow", back_populates="user", cascade="all, delete-orphan")
    sessions = relationship("UserSession", back_populates="user", cascade="all, delete-orphan")
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'is_active': self.is_active
        }


class Workflow(Base):
    __tablename__ = 'workflows'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    name = Column(String(100), nullable=False, index=True)
    description = Column(Text)
    schedule = Column(String(100))
    executor = Column(String(50), default='local')
    async = Column(Boolean, default=False)
    logdir = Column(String(255))
    mailto = Column(JSON)
    resume = Column(Boolean, default=False)
    env = Column(JSON)
    type = Column(String(50), default='serialFlow')
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True, index=True)
    
    user = relationship("User", back_populates="workflows")
    tasks = relationship("Task", back_populates="workflow", cascade="all, delete-orphan")
    executions = relationship("TaskExecution", back_populates="workflow", cascade="all, delete-orphan")
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'user_id': self.user_id,
            'name': self.name,
            'description': self.description,
            'schedule': self.schedule,
            'executor': self.executor,
            'async': self.async,
            'logdir': self.logdir,
            'mailto': self.mailto,
            'resume': self.resume,
            'env': self.env,
            'type': self.type,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'is_active': self.is_active
        }


class Task(Base):
    __tablename__ = 'tasks'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    workflow_id = Column(Integer, ForeignKey('workflows.id', ondelete='CASCADE'), nullable=False, index=True)
    name = Column(String(100), nullable=False, index=True)
    command = Column(JSON, nullable=False)
    deps = Column(JSON)
    retry_count = Column(Integer, default=0)
    retry_interval = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    workflow = relationship("Workflow", back_populates="tasks")
    executions = relationship("TaskExecution", back_populates="task", cascade="all, delete-orphan")
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'workflow_id': self.workflow_id,
            'name': self.name,
            'command': self.command,
            'deps': self.deps,
            'retry_count': self.retry_count,
            'retry_interval': self.retry_interval,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class TaskExecution(Base):
    __tablename__ = 'task_executions'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(Integer, ForeignKey('tasks.id', ondelete='CASCADE'), nullable=False, index=True)
    workflow_id = Column(Integer, ForeignKey('workflows.id', ondelete='CASCADE'), nullable=False, index=True)
    status = Column(Enum('pending', 'running', 'success', 'failed', 'skipped'), default='pending', index=True)
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    exit_code = Column(Integer)
    retry_count = Column(Integer, default=0)
    error_message = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    task = relationship("Task", back_populates="executions")
    workflow = relationship("Workflow", back_populates="executions")
    logs = relationship("TaskLog", back_populates="execution", cascade="all, delete-orphan")
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'task_id': self.task_id,
            'workflow_id': self.workflow_id,
            'status': self.status,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'exit_code': self.exit_code,
            'retry_count': self.retry_count,
            'error_message': self.error_message,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class TaskLog(Base):
    __tablename__ = 'task_logs'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    execution_id = Column(Integer, ForeignKey('task_executions.id', ondelete='CASCADE'), nullable=False, index=True)
    log_content = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    execution = relationship("TaskExecution", back_populates="logs")
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'execution_id': self.execution_id,
            'log_content': self.log_content,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class UserSession(Base):
    __tablename__ = 'user_sessions'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    session_token = Column(String(255), nullable=False, unique=True, index=True)
    expires_at = Column(DateTime, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="sessions")
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'user_id': self.user_id,
            'session_token': self.session_token,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
