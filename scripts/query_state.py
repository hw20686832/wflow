#!/usr/bin/env python3
import argparse
import json
import sys
from lib.redis_state_manager import RedisTaskStateManager
from lib import utils


def print_task_state(state):
    if not state:
        print("  No state found")
        return
    
    print(f"  Status: {state.get('status', 'unknown')}")
    print(f"  Return Code: {state.get('return_code', 'N/A')}")
    print(f"  Start Time: {state.get('start_time', 'N/A')}")
    print(f"  End Time: {state.get('end_time', 'N/A')}")
    if 'attempts' in state:
        print(f"  Attempts: {state['attempts']}")


def main():
    parser = argparse.ArgumentParser(description='Query task state from Redis')
    parser.add_argument(
        "--host", dest="host", default="localhost",
        help="Redis host", type=str)
    parser.add_argument(
        "--port", dest="port", default=6379,
        help="Redis port", type=int)
    parser.add_argument(
        "--db", dest="db", default=0,
        help="Redis database", type=int)
    parser.add_argument(
        "--password", dest="password", default=None,
        help="Redis password", type=str)
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    task_parser = subparsers.add_parser('task', help='Query specific task state')
    task_parser.add_argument('workflow', help='Workflow name')
    task_parser.add_argument('task', help='Task name')
    
    workflow_parser = subparsers.add_parser('workflow', help='Query workflow state')
    workflow_parser.add_argument('workflow', help='Workflow name')
    
    workflows_parser = subparsers.add_parser('workflows', help='List all workflows')
    
    stats_parser = subparsers.add_parser('stats', help='Show statistics')
    
    health_parser = subparsers.add_parser('health', help='Check Redis connection')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    redis_manager = RedisTaskStateManager()
    if not redis_manager.connect(args.host, args.port, args.db, args.password):
        print(f"Failed to connect to Redis at {args.host}:{args.port}/{args.db}")
        return 1
    
    if args.command == 'task':
        state = redis_manager.get_task_state(args.workflow, args.task)
        print(f"Task: {args.workflow}:{args.task}")
        print_task_state(state)
        
    elif args.command == 'workflow':
        print(f"Workflow: {args.workflow}")
        tasks = redis_manager.get_all_workflow_tasks(args.workflow)
        if not tasks:
            print("  No tasks found")
        else:
            for task_name, state in tasks.items():
                print(f"\n  Task: {task_name}")
                print_task_state(state)
                
    elif args.command == 'workflows':
        workflows = redis_manager.get_all_workflows()
        print("Workflows:")
        for workflow in workflows:
            print(f"  - {workflow}")
            
    elif args.command == 'stats':
        stats = redis_manager.get_statistics()
        print("Statistics:")
        print(f"  Total Tasks: {stats.get('total_tasks', 0)}")
        print(f"  Total Workflows: {stats.get('total_workflows', 0)}")
        print(f"  By Status:")
        for status, count in stats.get('by_status', {}).items():
            print(f"    {status}: {count}")
        print(f"  By Workflow:")
        for workflow, statuses in stats.get('by_workflow', {}).items():
            print(f"    {workflow}:")
            for status, count in statuses.items():
                print(f"      {status}: {count}")
                
    elif args.command == 'health':
        if redis_manager.health_check():
            print("Redis connection: OK")
            return 0
        else:
            print("Redis connection: FAILED")
            return 1
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
