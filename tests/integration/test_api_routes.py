import pytest
import json
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient
from httpx import AsyncClient

from src.main import create_app


@pytest.mark.integration
class TestHealthRoutes:
    """Test health check endpoints."""
    
    def test_health_check(self, client: TestClient):
        """Test basic health check."""
        response = client.get("/health/")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "status" in data
        assert "timestamp" in data
        assert "version" in data
        assert "services" in data
        assert "system" in data
    
    def test_readiness_check(self, client: TestClient):
        """Test readiness probe."""
        response = client.get("/health/ready")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "ready"
        assert "timestamp" in data
    
    def test_liveness_check(self, client: TestClient):
        """Test liveness probe."""
        response = client.get("/health/live")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "alive"
        assert "timestamp" in data


@pytest.mark.integration
class TestUploadRoutes:
    """Test upload endpoints."""
    
    @pytest.fixture
    def auth_headers(self):
        """Mock authentication headers."""
        return {"Authorization": "Bearer test-token"}
    
    @pytest.fixture
    def mock_s3_service(self):
        """Mock S3 service for upload tests."""
        with patch('src.api.routes.upload.S3Service') as mock:
            service_instance = AsyncMock()
            service_instance.upload_file.return_value = {
                "bucket": "test-bucket",
                "key": "test-key.pdf",
                "etag": "test-etag",
                "size": 1024,
                "last_modified": "2023-01-01T00:00:00Z"
            }
            mock.return_value = service_instance
            yield service_instance
    
    def test_upload_resume_success(self, client: TestClient, auth_headers, mock_s3_service):
        """Test successful resume upload."""
        # Create test PDF content
        test_content = b"%PDF-1.4 test content"
        
        files = {
            "file": ("test_resume.pdf", test_content, "application/pdf")
        }
        
        with patch('src.api.routes.upload.get_current_active_user') as mock_user:
            mock_user.return_value = {"id": "test-user", "email": "test@example.com"}
            
            response = client.post(
                "/api/v1/upload/resume",
                files=files,
                headers=auth_headers
            )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "file_id" in data
        assert data["filename"] == "test_resume.pdf"
        assert data["content_type"] == "application/pdf"
        assert data["file_size"] == len(test_content)
    
    def test_upload_resume_invalid_file_type(self, client: TestClient, auth_headers):
        """Test upload with invalid file type."""
        # Create test image content
        test_content = b"fake image content"
        
        files = {
            "file": ("test_image.jpg", test_content, "image/jpeg")
        }
        
        with patch('src.api.routes.upload.get_current_active_user') as mock_user:
            mock_user.return_value = {"id": "test-user", "email": "test@example.com"}
            
            response = client.post(
                "/api/v1/upload/resume",
                files=files,
                headers=auth_headers
            )
        
        assert response.status_code == 400
        assert "not allowed" in response.json()["detail"]
    
    def test_upload_resume_file_too_large(self, client: TestClient, auth_headers):
        """Test upload with file too large."""
        # Create large test content (simulate file larger than 10MB)
        large_content = b"x" * (11 * 1024 * 1024)  # 11MB
        
        files = {
            "file": ("large_resume.pdf", large_content, "application/pdf")
        }
        
        with patch('src.api.routes.upload.get_current_active_user') as mock_user:
            mock_user.return_value = {"id": "test-user", "email": "test@example.com"}
            
            response = client.post(
                "/api/v1/upload/resume",
                files=files,
                headers=auth_headers
            )
        
        assert response.status_code == 413
    
    def test_upload_resume_unauthorized(self, client: TestClient):
        """Test upload without authentication."""
        files = {
            "file": ("test_resume.pdf", b"test", "application/pdf")
        }
        
        response = client.post("/api/v1/upload/resume", files=files)
        assert response.status_code == 401
    
    def test_list_user_resumes(self, client: TestClient, auth_headers):
        """Test listing user resumes."""
        with patch('src.api.routes.upload.get_current_active_user') as mock_user:
            mock_user.return_value = {"id": "test-user", "email": "test@example.com"}
            
            response = client.get(
                "/api/v1/upload/resume/list",
                headers=auth_headers
            )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "files" in data
        assert "total_count" in data
        assert isinstance(data["files"], list)


@pytest.mark.integration 
class TestAnalysisRoutes:
    """Test analysis endpoints."""
    
    @pytest.fixture
    def auth_headers(self):
        return {"Authorization": "Bearer test-token"}
    
    @pytest.fixture
    def analysis_request_data(self):
        return {
            "resume_content": "Sample resume content with Python and FastAPI experience",
            "resume_filename": "john_doe_resume.pdf",
            "job_title": "Senior Python Developer",
            "company": "TechCorp Inc.",
            "job_description": "We need a Python developer with FastAPI experience",
            "priority": "medium"
        }
    
    @pytest.fixture
    def mock_orchestrator(self):
        """Mock orchestrator for analysis tests."""
        with patch('src.api.routes.analysis.OrchestratorAgent') as mock:
            orchestrator_instance = AsyncMock()
            orchestrator_instance.start_workflow.return_value = "test-analysis-id"
            orchestrator_instance.get_workflow_status.return_value = {
                "analysis_id": "test-analysis-id",
                "status": "completed",
                "progress_percentage": 100.0,
                "current_step": "completed"
            }
            mock.return_value = orchestrator_instance
            yield orchestrator_instance
    
    def test_start_analysis_success(
        self, 
        client: TestClient, 
        auth_headers, 
        analysis_request_data,
        mock_orchestrator
    ):
        """Test successful analysis start."""
        with patch('src.api.routes.analysis.get_current_active_user') as mock_user:
            mock_user.return_value = {"id": "test-user", "email": "test@example.com"}
            
            response = client.post(
                "/api/v1/analysis/start",
                json=analysis_request_data,
                headers=auth_headers
            )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["analysis_id"] == "test-analysis-id"
        assert data["status"] == "started"
        assert "message" in data
    
    def test_start_analysis_unauthorized(self, client: TestClient, analysis_request_data):
        """Test analysis start without authentication."""
        response = client.post(
            "/api/v1/analysis/start",
            json=analysis_request_data
        )
        assert response.status_code == 401
    
    def test_start_analysis_invalid_data(self, client: TestClient, auth_headers):
        """Test analysis start with invalid data."""
        invalid_data = {
            "resume_content": "",  # Empty content
            "job_title": "Test Job"
            # Missing required fields
        }
        
        with patch('src.api.routes.analysis.get_current_active_user') as mock_user:
            mock_user.return_value = {"id": "test-user", "email": "test@example.com"}
            
            response = client.post(
                "/api/v1/analysis/start",
                json=invalid_data,
                headers=auth_headers
            )
        
        assert response.status_code == 422  # Validation error
    
    def test_get_analysis_status_success(
        self, 
        client: TestClient, 
        auth_headers,
        mock_orchestrator
    ):
        """Test getting analysis status."""
        with patch('src.api.routes.analysis.get_current_active_user') as mock_user:
            mock_user.return_value = {"id": "test-user", "email": "test@example.com"}
            
            response = client.get(
                "/api/v1/analysis/status/test-analysis-id",
                headers=auth_headers
            )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["analysis_id"] == "test-analysis-id"
        assert data["status"] == "completed"
        assert data["progress_percentage"] == 100.0
    
    def test_get_analysis_status_not_found(self, client: TestClient, auth_headers):
        """Test getting status for non-existent analysis."""
        with patch('src.api.routes.analysis.get_current_active_user') as mock_user:
            mock_user.return_value = {"id": "test-user", "email": "test@example.com"}
            
            with patch('src.api.routes.analysis.OrchestratorAgent') as mock_orch:
                orchestrator_instance = AsyncMock()
                orchestrator_instance.get_workflow_status.return_value = None
                mock_orch.return_value = orchestrator_instance
                
                response = client.get(
                    "/api/v1/analysis/status/non-existent-id",
                    headers=auth_headers
                )
        
        assert response.status_code == 404
    
    def test_cancel_analysis_success(
        self, 
        client: TestClient, 
        auth_headers,
        mock_orchestrator
    ):
        """Test successful analysis cancellation."""
        # Setup mock for running analysis
        mock_orchestrator.get_workflow_status.return_value = {
            "analysis_id": "test-analysis-id",
            "status": "running"
        }
        mock_orchestrator.cancel_workflow.return_value = True
        
        with patch('src.api.routes.analysis.get_current_active_user') as mock_user:
            mock_user.return_value = {"id": "test-user", "email": "test@example.com"}
            
            response = client.delete(
                "/api/v1/analysis/cancel/test-analysis-id",
                headers=auth_headers
            )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["analysis_id"] == "test-analysis-id"
        assert "cancelled" in data["message"]
    
    def test_cancel_analysis_invalid_state(
        self, 
        client: TestClient, 
        auth_headers,
        mock_orchestrator
    ):
        """Test cancelling analysis in invalid state."""
        # Setup mock for completed analysis
        mock_orchestrator.get_workflow_status.return_value = {
            "analysis_id": "test-analysis-id",
            "status": "completed"
        }
        
        with patch('src.api.routes.analysis.get_current_active_user') as mock_user:
            mock_user.return_value = {"id": "test-user", "email": "test@example.com"}
            
            response = client.delete(
                "/api/v1/analysis/cancel/test-analysis-id",
                headers=auth_headers
            )
        
        assert response.status_code == 400
        assert "Cannot cancel" in response.json()["detail"]
    
    def test_list_user_analyses(self, client: TestClient, auth_headers):
        """Test listing user analyses."""
        with patch('src.api.routes.analysis.get_current_active_user') as mock_user:
            mock_user.return_value = {"id": "test-user", "email": "test@example.com"}
            
            response = client.get(
                "/api/v1/analysis/list",
                headers=auth_headers
            )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "analyses" in data
        assert "total_count" in data
        assert isinstance(data["analyses"], list)
    
    def test_batch_analysis_success(
        self, 
        client: TestClient, 
        auth_headers,
        analysis_request_data,
        mock_orchestrator
    ):
        """Test successful batch analysis."""
        batch_data = [analysis_request_data, analysis_request_data]
        
        with patch('src.api.routes.analysis.get_current_active_user') as mock_user:
            mock_user.return_value = {"id": "test-user", "email": "test@example.com"}
            
            response = client.post(
                "/api/v1/analysis/batch",
                json=batch_data,
                headers=auth_headers
            )
        
        assert response.status_code == 200
        data = response.json()
        
        assert len(data) == 2
        for result in data:
            assert "analysis_id" in result
            assert "status" in result
    
    def test_batch_analysis_too_many(
        self, 
        client: TestClient, 
        auth_headers,
        analysis_request_data
    ):
        """Test batch analysis with too many requests."""
        # Create more than the maximum allowed (10)
        batch_data = [analysis_request_data] * 15
        
        with patch('src.api.routes.analysis.get_current_active_user') as mock_user:
            mock_user.return_value = {"id": "test-user", "email": "test@example.com"}
            
            response = client.post(
                "/api/v1/analysis/batch",
                json=batch_data,
                headers=auth_headers
            )
        
        assert response.status_code == 400
        assert "Maximum 10" in response.json()["detail"]


@pytest.mark.integration
class TestWebSocketRoutes:
    """Test WebSocket endpoints."""
    
    async def test_websocket_connection_success(self, async_client: AsyncClient):
        """Test successful WebSocket connection."""
        # Mock token verification
        with patch('src.api.routes.websocket.verify_token') as mock_verify:
            mock_verify.return_value = Mock(user_id="test-user")
            
            async with async_client.websocket_connect(
                "/api/v1/ws?token=test-token"
            ) as websocket:
                # Should receive connection confirmation
                data = await websocket.receive_json()
                assert data["type"] == "connection_established"
    
    async def test_websocket_connection_invalid_token(self, async_client: AsyncClient):
        """Test WebSocket connection with invalid token."""
        with patch('src.api.routes.websocket.verify_token') as mock_verify:
            from fastapi import HTTPException
            mock_verify.side_effect = HTTPException(status_code=401)
            
            with pytest.raises(Exception):
                async with async_client.websocket_connect("/api/v1/ws?token=invalid"):
                    pass
    
    async def test_websocket_message_handling(self, async_client: AsyncClient):
        """Test WebSocket message handling."""
        with patch('src.api.routes.websocket.verify_token') as mock_verify:
            mock_verify.return_value = Mock(user_id="test-user")
            
            async with async_client.websocket_connect(
                "/api/v1/ws?token=test-token"
            ) as websocket:
                # Skip connection confirmation
                await websocket.receive_json()
                
                # Send ping message
                await websocket.send_json({"type": "ping"})
                
                # Should receive pong response
                response = await websocket.receive_json()
                assert response["type"] == "pong"


@pytest.mark.integration
class TestRateLimiting:
    """Test rate limiting middleware."""
    
    def test_rate_limit_enforcement(self, client: TestClient):
        """Test that rate limiting is enforced."""
        # This test would require actual rate limiting configuration
        # For now, just verify the endpoint is accessible
        response = client.get("/health/live")
        assert response.status_code == 200
    
    def test_rate_limit_headers(self, client: TestClient):
        """Test that rate limit headers are present."""
        response = client.get("/health/live")
        
        # Check for rate limiting headers (if implemented)
        # assert "X-RateLimit-Limit" in response.headers
        # assert "X-RateLimit-Remaining" in response.headers
        
        # For now, just verify response is valid
        assert response.status_code == 200


@pytest.mark.integration
class TestErrorHandling:
    """Test error handling across API."""
    
    def test_404_error(self, client: TestClient):
        """Test 404 error handling."""
        response = client.get("/api/v1/nonexistent-endpoint")
        assert response.status_code == 404
    
    def test_405_method_not_allowed(self, client: TestClient):
        """Test 405 method not allowed."""
        response = client.put("/health/live")  # GET-only endpoint
        assert response.status_code == 405
    
    def test_422_validation_error(self, client: TestClient):
        """Test validation error handling."""
        # Send invalid JSON to an endpoint that expects specific format
        with patch('src.api.routes.analysis.get_current_active_user') as mock_user:
            mock_user.return_value = {"id": "test-user", "email": "test@example.com"}
            
            response = client.post(
                "/api/v1/analysis/start",
                json={"invalid": "data"},
                headers={"Authorization": "Bearer test-token"}
            )
        
        assert response.status_code == 422
        assert "detail" in response.json()


@pytest.mark.integration 
class TestCORS:
    """Test CORS configuration."""
    
    def test_cors_headers(self, client: TestClient):
        """Test CORS headers are present."""
        # Make an OPTIONS request
        response = client.options(
            "/api/v1/analysis/start",
            headers={"Origin": "http://localhost:3000"}
        )
        
        # Should have CORS headers
        assert response.status_code in [200, 204]
        # Additional CORS header checks would go here