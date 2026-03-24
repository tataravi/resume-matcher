import pytest
import asyncio
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

from src.core.base_agent import BaseAgent
from src.core.models import AgentType, AgentState, Task, AgentContext, Priority


class TestableAgent(BaseAgent):
    """Testable implementation of BaseAgent."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.executed_tasks = []
    
    async def execute_task(self, task: Task):
        """Test implementation of execute_task."""
        self.executed_tasks.append(task)
        if task.input_data.get("should_fail"):
            raise ValueError("Test error")
        return {"result": "success", "task_id": str(task.id)}


@pytest.mark.unit
class TestBaseAgent:
    """Test suite for BaseAgent class."""
    
    @pytest.fixture
    def agent(self):
        """Create a test agent."""
        return TestableAgent(
            agent_id="test-agent",
            agent_type=AgentType.PARSER,
            max_concurrent_tasks=3
        )
    
    @pytest.fixture
    def sample_context(self):
        """Create sample agent context."""
        return AgentContext(
            task_id=uuid4(),
            user_id="test-user",
            session_id="test-session"
        )
    
    @pytest.fixture
    def sample_task(self, sample_context):
        """Create sample task."""
        return Task(
            type="test_task",
            priority=Priority.MEDIUM,
            input_data={"test": "data"},
            context=sample_context
        )
    
    def test_agent_initialization(self, agent):
        """Test agent initialization."""
        assert agent.agent_id == "test-agent"
        assert agent.agent_type == AgentType.PARSER
        assert agent.state == AgentState.IDLE
        assert agent.max_concurrent_tasks == 3
        assert len(agent.current_tasks) == 0
        assert not agent.is_running
    
    def test_agent_initialization_with_defaults(self):
        """Test agent initialization with default values."""
        agent = TestableAgent()
        assert agent.agent_id is not None
        assert agent.agent_type == AgentType.ORCHESTRATOR
        assert agent.max_concurrent_tasks == 5
    
    async def test_assign_task(self, agent, sample_task):
        """Test task assignment."""
        await agent.assign_task(sample_task)
        
        assert str(sample_task.id) in agent.current_tasks
        assert agent.current_tasks[str(sample_task.id)] == sample_task
    
    async def test_cancel_task(self, agent, sample_task):
        """Test task cancellation."""
        # Assign task first
        await agent.assign_task(sample_task)
        
        # Cancel task
        await agent.cancel_task(str(sample_task.id))
        
        # Check task status
        task = agent.current_tasks[str(sample_task.id)]
        assert task.status.value == "cancelled"
    
    async def test_cancel_nonexistent_task(self, agent):
        """Test cancelling a task that doesn't exist."""
        # Should not raise an error
        await agent.cancel_task("non-existent-task-id")
    
    def test_get_status(self, agent):
        """Test getting agent status."""
        status = agent.get_status()
        
        expected_keys = [
            "agent_id", "agent_type", "state", "current_tasks",
            "max_concurrent_tasks", "is_running"
        ]
        
        for key in expected_keys:
            assert key in status
        
        assert status["agent_id"] == "test-agent"
        assert status["agent_type"] == "parser"
        assert status["state"] == "idle"
        assert status["current_tasks"] == 0
        assert status["is_running"] is False
    
    def test_get_task_status_existing(self, agent, sample_task):
        """Test getting status of existing task."""
        # Add task to current tasks
        agent.current_tasks[str(sample_task.id)] = sample_task
        
        status = agent.get_task_status(str(sample_task.id))
        
        assert status is not None
        assert status["id"] == str(sample_task.id)
        assert "status" in status
        assert "created_at" in status
        assert "updated_at" in status
    
    def test_get_task_status_nonexistent(self, agent):
        """Test getting status of non-existent task."""
        status = agent.get_task_status("non-existent-task-id")
        assert status is None
    
    async def test_execute_single_task_success(self, agent, sample_task):
        """Test successful task execution."""
        # Assign task
        await agent.assign_task(sample_task)
        
        # Execute task
        await agent._execute_single_task(sample_task)
        
        # Check task was executed
        assert len(agent.executed_tasks) == 1
        assert agent.executed_tasks[0] == sample_task
        
        # Check task status
        assert sample_task.status.value == "completed"
        assert sample_task.output_data is not None
        assert sample_task.completed_at is not None
    
    async def test_execute_single_task_failure(self, agent, sample_context):
        """Test task execution failure."""
        # Create task that will fail
        failing_task = Task(
            type="test_task",
            priority=Priority.MEDIUM,
            input_data={"should_fail": True},
            context=sample_context
        )
        
        # Assign and execute task
        await agent.assign_task(failing_task)
        await agent._execute_single_task(failing_task)
        
        # Check task status
        assert failing_task.status.value == "failed"
        assert failing_task.error_message == "Test error"
        assert failing_task.output_data is None
    
    async def test_execute_single_task_retry(self, agent, sample_context):
        """Test task retry mechanism."""
        # Create task that will fail
        failing_task = Task(
            type="test_task",
            priority=Priority.MEDIUM,
            input_data={"should_fail": True},
            context=sample_context,
            max_retries=2
        )
        
        # Execute task (will fail and retry)
        await agent._execute_single_task(failing_task)
        
        # Check retry count
        assert failing_task.retry_count == 1
        assert failing_task.status.value == "pending"  # Should be retried
    
    async def test_message_handling(self, agent):
        """Test message handling."""
        # This is a basic test since message handling is mostly abstract
        # In a real implementation, you'd test specific message types
        
        # Test that the agent can be started and stopped
        assert not agent.is_running
        
        # Start agent in background
        start_task = asyncio.create_task(agent.start())
        
        # Wait a bit for agent to start
        await asyncio.sleep(0.1)
        assert agent.is_running
        
        # Stop agent
        await agent.stop()
        assert not agent.is_running
        
        # Cancel the start task
        start_task.cancel()
        try:
            await start_task
        except asyncio.CancelledError:
            pass
    
    async def test_concurrent_task_limit(self, agent, sample_context):
        """Test that agent respects concurrent task limit."""
        # Create multiple tasks
        tasks = []
        for i in range(5):  # More than max_concurrent_tasks (3)
            task = Task(
                type="test_task",
                priority=Priority.MEDIUM,
                input_data={"task_num": i},
                context=sample_context
            )
            tasks.append(task)
            await agent.assign_task(task)
        
        # All tasks should be assigned but not necessarily executed
        assert len(agent.current_tasks) == 5
    
    async def test_state_transitions(self, agent, sample_task):
        """Test agent state transitions."""
        # Initially idle
        assert agent.state == AgentState.IDLE
        
        # Assign and execute task
        await agent.assign_task(sample_task)
        await agent._execute_single_task(sample_task)
        
        # Should be back to idle after task completion
        assert agent.state == AgentState.IDLE
    
    def test_agent_logger_creation(self, agent):
        """Test that agent creates a proper logger."""
        assert agent.logger is not None
        assert "parser_test-agent" in agent.logger.name


@pytest.mark.unit 
class TestAgentCommunication:
    """Test agent communication features."""
    
    @pytest.fixture
    def agent(self):
        return TestableAgent(agent_id="test-agent")
    
    async def test_send_message(self, agent):
        """Test sending messages to other agents."""
        # This is a basic test since real message sending would require a message broker
        await agent.send_message(
            recipient="other-agent",
            message_type="test_message",
            content={"data": "test"}
        )
        # No exception should be raised
    
    async def test_handle_custom_message(self, agent):
        """Test custom message handling."""
        from src.core.models import AgentMessage
        
        message = AgentMessage(
            sender="other-agent",
            recipient=agent.agent_id,
            message_type="custom_message",
            content={"custom": "data"}
        )
        
        # Should not raise an exception (default implementation is empty)
        await agent.handle_custom_message(message)


@pytest.mark.unit
class TestTaskManagement:
    """Test task management functionality."""
    
    @pytest.fixture
    def agent(self):
        return TestableAgent(agent_id="test-agent")
    
    async def test_task_lifecycle(self, agent, sample_context):
        """Test complete task lifecycle."""
        # Create task
        task = Task(
            type="test_task",
            priority=Priority.HIGH,
            input_data={"lifecycle": "test"},
            context=sample_context
        )
        
        # Initial state
        assert task.status.value == "pending"
        assert task.agent_id is None
        assert task.retry_count == 0
        
        # Assign task
        await agent.assign_task(task)
        
        # Execute task
        await agent._execute_single_task(task)
        
        # Final state
        assert task.status.value == "completed"
        assert task.agent_id == agent.agent_id
        assert task.output_data is not None
        assert task.completed_at is not None
    
    async def test_task_priority_handling(self, agent, sample_context):
        """Test that tasks can have different priorities."""
        priorities = [Priority.LOW, Priority.MEDIUM, Priority.HIGH, Priority.URGENT]
        
        for priority in priorities:
            task = Task(
                type="test_task",
                priority=priority,
                input_data={"priority": priority.value},
                context=sample_context
            )
            
            await agent.assign_task(task)
            assert task.priority == priority