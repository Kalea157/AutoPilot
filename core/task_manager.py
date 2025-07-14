"""
Liyana NEXUS v1 - Task Manager
Verwaltet Aufgaben und deren Ausführung
"""

import asyncio
import logging
import uuid
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from config import config

class TaskStatus(Enum):
    """Status einer Aufgabe"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class TaskPriority(Enum):
    """Priorität einer Aufgabe"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4

@dataclass
class Task:
    """Repräsentiert eine Aufgabe"""
    id: str
    type: str
    data: Dict[str, Any]
    priority: TaskPriority = TaskPriority.NORMAL
    status: TaskStatus = TaskStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3
    timeout: int = 300  # Sekunden

class TaskManager:
    """Verwaltet Aufgaben und deren Ausführung"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.tasks: Dict[str, Task] = {}
        self.task_queue: asyncio.PriorityQueue = asyncio.PriorityQueue()
        self.running_tasks: Dict[str, asyncio.Task] = {}
        self._running = False
        self._worker_task: Optional[asyncio.Task] = None
        
        # Task-Handler
        self.task_handlers: Dict[str, callable] = {}
        
        # Metriken
        self.metrics = {
            'total_tasks': 0,
            'completed_tasks': 0,
            'failed_tasks': 0,
            'pending_tasks': 0,
            'running_tasks': 0
        }
    
    async def initialize(self):
        """Initialisiert den Task Manager"""
        self.logger.info("Task Manager wird initialisiert...")
        self._running = True
        self._worker_task = asyncio.create_task(self._worker_loop())
        self.logger.info("Task Manager initialisiert")
    
    async def shutdown(self):
        """Beendet den Task Manager"""
        self.logger.info("Task Manager wird beendet...")
        self._running = False
        
        # Stoppe Worker
        if self._worker_task:
            self._worker_task.cancel()
            try:
                await self._worker_task
            except asyncio.CancelledError:
                pass
        
        # Warte auf laufende Tasks
        if self.running_tasks:
            await asyncio.gather(*self.running_tasks.values(), return_exceptions=True)
        
        self.logger.info("Task Manager beendet")
    
    async def create_task(self, task_type: str, task_data: Dict[str, Any], 
                         priority: TaskPriority = TaskPriority.NORMAL,
                         timeout: int = 300) -> str:
        """Erstellt eine neue Aufgabe"""
        task_id = str(uuid.uuid4())
        
        task = Task(
            id=task_id,
            type=task_type,
            data=task_data,
            priority=priority,
            timeout=timeout
        )
        
        self.tasks[task_id] = task
        await self.task_queue.put((priority.value, task_id))
        
        self.metrics['total_tasks'] += 1
        self.metrics['pending_tasks'] += 1
        
        self.logger.info(f"Task erstellt: {task_id} ({task_type})")
        return task_id
    
    async def get_task(self, task_id: str) -> Optional[Task]:
        """Gibt eine Aufgabe zurück"""
        return self.tasks.get(task_id)
    
    async def cancel_task(self, task_id: str) -> bool:
        """Bricht eine Aufgabe ab"""
        if task_id not in self.tasks:
            return False
        
        task = self.tasks[task_id]
        
        # Stoppe laufende Task
        if task_id in self.running_tasks:
            self.running_tasks[task_id].cancel()
            del self.running_tasks[task_id]
        
        task.status = TaskStatus.CANCELLED
        task.completed_at = datetime.now()
        
        self.logger.info(f"Task abgebrochen: {task_id}")
        return True
    
    async def register_task_handler(self, task_type: str, handler: callable):
        """Registriert einen Handler für einen Task-Typ"""
        self.task_handlers[task_type] = handler
        self.logger.info(f"Task Handler registriert für: {task_type}")
    
    async def _worker_loop(self):
        """Hauptschleife des Task Workers"""
        while self._running:
            try:
                # Warte auf neue Tasks
                priority, task_id = await asyncio.wait_for(
                    self.task_queue.get(), 
                    timeout=1.0
                )
                
                # Verarbeite Task
                await self._process_task(task_id)
                
            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Fehler im Task Worker: {e}")
    
    async def _process_task(self, task_id: str):
        """Verarbeitet eine Aufgabe"""
        if task_id not in self.tasks:
            return
        
        task = self.tasks[task_id]
        
        # Prüfe ob Task bereits abgebrochen wurde
        if task.status == TaskStatus.CANCELLED:
            return
        
        # Starte Task
        task.status = TaskStatus.RUNNING
        task.started_at = datetime.now()
        self.metrics['pending_tasks'] -= 1
        self.metrics['running_tasks'] += 1
        
        self.logger.info(f"Task gestartet: {task_id} ({task.type})")
        
        # Erstelle asyncio Task
        async_task = asyncio.create_task(self._execute_task(task))
        self.running_tasks[task_id] = async_task
        
        try:
            # Warte auf Task-Abschluss mit Timeout
            result = await asyncio.wait_for(async_task, timeout=task.timeout)
            
            # Task erfolgreich abgeschlossen
            task.status = TaskStatus.COMPLETED
            task.result = result
            task.completed_at = datetime.now()
            
            self.metrics['completed_tasks'] += 1
            self.logger.info(f"Task abgeschlossen: {task_id}")
            
        except asyncio.TimeoutError:
            # Task Timeout
            task.status = TaskStatus.FAILED
            task.error = "Task Timeout"
            task.completed_at = datetime.now()
            
            self.metrics['failed_tasks'] += 1
            self.logger.error(f"Task Timeout: {task_id}")
            
        except Exception as e:
            # Task Fehler
            task.status = TaskStatus.FAILED
            task.error = str(e)
            task.completed_at = datetime.now()
            
            self.metrics['failed_tasks'] += 1
            self.logger.error(f"Task Fehler: {task_id} - {e}")
            
        finally:
            # Cleanup
            self.metrics['running_tasks'] -= 1
            if task_id in self.running_tasks:
                del self.running_tasks[task_id]
    
    async def _execute_task(self, task: Task) -> Dict[str, Any]:
        """Führt eine Aufgabe aus"""
        # Suche nach Handler
        handler = self.task_handlers.get(task.type)
        if handler:
            return await handler(task.data)
        else:
            # Fallback: Standard-Task-Verarbeitung
            return await self._default_task_handler(task)
    
    async def _default_task_handler(self, task: Task) -> Dict[str, Any]:
        """Standard-Task-Handler"""
        return {
            'task_id': task.id,
            'task_type': task.type,
            'status': 'completed',
            'message': f'Task {task.type} wurde verarbeitet',
            'timestamp': datetime.now().isoformat()
        }
    
    async def get_queue_size(self) -> int:
        """Gibt die Anzahl der wartenden Tasks zurück"""
        return self.task_queue.qsize()
    
    async def get_running_tasks(self) -> List[str]:
        """Gibt die IDs der laufenden Tasks zurück"""
        return list(self.running_tasks.keys())
    
    async def get_task_metrics(self) -> Dict[str, Any]:
        """Gibt Task-Metriken zurück"""
        return {
            'metrics': self.metrics,
            'queue_size': await self.get_queue_size(),
            'running_tasks': len(self.running_tasks),
            'total_tasks': len(self.tasks)
        }
    
    async def cleanup_completed_tasks(self, max_age_hours: int = 24):
        """Bereinigt abgeschlossene Tasks"""
        cutoff_time = datetime.now().timestamp() - (max_age_hours * 3600)
        
        tasks_to_remove = []
        for task_id, task in self.tasks.items():
            if (task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED] and
                task.completed_at and task.completed_at.timestamp() < cutoff_time):
                tasks_to_remove.append(task_id)
        
        for task_id in tasks_to_remove:
            del self.tasks[task_id]
        
        if tasks_to_remove:
            self.logger.info(f"{len(tasks_to_remove)} alte Tasks bereinigt")