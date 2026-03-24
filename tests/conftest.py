import pytest
import asyncio
import os
from typing import Generator, AsyncGenerator
from unittest.mock import Mock, AsyncMock
from httpx import AsyncClient
from fastapi.testclient import TestClient

from src.main import create_app
from src.config import settings
from src.services.llm_service import LLMService
from src.services.s3_service import S3Service
from src.services.dynamodb_service import DynamoDBService
from src.services.sqs_service import SQSService
from src.agents import ParserAgent, MatcherAgent, FeedbackAgent, OrchestratorAgent


# Pytest configuration
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line("markers", "unit: Unit tests")
    config.addinivalue_line("markers", "integration: Integration tests")
    config.addinivalue_line("markers", "performance: Performance tests")
    config.addinivalue_line("markers", "slow: Slow running tests")


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def test_settings():
    """Test settings configuration."""
    # Override settings for testing
    settings.debug = True
    settings.database_url = "postgresql://test:test@localhost:5432/test_db"
    settings.redis_url = "redis://localhost:6379/1"
    settings.deepseek_api_key = "test-api-key"
    settings.aws_access_key_id = "test-access-key"
    settings.aws_secret_access_key = "test-secret-key"
    settings.secret_key = "test-secret-key"
    
    return settings


@pytest.fixture
def app(test_settings):
    """Create FastAPI test application."""
    return create_app()


@pytest.fixture
def client(app) -> TestClient:
    """Create test client."""
    return TestClient(app)


@pytest.fixture
async def async_client(app) -> AsyncGenerator[AsyncClient, None]:
    """Create async test client."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


# Mock service fixtures
@pytest.fixture
def mock_llm_service():
    """Mock LLM service."""
    service = Mock(spec=LLMService)
    service.generate_completion = AsyncMock(return_value="Test LLM response")
    service.generate_structured_completion = AsyncMock(return_value={
        "test": "structured response"
    })
    service.batch_generate_completions = AsyncMock(return_value=[
        "Response 1", "Response 2"
    ])
    service.get_metrics = Mock(return_value={
        "total_requests": 10,
        "successful_requests": 9,
        "failed_requests": 1,
        "cache_hits": 5
    })
    return service


@pytest.fixture
def mock_s3_service():
    """Mock S3 service."""
    service = Mock(spec=S3Service)
    service.upload_file = AsyncMock(return_value={
        "bucket": "test-bucket",
        "key": "test-key",
        "etag": "test-etag",
        "size": 1024
    })
    service.download_file = AsyncMock(return_value=b"test file content")
    service.delete_file = AsyncMock(return_value=True)
    service.file_exists = AsyncMock(return_value=True)
    service.list_files = AsyncMock(return_value=[
        {"key": "file1.pdf", "size": 1024},
        {"key": "file2.pdf", "size": 2048}
    ])
    service.generate_presigned_url = AsyncMock(return_value="https://presigned-url.com")
    return service


@pytest.fixture
def mock_dynamodb_service():
    """Mock DynamoDB service."""
    service = Mock(spec=DynamoDBService)
    service.put_item = AsyncMock(return_value={"operation": "put_item"})
    service.get_item = AsyncMock(return_value={"id": "test-id", "data": "test"})
    service.update_item = AsyncMock(return_value={"operation": "update_item"})
    service.delete_item = AsyncMock(return_value={"operation": "delete_item"})
    service.query_items = AsyncMock(return_value={
        "items": [{"id": "1"}, {"id": "2"}],
        "count": 2
    })
    service.scan_items = AsyncMock(return_value={
        "items": [{"id": "1"}, {"id": "2"}],
        "count": 2
    })
    return service


@pytest.fixture
def mock_sqs_service():
    """Mock SQS service."""
    service = Mock(spec=SQSService)
    service.send_message = AsyncMock(return_value={
        "message_id": "test-message-id",
        "md5_of_body": "test-md5"
    })
    service.receive_messages = AsyncMock(return_value=[
        {
            "message_id": "test-message-id",
            "receipt_handle": "test-receipt-handle",
            "body": {"test": "message"}
        }
    ])
    service.delete_message = AsyncMock(return_value=True)
    service.get_queue_attributes = AsyncMock(return_value={
        "ApproximateNumberOfMessages": 5
    })
    return service


# Agent fixtures
@pytest.fixture
def mock_parser_agent(mock_llm_service):
    """Mock parser agent."""
    agent = Mock(spec=ParserAgent)
    agent.execute_task = AsyncMock(return_value={
        "parsed_data": {
            "emails": ["test@example.com"],
            "phones": ["+1234567890"],
            "skills": ["Python", "FastAPI"]
        }
    })
    return agent


@pytest.fixture
def mock_matcher_agent(mock_llm_service):
    """Mock matcher agent."""
    agent = Mock(spec=MatcherAgent)
    agent.execute_task = AsyncMock(return_value={
        "analysis_result": {
            "match_score": 85.5,
            "strengths": ["Strong technical skills"],
            "weaknesses": ["Limited experience"],
            "recommendations": ["Highlight projects"]
        }
    })
    return agent


@pytest.fixture
def mock_feedback_agent(mock_llm_service):
    """Mock feedback agent."""
    agent = Mock(spec=FeedbackAgent)
    agent.execute_task = AsyncMock(return_value={
        "feedback_result": {
            "overall_feedback": "Good match with room for improvement",
            "improvement_areas": ["Skills alignment"],
            "actionable_steps": ["Add relevant keywords"]
        }
    })
    return agent


@pytest.fixture
def mock_orchestrator_agent(mock_parser_agent, mock_matcher_agent, mock_feedback_agent):
    """Mock orchestrator agent."""
    agent = Mock(spec=OrchestratorAgent)
    agent.start_workflow = AsyncMock(return_value="test-workflow-id")
    agent.get_workflow_status = Mock(return_value={
        "workflow_id": "test-workflow-id",
        "status": "completed",
        "progress_percentage": 100.0
    })
    agent.cancel_workflow = AsyncMock(return_value=True)
    return agent


# Test data fixtures
@pytest.fixture
def sample_resume_text():
    """Sample resume text for testing."""
    return """
    John Doe
    Software Engineer
    john.doe@example.com
    +1-555-123-4567
    
    EXPERIENCE
    Senior Software Engineer at TechCorp (2020-2023)
    - Developed web applications using Python and FastAPI
    - Implemented microservices architecture
    - Led team of 5 developers
    
    Software Engineer at StartupXYZ (2018-2020)
    - Built REST APIs using Django
    - Worked with PostgreSQL and Redis
    - Implemented CI/CD pipelines
    
    EDUCATION
    Bachelor of Science in Computer Science
    University of Technology (2014-2018)
    
    SKILLS
    Python, FastAPI, Django, PostgreSQL, Redis, Docker, AWS, Git
    """


@pytest.fixture
def sample_job_description():
    """Sample job description for testing."""
    return {
        "title": "Senior Python Developer",
        "company": "TechCompany Inc.",
        "description": """
        We are looking for a Senior Python Developer to join our team.
        
        Requirements:
        - 5+ years of Python experience
        - Experience with FastAPI or Django
        - Knowledge of databases (PostgreSQL preferred)
        - Experience with cloud platforms (AWS)
        - Strong problem-solving skills
        
        Responsibilities:
        - Design and develop web applications
        - Write clean, maintainable code
        - Collaborate with cross-functional teams
        - Mentor junior developers
        """
    }


@pytest.fixture
def sample_task_data():
    """Sample task data for testing."""
    return {
        "type": "full_analysis",
        "resume_content": "Sample resume content",
        "resume_filename": "john_doe_resume.pdf",
        "job_title": "Senior Python Developer",
        "company": "TechCompany Inc.",
        "job_description": "Sample job description"
    }


@pytest.fixture
def sample_analysis_result():
    """Sample analysis result for testing."""
    return {
        "workflow_id": "test-workflow-id",
        "status": "completed",
        "results": {
            "resume_data": {
                "emails": ["john.doe@example.com"],
                "phones": ["+1-555-123-4567"],
                "skills": ["Python", "FastAPI", "Django"]
            },
            "job_data": {
                "title": "Senior Python Developer",
                "company": "TechCompany Inc.",
                "required_skills": ["Python", "FastAPI", "PostgreSQL"]
            },
            "analysis_result": {
                "match_score": 85.5,
                "strengths": ["Strong Python experience", "Relevant framework knowledge"],
                "weaknesses": ["Limited cloud experience"],
                "recommendations": ["Highlight AWS projects", "Emphasize leadership experience"]
            },
            "feedback_result": {
                "overall_feedback": "Strong candidate with good technical fit",
                "improvement_areas": ["Cloud experience", "Leadership details"],
                "actionable_steps": ["Add AWS certifications", "Quantify team leadership impact"]
            }
        }
    }


# Database fixtures (for integration tests)
@pytest.fixture
async def db_session():
    """Database session for integration tests."""
    # This would create a test database session
    # Implementation depends on your actual database setup
    pass


# Authentication fixtures
@pytest.fixture
def mock_user():
    """Mock user for testing."""
    return {
        "id": "test-user-id",
        "email": "test@example.com",
        "is_active": True
    }


@pytest.fixture
def auth_headers(mock_user):
    """Authentication headers for testing."""
    # This would generate test JWT tokens
    return {
        "Authorization": "Bearer test-jwt-token"
    }


# Performance test fixtures
@pytest.fixture
def benchmark_settings():
    """Settings for benchmark tests."""
    return {
        "max_response_time": 1.0,  # seconds
        "max_memory_usage": 100,   # MB
        "max_cpu_usage": 80        # percentage
    }


# Cleanup fixtures
@pytest.fixture(autouse=True)
def cleanup_test_files():
    """Cleanup test files after each test."""
    yield
    # Cleanup any test files created during testing
    test_files = ["test_resume.pdf", "test_output.json"]
    for file in test_files:
        if os.path.exists(file):
            os.remove(file)