#!/usr/bin/env python3
import os
import sys
import time
import signal
import datetime
import functools
import traceback
import configparser
import json
import threading
from typing import Optional, List, Dict, Any, Union
from multiprocessing import Process

import gevent
from gevent import monkey
monkey.patch_all()
from gevent import Greenlet, subprocess

import socket

import yaml
from babel import dates
from jinja2 import Environment
from croniter import croniter
from dateutil.relativedelta import relativedelta

from executor import work
from lib import utils
from lib.redis_state_manager import RedisTaskStateManager


common_conf = configparser.ConfigParser()
common_conf.read("conf/common.conf")


class TaskStateManager:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._backend = None
                    cls._instance._state_file = None
                    cls._instance._state = {}
                    cls._instance._lock = threading.RLock()
        return cls._instance

    def set_backend(self, backend: str = 'file', **kwargs):
        self._backend = backend
        
        if backend == 'redis':
            redis_manager = RedisTaskStateManager()
            redis_host = kwargs.get('redis_host', 'localhost')
            redis_port = kwargs.get('redis_port', 6379)
            redis_db = kwargs.get('redis_db', 0)
            redis_password = kwargs.get('redis_password', None)
            
            if redis_manager.connect(redis_host, redis_port, redis_db, redis_password):
                self._redis_manager = redis_manager
            else:
                utils.get_log("StateManager").warning(
                    "Failed to connect to Redis, falling back to file backend")
                self._backend = 'file'
        else:
            self._redis_manager = None

    def set_state_file(self, state_file: str):
        if self._backend == 'redis':
            return
        self._state_file = state_file
        self._load_state()

    def _load_state(self):
        if self._state_file and os.path.exists(self._state_file):
            try:
                with open(self._state_file, 'r') as f:
                    self._state = json.load(f)
            except Exception:
                self._state = {}

    def _save_state(self):
        if self._state_file:
            with open(self._state_file, 'w') as f:
                json.dump(self._state, f, indent=2, default=str)

    def get_task_state(self, workflow_name: str, task_name: str) -> Optional[Dict[str, Any]]:
        if self._backend == 'redis' and self._redis_manager:
            return self._redis_manager.get_task_state(workflow_name, task_name)
        
        key = f"{workflow_name}:{task_name}"
        with self._lock:
            return self._state.get(key)

    def set_task_state(self, workflow_name: str, task_name: str, state: Dict[str, Any]):
        if self._backend == 'redis' and self._redis_manager:
            self._redis_manager.set_task_state(workflow_name, task_name, state)
            return
        
        key = f"{workflow_name}:{task_name}"
        with self._lock:
            self._state[key] = state
            self._save_state()

    def clear_workflow_state(self, workflow_name: str):
        if self._backend == 'redis' and self._redis_manager:
            self._redis_manager.clear_workflow_state(workflow_name)
            return
        
        with self._lock:
            keys_to_remove = [k for k in self._state.keys() if k.startswith(f"{workflow_name}:")]
            for key in keys_to_remove:
                del self._state[key]
            self._save_state()

    def get_all_workflow_tasks(self, workflow_name: str) -> Dict[str, Dict[str, Any]]:
        if self._backend == 'redis' and self._redis_manager:
            return self._redis_manager.get_all_workflow_tasks(workflow_name)
        
        result = {}
        with self._lock:
            for key, value in self._state.items():
                if key.startswith(f"{workflow_name}:"):
                    task_name = key.split(':', 1)[1]
                    result[task_name] = value
        return result


state_manager = TaskStateManager()


class Task(Greenlet):
    name: Optional[str] = None
    command: Optional[List[str]] = None
    disabled: bool = False
    proc: Optional[subprocess.Popen] = None

    def __init__(self, name: str, sysdate: str, *,
                 command: Optional[List[str]] = None,
                 deps: Optional[List[str]] = None,
                 logdir: Optional[str] = None,
                 disabled: bool = False,
                 greenlets: Optional[Dict[str, Greenlet]] = None,
                 workflow_name: Optional[str] = None,
                 retry_count: int = 0,
                 retry_interval: int = 5,
                 resume: bool = False):
        super(Task, self).__init__()
        self.name = name
        self.command = command
        self.deps = deps or []
        self.logdir = logdir
        self.disabled = disabled
        self.sysdate = sysdate
        self.greenlets = greenlets or {}
        self.workflow_name = workflow_name or 'default'
        self.retry_count = retry_count
        self.retry_interval = retry_interval
        self.resume = resume
        self.log = utils.get_log("Task")

        gevent.signal_handler(signal.SIGINT, self.kill)

    def _run(self) -> int:
        rs = utils.EXIT_ERROR
        start = 0
        end = 0

        if self.resume:
            saved_state = state_manager.get_task_state(self.workflow_name, self.name)
            if saved_state and saved_state.get('status') == 'completed':
                self.log.info(f"Task '{self.name}' already completed, skipping.")
                return saved_state.get('return_code', utils.EXIT_COMPLETE)

        for d in self.deps:
            if ':' in d:
                workflow, task = d.split(':', 1)
                saved_state = state_manager.get_task_state(workflow, task)
                if saved_state is None:
                    self.log.error(
                        f"Cross-workflow dependency '{d}' not found in state.")
                    break
                rs = saved_state.get('return_code', utils.EXIT_ERROR)
            else:
                try:
                    rs = self.greenlets[d].get()
                except KeyError:
                    self.log.error(
                        f"Dependent task '{d}' not found in context '{self.name}'.")
                    break
            if rs != utils.EXIT_COMPLETE:
                break
        else:
            self.log.debug(f"`{self.name}` start.")
            start = time.time()
            try:
                rs = self.execute_with_retry()
            except Exception:
                self.log.error(traceback.format_exc())
                rs = utils.EXIT_ERROR
            end = time.time()

        self.log.debug(f"`{self.name}` exited ({rs}), cost {end-start:.3f} seconds.")
        return rs

    def execute_with_retry(self) -> int:
        return_code = utils.EXIT_ERROR
        attempt = 0
        max_attempts = self.retry_count + 1

        while attempt < max_attempts:
            attempt += 1
            self.log.info(f"Task '{self.name}' attempt {attempt}/{max_attempts}")
            
            return_code = self.execute()
            
            if return_code == utils.EXIT_COMPLETE:
                state_manager.set_task_state(
                    self.workflow_name, self.name,
                    {
                        'status': 'completed',
                        'return_code': return_code,
                        'start_time': datetime.datetime.now().isoformat(),
                        'end_time': datetime.datetime.now().isoformat()
                    }
                )
                return return_code
            
            if attempt < max_attempts:
                self.log.warning(
                    f"Task '{self.name}' failed with code {return_code}, "
                    f"retrying in {self.retry_interval} seconds...")
                time.sleep(self.retry_interval)

        state_manager.set_task_state(
            self.workflow_name, self.name,
            {
                'status': 'failed',
                'return_code': return_code,
                'attempts': attempt,
                'start_time': datetime.datetime.now().isoformat(),
                'end_time': datetime.datetime.now().isoformat()
            }
        )
        return return_code

    def execute(self) -> int:
        if not self.disabled:
            if not self.command:
                return utils.EXIT_COMPLETE
            logfile = os.path.join(self.logdir, f"Task-{self.name}.log")
            with open(logfile, "a") as f:
                self.proc = subprocess.Popen(
                    self.command,
                    stdout=f, stderr=subprocess.STDOUT,
                    shell=False
                )
                return_code = self.proc.wait()
            return return_code
        else:
            return utils.EXIT_DISABLED


class ClusterTask(Task):
    def execute(self) -> int:
        if not self.disabled:
            if not self.command:
                return utils.EXIT_COMPLETE
            logfile = os.path.join(self.logdir, f"Task-{self.name}.log")
            c = work.apply_async((self.command, logfile))
            return c.get()
        else:
            return utils.EXIT_DISABLED


class TaskFlow(Greenlet):
    name: Optional[str] = None
    tasks: Optional[List[Union[Task, 'TaskFlow']]] = None
    disabled: bool = False

    def __init__(self, name: str, deps: List[str], *tasks: Union[Task, 'TaskFlow'],
                 greenlets: Optional[Dict[str, Greenlet]] = None,
                 disabled: bool = False,
                 workflow_name: Optional[str] = None,
                 resume: bool = False):
        super(TaskFlow, self).__init__()
        self.name = name
        self.deps = deps or []
        self.tasks = list(tasks)
        self.disabled = disabled
        self.greenlets = greenlets or {}
        self.workflow_name = workflow_name or 'default'
        self.resume = resume
        self.log = utils.get_log(f"{self.__class__.__name__}#{self.name}")

    def append(self, task: Union[Task, 'TaskFlow']) -> None:
        self.tasks.append(task)

    def _run(self) -> int:
        rs = utils.EXIT_ERROR
        for d in self.deps:
            if ':' in d:
                workflow, task = d.split(':', 1)
                saved_state = state_manager.get_task_state(workflow, task)
                if saved_state is None:
                    self.log.error(f"Cross-workflow dependency '{d}' not found in state.")
                    break
                rs = saved_state.get('return_code', utils.EXIT_ERROR)
            else:
                try:
                    rs = self.greenlets[d].get()
                except KeyError:
                    self.log.error(f"Dependent task '{d}' not found in context.")
                    break
            if rs != utils.EXIT_COMPLETE:
                break
        else:
            if self.disabled:
                rs = utils.EXIT_DISABLED
            else:
                rs = self.execute()

        if isinstance(rs, gevent.GreenletExit):
            rs = utils.EXIT_CANCEL
        return rs


class ParallelFlow(TaskFlow):
    def execute(self) -> int:
        return_code = utils.EXIT_COMPLETE
        for task in self.tasks:
            task.start()

        for task in self.tasks:
            rc = task.get()
            if rc != utils.EXIT_COMPLETE and rc != utils.EXIT_DISABLED:
                return_code = rc

        return return_code


class SerialFlow(TaskFlow):
    def execute(self) -> int:
        return_code = utils.EXIT_COMPLETE
        for task in self.tasks:
            task.start()
            return_code = task.get()
            if return_code != utils.EXIT_COMPLETE:
                break

        return return_code


def job_generator(conf: Dict[str, Any], sysdate: str,
                  task_class: type, logdir: Optional[str] = None,
                  greenlets: Optional[Dict[str, Greenlet]] = None,
                  workflow_name: Optional[str] = None,
                  resume: bool = False) -> Union[Task, TaskFlow]:
    task_type = conf.get('type')
    retry_count = conf.get('retry_count', 0)
    retry_interval = conf.get('retry_interval', 5)
    
    if task_type == 'serialFlow':
        base = SerialFlow(
            conf['name'], conf.get('deps', []),
            *(job_generator(t, sysdate, task_class, logdir, greenlets, workflow_name, resume)
              for t in (conf.get('tasks', []) or [])),
            greenlets=greenlets,
            disabled=bool(conf.get('disabled')),
            workflow_name=workflow_name,
            resume=resume
        )
    elif task_type == 'parallelFlow':
        base = ParallelFlow(
            conf['name'], conf.get('deps', []),
            *(job_generator(t, sysdate, task_class, logdir, greenlets, workflow_name, resume)
              for t in (conf.get('tasks', []) or [])),
            greenlets=greenlets,
            disabled=bool(conf.get('disabled')),
            workflow_name=workflow_name,
            resume=resume
        )
    else:
        base = task_class(
            conf['name'], sysdate, command=conf.get('command'),
            deps=conf.get('deps'), logdir=logdir,
            disabled=conf.get('disabled'),
            greenlets=greenlets,
            workflow_name=workflow_name,
            retry_count=retry_count,
            retry_interval=retry_interval,
            resume=resume
        )

    greenlets[conf['name']] = base
    return base


def sysdate_format(sysdate: datetime.datetime, f: str, *,
                   y: int = 0, m: int = 0, w: int = 0,
                   d: int = 0, h: int = 0) -> str:
    now = sysdate + relativedelta(years=y, months=m, weeks=w, days=d, hours=h)
    return dates.format_datetime(now, f)


def load_env() -> Dict[str, str]:
    envs = {}
    for k, v in os.environ.items():
        envs[f'ENV_{k}'] = v
    return envs


def load_config(conf_file: str, params: Dict[str, str],
                sysdate: Optional[datetime.datetime] = None) -> Dict[str, Any]:
    if sysdate is None:
        sysdate = datetime.datetime.now()
    
    try:
        with open(conf_file) as f:
            conf_str = f.read()
    except FileNotFoundError:
        raise FileNotFoundError(f"Config file '{conf_file}' not found.")
    except Exception as e:
        raise Exception(f"Error reading config file '{conf_file}': {e}")

    env = Environment(
        variable_start_string='${',
        variable_end_string='}')
    env.filters['sysdate'] = functools.partial(sysdate_format, sysdate)

    params.update(load_env())
    try:
        cf = env.from_string(conf_str).render(**params)
        conf = yaml.safe_load(cf)
    except Exception as e:
        raise Exception(f"Error parsing config file '{conf_file}': {e}")

    if conf is None:
        raise Exception(f"Config file '{conf_file}' is empty or invalid.")
    
    conf['_sysdate'] = sysdate
    return conf


def run(conf: Dict[str, Any], notify: bool = False) -> int:
    log = utils.get_log("Main-Thread")
    log.debug(f"Init Job...")
    task_name = conf.get('name', 'Unnamed')
    workflow_name = task_name
    recipients = conf.get('mailto')
    logdir = os.path.join(conf.get('logdir', f'log/{task_name}'),
                          conf['_sysdate'].strftime('%Y%m%d%H%M%S'))
    if not os.path.isdir(logdir):
        os.makedirs(logdir)

    resume = conf.get('resume', False)
    state_backend = conf.get('state_backend', 'file')
    state_file = os.path.join(logdir, 'task_state.json')
    
    if state_backend == 'redis':
        redis_host = conf.get('redis_host', 'localhost')
        redis_port = conf.get('redis_port', 6379)
        redis_db = conf.get('redis_db', 0)
        redis_password = conf.get('redis_password', None)
        
        state_manager.set_backend('redis', 
                               redis_host=redis_host,
                               redis_port=redis_port,
                               redis_db=redis_db,
                               redis_password=redis_password)
        
        log.info(f"Using Redis backend for state management: {redis_host}:{redis_port}/{redis_db}")
    else:
        state_manager.set_state_file(state_file)
        log.info(f"Using file backend for state management: {state_file}")

    if not resume:
        state_manager.clear_workflow_state(workflow_name)

    os.environ.update(conf.get('env', {}))
    log.info(f"Job '{task_name}' start, sysdate={conf['_sysdate']:%Y%m%d%H%M%S}, resume={resume}.")

    start = time.time()
    return_code = utils.EXIT_ERROR
    greenlets: Dict[str, Greenlet] = {}
    
    try:
        executor = conf.get('executor', 'local')
        if executor == 'local':
            task_class = Task
        elif executor == 'cluster':
            task_class = ClusterTask
        else:
            raise Exception(f"Unknown executor '{executor}'.")
        
        job = job_generator(conf, conf['_sysdate'].strftime('%Y%m%d%H%M%S'),
                            task_class, logdir, greenlets, workflow_name, resume)
        job.start()
        job.join()
        return_code = job.get()
    except gevent.exceptions.LoopExit:
        return_code = utils.EXIT_CANCEL
    except Exception:
        log.error(traceback.format_exc())
        return_code = utils.EXIT_ERROR
    end = time.time()
    
    log.info(f"Job '{task_name}' complete, exited ({return_code}), sysdate={conf['_sysdate']:%Y%m%d%H%M%S}, cost {end-start:.3f} seconds.")
    
    if return_code != utils.EXIT_COMPLETE and recipients and notify:
        msg = f"Job '{task_name}' exit with non-zero ({return_code}), sysdate={conf['_sysdate']:%Y%m%d%H%M%S}"
        utils.notice(common_conf['notify']['url'], msg, recipients)

    return return_code


def cron_schedule() -> None:
    import argparse
    
    parser = argparse.ArgumentParser(description='Task scheduler with cron-like scheduling')
    parser.add_argument(
        "-f", "--config", dest="conf",
        metavar="FILE", help="The config file location.", required=True)
    parser.add_argument(
        "-D", action="store_true", dest="daemon",
        help="Run as daemon.", default=False)
    parser.add_argument(
        "-a", "--var", action='append', dest="vars",
        help="Set parameters (KEY=VALUE format)")
    parser.add_argument(
        "-l", "--loglevel", dest="level",
        help="Set logging level.", default="DEBUG")
    parser.add_argument(
        "-r", "--resume", action="store_true", dest="resume",
        help="Resume from last failed task.", default=False)
    args = parser.parse_args()

    utils.LOGGING_CONF['level'] = args.level
    log = utils.get_log("Scheduler")
    
    try:
        params = dict(v.split('=', 1) for v in args.vars or [])
    except ValueError:
        parser.error("Invalid parameter format. Use KEY=VALUE format.")
    
    sysdate_opt = params.pop('sysdate', None)
    sysdate = None
    if sysdate_opt is not None:
        try:
            sysdate = datetime.datetime.strptime(sysdate_opt, '%Y%m%d%H%M%S')
        except ValueError:
            parser.error("Invalid sysdate format. Use YYYYMMDDHHMMSS format.")
    
    try:
        conf = load_config(args.conf, params, sysdate)
    except Exception as e:
        log.error(f"Failed to load config: {e}")
        sys.exit(1)

    conf['resume'] = args.resume

    if args.daemon:
        now = datetime.datetime.now()
        cron = croniter(conf['schedule'], now,
                        ret_type=datetime.datetime)

        log.info('Scheduler started.')
        try:
            for c in cron:
                while datetime.datetime.now() < c:
                    gevent.sleep(0.3)
                conf_interval = load_config(args.conf, params, c)
                conf_interval['resume'] = args.resume
                proc = Process(target=run, args=(conf_interval, ),
                               kwargs={'notify': True})
                proc.start()
                if not conf_interval.get('async', True):
                    proc.join()
        except KeyboardInterrupt:
            log.info('Scheduler stopped by user.')
    else:
        sys.exit(run(conf))


if __name__ == "__main__":
    cron_schedule()
