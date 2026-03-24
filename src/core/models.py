from enum import Enum
from typing import Any, Dict, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field
from uuid import UUID, uuid4


class AgentState(str, Enum):
    IDLE = "idle"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class AgentType(str, Enum):
    PARSER = "parser"
    MATCHER = "matcher"
    FEEDBACK = "feedback"
    ORCHESTRATOR = "orchestrator"


class Priority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class TaskStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class AgentContext(BaseModel):
    task_id: UUID
    user_id: str
    session_id: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class AgentMessage(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    sender: str
    recipient: str
    content: Dict[str, Any]
    message_type: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class Task(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    type: str
    priority: Priority = Priority.MEDIUM
    status: TaskStatus = TaskStatus.PENDING
    input_data: Dict[str, Any] = Field(default_factory=dict)
    output_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    agent_id: Optional[str] = None
    context: AgentContext
    dependencies: List[UUID] = Field(default_factory=list)
    retry_count: int = 0
    max_retries: int = 3
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None


class ResumeData(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    file_path: str
    original_filename: str
    content: str
    parsed_data: Optional[Dict[str, Any]] = None
    user_id: str
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)


class JobDescription(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    title: str
    company: str
    description: str
    requirements: List[str] = Field(default_factory=list)
    parsed_data: Optional[Dict[str, Any]] = None
    user_id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)


class AnalysisResult(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    resume_id: UUID
    job_description_id: UUID
    match_score: float
    strengths: List[str] = Field(default_factory=list)
    weaknesses: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    detailed_analysis: Dict[str, Any] = Field(default_factory=dict)
    user_id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)