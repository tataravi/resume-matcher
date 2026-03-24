# API Documentation

This document provides comprehensive API documentation for the Resume Analyzer service.

## Base URL

- **Development**: `http://localhost:8000`
- **Staging**: `https://staging-api.resume-analyzer.com`
- **Production**: `https://api.resume-analyzer.com`

## Authentication

All API endpoints (except health checks) require authentication using JWT tokens.

### Getting a Token

```bash
POST /auth/token
Content-Type: application/json

{
  "username": "your_username",
  "password": "your_password"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

### Using Tokens

Include the token in the Authorization header:

```bash
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

## Rate Limiting

API requests are rate limited:

- **Standard users**: 100 requests per minute
- **Premium users**: 1000 requests per minute

Rate limit headers are included in all responses:

```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1640995200
```

## Error Handling

The API uses conventional HTTP response codes and returns error details in JSON format.

### Error Response Format

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid input data",
    "details": [
      {
        "field": "resume_content",
        "message": "Field is required"
      }
    ]
  },
  "request_id": "req_1234567890"
}
```

### HTTP Status Codes

- `200` - OK
- `201` - Created
- `400` - Bad Request
- `401` - Unauthorized
- `403` - Forbidden
- `404` - Not Found
- `413` - Payload Too Large
- `422` - Validation Error
- `429` - Rate Limit Exceeded
- `500` - Internal Server Error

## Health Endpoints

### Basic Health Check

```bash
GET /health/
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2023-12-01T10:00:00Z",
  "version": "0.1.0",
  "environment": "production",
  "services": {
    "database": {"status": "healthy", "response_time_ms": 5.2},
    "redis": {"status": "healthy", "response_time_ms": 1.8},
    "claude_api": {"status": "healthy", "response_time_ms": 150.0}
  },
  "system": {
    "cpu_usage_percent": 45.2,
    "memory_usage_percent": 67.8,
    "disk_usage_percent": 23.1
  }
}
```

### Readiness Check

```bash
GET /health/ready
```

**Response:**
```json
{
  "status": "ready",
  "timestamp": "2023-12-01T10:00:00Z"
}
```

### Liveness Check

```bash
GET /health/live
```

**Response:**
```json
{
  "status": "alive",
  "timestamp": "2023-12-01T10:00:00Z"
}
```

## Upload Endpoints

### Upload Resume

Upload a resume file for analysis.

```bash
POST /api/v1/upload/resume
Authorization: Bearer {token}
Content-Type: multipart/form-data

file: <resume_file>
```

**Supported File Types:**
- PDF (`.pdf`)
- Microsoft Word (`.doc`, `.docx`)
- Plain Text (`.txt`)

**File Size Limit:** 10MB

**Response:**
```json
{
  "file_id": "123e4567-e89b-12d3-a456-426614174000",
  "filename": "john_doe_resume.pdf",
  "file_path": "resumes/user123/123e4567-e89b-12d3-a456-426614174000.pdf",
  "file_size": 245760,
  "upload_timestamp": "2023-12-01T10:00:00Z",
  "content_type": "application/pdf"
}
```

### List User Resumes

```bash
GET /api/v1/upload/resume/list?limit=10&offset=0
Authorization: Bearer {token}
```

**Query Parameters:**
- `limit` (optional): Number of results to return (default: 10, max: 100)
- `offset` (optional): Number of results to skip (default: 0)

**Response:**
```json
{
  "files": [
    {
      "file_id": "123e4567-e89b-12d3-a456-426614174000",
      "filename": "john_doe_resume.pdf",
      "file_path": "resumes/user123/123e4567-e89b-12d3-a456-426614174000.pdf",
      "file_size": 245760,
      "upload_timestamp": "2023-12-01T10:00:00Z",
      "content_type": "application/pdf"
    }
  ],
  "total_count": 1
}
```

### Delete Resume

```bash
DELETE /api/v1/upload/resume/{file_id}
Authorization: Bearer {token}
```

**Response:**
```json
{
  "message": "File deleted successfully",
  "file_id": "123e4567-e89b-12d3-a456-426614174000"
}
```

### Download Resume

Generate a presigned URL for downloading a resume.

```bash
GET /api/v1/upload/resume/{file_id}/download
Authorization: Bearer {token}
```

**Response:**
```json
{
  "download_url": "https://s3.amazonaws.com/bucket/path?AWSAccessKeyId=...",
  "expires_in": 3600
}
```

## Analysis Endpoints

### Start Analysis

Start a new resume analysis workflow.

```bash
POST /api/v1/analysis/start
Authorization: Bearer {token}
Content-Type: application/json

{
  "resume_content": "John Doe\nSoftware Engineer\n...",
  "resume_filename": "john_doe_resume.pdf",
  "job_title": "Senior Python Developer",
  "company": "TechCorp Inc.",
  "job_description": "We are looking for a Senior Python Developer...",
  "priority": "medium"
}
```

**Request Fields:**
- `resume_content` (string, required): Resume text content
- `resume_filename` (string, required): Original filename
- `job_title` (string, required): Target job title
- `company` (string, required): Company name
- `job_description` (string, required): Job description text
- `priority` (string, optional): Priority level (`low`, `medium`, `high`, `urgent`)

**Response:**
```json
{
  "analysis_id": "analysis_456e7890-f12a-34b5-c678-90def1234567",
  "status": "started",
  "message": "Analysis workflow started successfully",
  "estimated_completion_time": "2023-12-01T10:05:00Z"
}
```

### Get Analysis Status

```bash
GET /api/v1/analysis/status/{analysis_id}
Authorization: Bearer {token}
```

**Response:**
```json
{
  "analysis_id": "analysis_456e7890-f12a-34b5-c678-90def1234567",
  "status": "completed",
  "current_step": "completed",
  "steps_completed": ["parsing", "job_parsing", "matching", "feedback"],
  "progress_percentage": 100.0,
  "start_time": "2023-12-01T10:00:00Z",
  "estimated_completion": null,
  "error_message": null
}
```

**Status Values:**
- `pending`: Analysis is queued
- `running`: Analysis is in progress
- `completed`: Analysis finished successfully
- `failed`: Analysis failed
- `cancelled`: Analysis was cancelled

### Get Analysis Result

Retrieve the completed analysis result.

```bash
GET /api/v1/analysis/result/{analysis_id}
Authorization: Bearer {token}
```

**Response:**
```json
{
  "analysis_id": "analysis_456e7890-f12a-34b5-c678-90def1234567",
  "status": "completed",
  "results": {
    "resume_data": {
      "emails": ["john.doe@example.com"],
      "phones": ["+1-555-123-4567"],
      "detected_skills": ["Python", "FastAPI", "PostgreSQL"],
      "llm_extracted": {
        "name": "John Doe",
        "summary": "Experienced software engineer...",
        "experience": [...],
        "education": [...],
        "skills": [...]
      }
    },
    "job_data": {
      "title": "Senior Python Developer",
      "company": "TechCorp Inc.",
      "llm_extracted": {
        "required_skills": ["Python", "FastAPI", "PostgreSQL"],
        "preferred_skills": ["AWS", "Docker"],
        "experience_level": "5+ years",
        "responsibilities": [...]
      }
    },
    "analysis_result": {
      "match_score": 85.5,
      "skill_match_score": 90.2,
      "experience_match_score": 82.1,
      "strengths": [
        "Strong Python programming experience",
        "Relevant framework knowledge (FastAPI)",
        "Database experience matches requirements"
      ],
      "weaknesses": [
        "Limited cloud platform experience",
        "No Docker mentioned in resume"
      ],
      "recommendations": [
        "Highlight any cloud projects or certifications",
        "Mention containerization experience if applicable"
      ],
      "detailed_analysis": "...",
      "analyzed_at": "2023-12-01T10:02:30Z"
    },
    "feedback_result": {
      "overall_feedback": "Strong candidate with excellent technical alignment...",
      "improvement_areas": [
        {
          "area": "Cloud Experience",
          "priority": "medium",
          "description": "Consider highlighting cloud platform experience",
          "impact": "Would strengthen application for this role"
        }
      ],
      "actionable_steps": [
        "Add AWS certifications if available",
        "Quantify team leadership experience",
        "Include specific project metrics"
      ],
      "priority_recommendations": [
        {
          "recommendation": "Emphasize FastAPI experience",
          "priority": "high",
          "impact": "Direct match with job requirements"
        }
      ]
    }
  },
  "execution_summary": {
    "steps_completed": ["parsing", "job_parsing", "matching", "feedback"],
    "start_time": "2023-12-01T10:00:00Z",
    "end_time": "2023-12-01T10:02:45Z",
    "duration_seconds": 165
  }
}
```

### Cancel Analysis

```bash
DELETE /api/v1/analysis/cancel/{analysis_id}
Authorization: Bearer {token}
```

**Response:**
```json
{
  "message": "Analysis cancelled successfully",
  "analysis_id": "analysis_456e7890-f12a-34b5-c678-90def1234567"
}
```

### List User Analyses

```bash
GET /api/v1/analysis/list?limit=10&offset=0&status_filter=completed
Authorization: Bearer {token}
```

**Query Parameters:**
- `limit` (optional): Number of results (default: 10, max: 100)
- `offset` (optional): Number to skip (default: 0)
- `status_filter` (optional): Filter by status

**Response:**
```json
{
  "analyses": [
    {
      "analysis_id": "analysis_456e7890-f12a-34b5-c678-90def1234567",
      "status": "completed",
      "current_step": "completed",
      "steps_completed": ["parsing", "job_parsing", "matching", "feedback"],
      "progress_percentage": 100.0,
      "start_time": "2023-12-01T10:00:00Z"
    }
  ],
  "total_count": 1
}
```

### Batch Analysis

Start multiple analyses in a single request.

```bash
POST /api/v1/analysis/batch
Authorization: Bearer {token}
Content-Type: application/json

[
  {
    "resume_content": "Resume 1 content...",
    "resume_filename": "resume1.pdf",
    "job_title": "Python Developer",
    "company": "Company A",
    "job_description": "Job description 1..."
  },
  {
    "resume_content": "Resume 2 content...",
    "resume_filename": "resume2.pdf", 
    "job_title": "Data Scientist",
    "company": "Company B",
    "job_description": "Job description 2..."
  }
]
```

**Limits:**
- Maximum 10 analyses per batch request
- Lower priority assigned to batch analyses

**Response:**
```json
[
  {
    "analysis_id": "analysis_111",
    "status": "started",
    "message": "Analysis workflow started successfully"
  },
  {
    "analysis_id": "analysis_222",
    "status": "started", 
    "message": "Analysis workflow started successfully"
  }
]
```

## WebSocket API

Real-time updates are available via WebSocket connection.

### Connection

```javascript
const ws = new WebSocket('ws://localhost:8000/api/v1/ws?token=YOUR_JWT_TOKEN');
```

### Message Format

All WebSocket messages follow this format:

```json
{
  "type": "message_type",
  "timestamp": "2023-12-01T10:00:00Z",
  "data": { ... }
}
```

### Client Messages

#### Subscribe to Analysis Updates

```json
{
  "type": "subscribe_analysis",
  "analysis_id": "analysis_456e7890-f12a-34b5-c678-90def1234567"
}
```

#### Unsubscribe from Analysis Updates

```json
{
  "type": "unsubscribe_analysis", 
  "analysis_id": "analysis_456e7890-f12a-34b5-c678-90def1234567"
}
```

#### Get Current Status

```json
{
  "type": "get_status",
  "analysis_id": "analysis_456e7890-f12a-34b5-c678-90def1234567"
}
```

#### Ping

```json
{
  "type": "ping"
}
```

### Server Messages

#### Connection Established

```json
{
  "type": "connection_established",
  "message": "WebSocket connection established",
  "timestamp": "2023-12-01T10:00:00Z"
}
```

#### Analysis Update

```json
{
  "type": "analysis_update",
  "analysis_id": "analysis_456e7890-f12a-34b5-c678-90def1234567", 
  "update": {
    "status": "running",
    "current_step": "matching",
    "progress_percentage": 65.0
  },
  "timestamp": "2023-12-01T10:01:30Z"
}
```

#### Analysis Status

```json
{
  "type": "analysis_status",
  "analysis_id": "analysis_456e7890-f12a-34b5-c678-90def1234567",
  "status": {
    "status": "completed",
    "progress_percentage": 100.0,
    "current_step": "completed"
  },
  "timestamp": "2023-12-01T10:02:45Z"
}
```

#### Subscription Confirmed

```json
{
  "type": "subscription_confirmed",
  "analysis_id": "analysis_456e7890-f12a-34b5-c678-90def1234567",
  "message": "Subscribed to analysis updates",
  "timestamp": "2023-12-01T10:00:15Z"
}
```

#### Pong

```json
{
  "type": "pong",
  "timestamp": "2023-12-01T10:00:30Z"
}
```

#### Error

```json
{
  "type": "error",
  "message": "Invalid message format",
  "timestamp": "2023-12-01T10:00:45Z"
}
```

## Metrics Endpoint

Application metrics for monitoring (Prometheus format).

```bash
GET /metrics
```

**Sample Response:**
```
# HELP http_requests_total Total HTTP requests
# TYPE http_requests_total counter
http_requests_total{method="POST",endpoint="/api/v1/analysis/start",status="200"} 42

# HELP http_request_duration_seconds HTTP request duration
# TYPE http_request_duration_seconds histogram
http_request_duration_seconds_bucket{le="0.1"} 28
http_request_duration_seconds_bucket{le="0.5"} 42
http_request_duration_seconds_sum 15.2
http_request_duration_seconds_count 42

# HELP llm_requests_total Total LLM API requests
# TYPE llm_requests_total counter
llm_requests_total{status="success"} 156
llm_requests_total{status="error"} 4
```

## SDK Examples

### Python SDK

```python
import asyncio
import aiohttp

class ResumeAnalyzerClient:
    def __init__(self, base_url: str, token: str):
        self.base_url = base_url
        self.headers = {"Authorization": f"Bearer {token}"}
    
    async def start_analysis(self, resume_content: str, job_description: str):
        async with aiohttp.ClientSession() as session:
            data = {
                "resume_content": resume_content,
                "resume_filename": "resume.pdf",
                "job_title": "Software Engineer",
                "company": "TechCorp",
                "job_description": job_description
            }
            
            async with session.post(
                f"{self.base_url}/api/v1/analysis/start",
                json=data,
                headers=self.headers
            ) as response:
                return await response.json()
    
    async def get_result(self, analysis_id: str):
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{self.base_url}/api/v1/analysis/result/{analysis_id}",
                headers=self.headers
            ) as response:
                return await response.json()

# Usage
async def main():
    client = ResumeAnalyzerClient("http://localhost:8000", "your_token")
    
    # Start analysis
    result = await client.start_analysis(
        resume_content="John Doe resume content...",
        job_description="Job requirements..."
    )
    
    analysis_id = result["analysis_id"]
    print(f"Started analysis: {analysis_id}")
    
    # Get result
    analysis_result = await client.get_result(analysis_id)
    print(f"Match score: {analysis_result['results']['analysis_result']['match_score']}")

asyncio.run(main())
```

### JavaScript SDK

```javascript
class ResumeAnalyzerClient {
  constructor(baseUrl, token) {
    this.baseUrl = baseUrl;
    this.headers = {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    };
  }

  async startAnalysis(resumeContent, jobDescription) {
    const response = await fetch(`${this.baseUrl}/api/v1/analysis/start`, {
      method: 'POST',
      headers: this.headers,
      body: JSON.stringify({
        resume_content: resumeContent,
        resume_filename: 'resume.pdf',
        job_title: 'Software Engineer',
        company: 'TechCorp',
        job_description: jobDescription
      })
    });
    
    return await response.json();
  }

  async getResult(analysisId) {
    const response = await fetch(
      `${this.baseUrl}/api/v1/analysis/result/${analysisId}`,
      { headers: this.headers }
    );
    
    return await response.json();
  }

  connectWebSocket(token) {
    const ws = new WebSocket(`ws://localhost:8000/api/v1/ws?token=${token}`);
    
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      console.log('Received:', data);
    };
    
    return ws;
  }
}

// Usage
const client = new ResumeAnalyzerClient('http://localhost:8000', 'your_token');

// Start analysis
client.startAnalysis('Resume content...', 'Job description...')
  .then(result => {
    console.log('Started analysis:', result.analysis_id);
    return client.getResult(result.analysis_id);
  })
  .then(analysisResult => {
    console.log('Match score:', analysisResult.results.analysis_result.match_score);
  });
```

## Testing the API

### Using curl

```bash
# Health check
curl http://localhost:8000/health/

# Start analysis
curl -X POST "http://localhost:8000/api/v1/analysis/start" \
  -H "Authorization: Bearer your_token" \
  -H "Content-Type: application/json" \
  -d '{
    "resume_content": "John Doe Software Engineer...",
    "resume_filename": "resume.pdf",
    "job_title": "Python Developer",
    "company": "TechCorp",
    "job_description": "We need a Python developer..."
  }'

# Get status
curl "http://localhost:8000/api/v1/analysis/status/analysis_id" \
  -H "Authorization: Bearer your_token"
```

### Using Postman

Import the Postman collection (to be provided) for comprehensive API testing.

## Changelog

- **v0.1.0**: Initial API release
- Add new versions here as they are released

For the most up-to-date API documentation, visit the interactive docs at `/docs` when running the service.