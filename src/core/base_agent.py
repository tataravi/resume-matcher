import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from uuid import uuid4
from datetime import datetime

from .models import AgentState, AgentType, Task, AgentContext, AgentMessage


logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    def __init__(
        self,
        agent_id: Optional[str] = None,
        agent_type: AgentType = AgentType.ORCHESTRATOR,
        max_concurrent_tasks: int = 5
    ):
        self.agent_id = agent_id or str(uuid4())
        self.agent_type = agent_type
        self.state = AgentState.IDLE
        self.max_concurrent_tasks = max_concurrent_tasks
        self.current_tasks: Dict[str, Task] = {}
        self.message_queue: asyncio.Queue = asyncio.Queue()
        self.is_running = False
        self.logger = logger.getChild(f"{agent_type.value}_{self.agent_id}")
        
    async def start(self):
        """Start the agent's main processing loop."""
        self.is_running = True
        self.logger.info(f"Agent {self.agent_id} starting...")
        await self._main_loop()
        
    async def stop(self):
        """Stop the agent gracefully."""
        self.is_running = False
        self.state = AgentState.IDLE
        self.logger.info(f"Agent {self.agent_id} stopping...")
        
    async def _main_loop(self):
        """Main processing loop for the agent."""
        while self.is_running:
            try:
                # Process messages
                await self._process_messages()
                
                # Execute tasks
                await self._execute_tasks()
                
                # Small delay to prevent CPU spinning
                await asyncio.sleep(0.1)
                
            except Exception as e:
                self.logger.error(f"Error in main loop: {e}", exc_info=True)
                await asyncio.sleep(1)
                
    async def _process_messages(self):
        """Process incoming messages from the queue."""
        try:
            while not self.message_queue.empty():
                message = await asyncio.wait_for(
                    self.message_queue.get(), timeout=0.1
                )
                await self._handle_message(message)
        except asyncio.TimeoutError:
            pass
        except Exception as e:
            self.logger.error(f"Error processing messages: {e}", exc_info=True)
            
    async def _handle_message(self, message: AgentMessage):
        """Handle individual messages."""
        self.logger.debug(f"Received message: {message.message_type} from {message.sender}")
        
        if message.message_type == "task_assignment":
            task_data = message.content.get("task")
            if task_data:
                task = Task(**task_data)
                await self.assign_task(task)
        elif message.message_type == "task_cancellation":
            task_id = message.content.get("task_id")
            if task_id:
                await self.cancel_task(task_id)
        else:
            await self.handle_custom_message(message)
            
    async def handle_custom_message(self, message: AgentMessage):
        """Override this method to handle custom message types."""
        pass
        
    async def _execute_tasks(self):
        """Execute pending tasks."""
        if len(self.current_tasks) >= self.max_concurrent_tasks:
            return
            
        pending_tasks = [
            task for task in self.current_tasks.values() 
            if task.status.value == "pending"
        ]
        
        for task in pending_tasks[:self.max_concurrent_tasks - len(self.current_tasks)]:
            asyncio.create_task(self._execute_single_task(task))
            
    async def _execute_single_task(self, task: Task):
        """Execute a single task."""
        try:
            self.logger.info(f"Starting task {task.id}")
            task.status = "in_progress"
            task.agent_id = self.agent_id
            task.updated_at = datetime.utcnow()
            
            self.state = AgentState.PROCESSING
            
            result = await self.execute_task(task)
            
            task.output_data = result
            task.status = "completed"
            task.completed_at = datetime.utcnow()
            task.updated_at = datetime.utcnow()
            
            self.logger.info(f"Completed task {task.id}")
            
        except Exception as e:
            self.logger.error(f"Task {task.id} failed: {e}", exc_info=True)
            task.status = "failed"
            task.error_message = str(e)
            task.updated_at = datetime.utcnow()
            
            # Retry logic
            if task.retry_count < task.max_retries:
                task.retry_count += 1
                task.status = "pending"
                self.logger.info(f"Retrying task {task.id} (attempt {task.retry_count})")
            
        finally:
            # Update state if no more tasks are running
            active_tasks = [
                t for t in self.current_tasks.values() 
                if t.status.value == "in_progress"
            ]
            if not active_tasks:
                self.state = AgentState.IDLE
                
    @abstractmethod
    async def execute_task(self, task: Task) -> Dict[str, Any]:
        """Execute a specific task. Must be implemented by subclasses."""
        pass
        
    async def assign_task(self, task: Task):
        """Assign a task to this agent."""
        self.current_tasks[str(task.id)] = task
        self.logger.info(f"Task {task.id} assigned to agent {self.agent_id}")
        
    async def cancel_task(self, task_id: str):
        """Cancel a running task."""
        if task_id in self.current_tasks:
            task = self.current_tasks[task_id]
            task.status = "cancelled"
            task.updated_at = datetime.utcnow()
            self.logger.info(f"Task {task_id} cancelled")
            
    async def send_message(self, recipient: str, message_type: str, content: Dict[str, Any]):
        """Send a message to another agent."""
        message = AgentMessage(
            sender=self.agent_id,
            recipient=recipient,
            message_type=message_type,
            content=content
        )
        # In a real implementation, this would use a message broker
        self.logger.debug(f"Sending message to {recipient}: {message_type}")
        
    def get_status(self) -> Dict[str, Any]:
        """Get current agent status."""
        return {
            "agent_id": self.agent_id,
            "agent_type": self.agent_type.value,
            "state": self.state.value,
            "current_tasks": len(self.current_tasks),
            "max_concurrent_tasks": self.max_concurrent_tasks,
            "is_running": self.is_running
        }
        
    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a specific task."""
        if task_id in self.current_tasks:
            task = self.current_tasks[task_id]
            return {
                "id": str(task.id),
                "status": task.status.value,
                "created_at": task.created_at.isoformat(),
                "updated_at": task.updated_at.isoformat(),
                "retry_count": task.retry_count,
                "error_message": task.error_message
            }
        return None