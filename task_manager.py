import time
from typing import Dict, Optional
from app.utils.logger import get_logger

logger = get_logger(__name__)

class TaskManager:
    def __init__(self):
        self.tasks: Dict[str, Dict] = {}
        self.task_timeout = 3600  # 1 hour
    
    def create_task(self, task_id: str, initial_data: Dict):
        """Create a new task"""
        self.tasks[task_id] = {
            **initial_data,
            "created_at": time.time(),
            "updated_at": time.time(),
            "progress": 0,
            "status": "initializing"
        }
        logger.info(f"Created task: {task_id}")
    
    def get_task(self, task_id: str) -> Optional[Dict]:
        """Get task by ID"""
        self._cleanup_old_tasks()
        return self.tasks.get(task_id)
    
    def update_task(self, task_id: str, updates: Dict):
        """Update task progress and status"""
        if task_id in self.tasks:
            self.tasks[task_id].update(updates)
            self.tasks[task_id]["updated_at"] = time.time()
            logger.debug(f"Updated task {task_id}: {updates}")
    
    def _cleanup_old_tasks(self):
        """Remove tasks older than timeout"""
        current_time = time.time()
        expired_tasks = [
            task_id for task_id, task in self.tasks.items()
            if current_time - task["updated_at"] > self.task_timeout
        ]
        
        for task_id in expired_tasks:
            del self.tasks[task_id]
            logger.info(f"Cleaned up expired task: {task_id}")
    
    def cleanup(self):
        """Cleanup all tasks"""
        self.tasks.clear()
        logger.info("Cleaned up all tasks")