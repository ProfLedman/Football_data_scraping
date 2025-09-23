import time
from typing import Dict, Optional, List

class TaskManager:
    def __init__(self):
        self.tasks: Dict[str, Dict] = {}
        self.task_timeout = 3600  # 1 hour
    
    def create_task(self, task_id: str, initial_data: Dict):
        """Create a new task with required default fields"""
        self.tasks[task_id] = {
            "progress": 0,
            "status": "initializing",
            "message": "Task created",
            "created_at": time.time(),
            "updated_at": time.time(),
            **initial_data  # Allow initial_data to override defaults
        }
    
    def get_task(self, task_id: str) -> Optional[Dict]:
        """Get task by ID, cleaning up old tasks first"""
        self._cleanup_old_tasks()
        task = self.tasks.get(task_id)
        if task:
            # Return a copy to prevent accidental modification
            return task.copy()
        return None
    
    def update_task(self, task_id: str, updates: Dict):
        """Update task with new data and refresh timestamp"""
        if task_id in self.tasks:
            self.tasks[task_id].update(updates)
            self.tasks[task_id]["updated_at"] = time.time()
    
    def get_all_tasks(self) -> List[Dict]:
        """Get all active tasks (for debugging/monitoring)"""
        self._cleanup_old_tasks()
        return [
            {**task, "task_id": task_id} 
            for task_id, task in self.tasks.items()
        ]
    
    def _cleanup_old_tasks(self):
        """Remove tasks that haven't been updated within timeout"""
        current_time = time.time()
        expired_tasks = [
            task_id for task_id, task in self.tasks.items()
            if current_time - task.get("updated_at", 0) > self.task_timeout
        ]
        
        for task_id in expired_tasks:
            print(f"Cleaning up expired task: {task_id}")
            del self.tasks[task_id]
    
    def cleanup(self):
        """Clean up all tasks (called on shutdown)"""
        print(f"Cleaning up {len(self.tasks)} tasks")
        self.tasks.clear()