#!/usr/bin/env python3
import socket
import subprocess
from typing import Tuple, List

import celery
from celery.bin import worker
from lib import utils
from config.loader import get_config


def load_redis_config() -> dict:
    config = get_config()
    redis_config = config.get('redis', {})
    return {
        'host': redis_config.get('host', 'localhost'),
        'port': redis_config.get('port', 6379),
        'db': redis_config.get('db', 0),
        'password': redis_config.get('password', '')
    }


class CeleryConf:
    def __init__(self, redis_config: dict):
        self.BROKER_URL = f"redis://{redis_config['host']}:{redis_config['port']}/{redis_config['db']}"
        if redis_config.get('password'):
            self.BROKER_URL = f"redis://:{redis_config['password']}@{redis_config['host']}:{redis_config['port']}/{redis_config['db']}"
        self.CELERY_RESULT_BACKEND = f"redis://{redis_config['host']}:{redis_config['port']}/{redis_config['db']}"
        self.CELERY_TASK_RESULT_EXPIRES = 180


app = celery.Celery('executor')
app.config_from_object(CeleryConf(load_redis_config()))


@app.task
def work(command: List[str], logfile: str) -> int:
    try:
        with open(logfile, "a") as f:
            proc = subprocess.Popen(
                command,
                stdout=f,
                stderr=subprocess.STDOUT,
                shell=False
            )
        rs = proc.wait()
    except Exception:
        rs = utils.EXIT_ERROR

    return rs


def start() -> None:
    import argparse
    
    parser = argparse.ArgumentParser(description='Celery executor for task scheduling')
    parser.add_argument(
        "-s", "--seq", dest="seq", type=int,
        help="Set the node seq number start to 1.", default=1)
    parser.add_argument(
        "-n", "--node", dest="nodename",
        help="Set node name.", default=socket.gethostname())
    parser.add_argument(
        "-c", "--concurrency", dest="concurrency", type=int,
        help="Set concurrency number for prefork.", default=4)
    parser.add_argument(
        "-l", "--loglevel", dest="level",
        help="Set logging level.", default="INFO")
    args = parser.parse_args()
    
    task = worker.worker(app=app)
    opt = {
        'hostname': f"celery@executor_{args.nodename}_{args.seq}",
        'concurrency': args.concurrency,
        'loglevel': args.level,
        'traceback': True,
    }
    task.run(**opt)


if __name__ == '__main__':
    start()
