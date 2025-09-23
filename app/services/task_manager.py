import time
from typing import Dict, Optional

class TaskManager:
    def __init__(self):
        self.tasks: Dict[str, Dict] = {}
        self.task_timeout = 3600
    
    def create_task(self, task_id: str, initial_data: Dict):
        self.tasks[task_id] = {
            **initial_data,
            "created_at": time.time(),
            "updated_at": time.time(),
            "progress": 0,
            "status": "initializing"
        }
    
    def get_task(self, task_id: str) -> Optional[Dict]:
        self._cleanup_old_tasks()
        return self.tasks.get(task_id)
    
    def update_task(self, task_id: str, updates: Dict):
        if task_id in self.tasks:
            self.tasks[task_id].update(updates)
            self.tasks[task_id]["updated_at"] = time.time()
    
    def _cleanup_old_tasks(self):
        current_time = time.time()
        expired_tasks = [
            task_id for task_id, task in self.tasks.items()
            if current_time - task["updated_at"] > self.task_timeout
        ]
        for task_id in expired_tasks:
            del self.tasks[task_id]
    
    def cleanup(self):
        self.tasks.clear()