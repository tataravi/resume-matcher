# Resume Analyzer

An AI agent-based resume analysis system built with FastAPI, featuring automated parsing, job matching, and feedback generation using advanced LLM technology.

## 🚀 Features

- **AI-Powered Analysis**: Advanced resume parsing and job matching using Claude AI
- **Agent Architecture**: Modular design with specialized agents for different tasks
- **Real-time Processing**: WebSocket support for live analysis updates
- **Cloud-Ready**: AWS integration with S3, DynamoDB, SQS, and Lambda
- **Scalable Infrastructure**: Containerized deployment with auto-scaling
- **Comprehensive Testing**: Full test suite with unit, integration, and performance tests
- **Security-First**: Built-in security scanning, authentication, and rate limiting
- **Production-Ready**: CI/CD pipeline, monitoring, and infrastructure as code

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Parser Agent  │    │  Matcher Agent  │    │ Feedback Agent  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │ Orchestrator    │
                    │     Agent       │
                    └─────────────────┘
                                 │
                    ┌─────────────────┐
                    │   FastAPI       │
                    │   Backend       │
                    └─────────────────┘
                                 │
         ┌───────────────────────┼───────────────────────┐
         │                       │                       │
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│      AWS S3     │    │   DynamoDB      │    │      SQS        │
│   (File Storage)│    │  (Metadata)     │    │  (Task Queue)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🛠️ Technology Stack

### Backend
- **FastAPI**: High-performance Python web framework
- **Python 3.11**: Modern Python with type hints
- **Pydantic**: Data validation and serialization
- **AsyncIO**: Asynchronous programming support

### AI & ML
- **Claude API**: Advanced language model for text analysis
- **Custom Agents**: Modular AI agent architecture
- **Structured Output**: JSON schema validation for LLM responses

### Infrastructure
- **Docker**: Containerization and orchestration
- **AWS Services**: S3, DynamoDB, SQS, Lambda, ECS
- **Terraform**: Infrastructure as Code
- **GitHub Actions**: CI/CD automation

### Database & Storage
- **PostgreSQL**: Primary database for structured data
- **Redis**: Caching and session management
- **AWS S3**: File storage for resumes and documents
- **DynamoDB**: NoSQL database for analysis results

### Monitoring & Security
- **Prometheus**: Metrics collection
- **Grafana**: Visualization and dashboards
- **Structured Logging**: JSON-based logging with correlation IDs
- **Security Scanning**: Automated vulnerability detection

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Docker and Docker Compose
- AWS CLI configured
- Node.js (for frontend, if applicable)

### Local Development

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-org/resume-analyzer.git
   cd resume-analyzer
   ```

2. **Set up environment**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Install dependencies**
   ```bash
   pip install poetry
   poetry install
   ```

4. **Start services with Docker**
   ```bash
   ./scripts/docker-setup.sh dev
   ```

5. **Access the application**
   - API: https://localhost/docs
   - Grafana: http://localhost:3000
   - Flower (Celery): http://localhost:5555

### Using Docker Only

```bash
# Setup and start development environment
./scripts/docker-setup.sh dev

# Start production environment
./scripts/docker-setup.sh prod

# Setup only (no start)
./scripts/docker-setup.sh setup-only
```

## 📚 API Documentation

### Authentication

All API endpoints (except health checks) require authentication:

```bash
# Get token (implement your auth flow)
curl -X POST "https://api.example.com/auth/token" \
  -H "Content-Type: application/json" \
  -d '{"username": "user", "password": "pass"}'

# Use token in requests
curl -H "Authorization: Bearer YOUR_TOKEN" \
  "https://api.example.com/api/v1/analysis/list"
```

### Core Endpoints

#### Upload Resume
```bash
curl -X POST "http://localhost:8000/api/v1/upload/resume" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@resume.pdf"
```

#### Start Analysis
```bash
curl -X POST "http://localhost:8000/api/v1/analysis/start" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "resume_content": "Resume text content...",
    "resume_filename": "john_doe_resume.pdf",
    "job_title": "Senior Python Developer",
    "company": "Tech Corp",
    "job_description": "We are looking for...",
    "priority": "medium"
  }'
```

#### Get Analysis Status
```bash
curl "http://localhost:8000/api/v1/analysis/status/{analysis_id}" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

#### WebSocket Connection
```javascript
const ws = new WebSocket('ws://localhost:8000/api/v1/ws?token=YOUR_TOKEN');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Received:', data);
};

// Subscribe to analysis updates
ws.send(JSON.stringify({
  type: 'subscribe_analysis',
  analysis_id: 'your-analysis-id'
}));
```

## 🏗️ Development

### Project Structure

```
resume-analyzer/
├── src/                          # Source code
│   ├── agents/                   # AI agent implementations
│   │   ├── parser_agent.py      # Resume parsing agent
│   │   ├── matcher_agent.py     # Job matching agent
│   │   ├── feedback_agent.py    # Feedback generation agent
│   │   └── orchestrator_agent.py# Workflow orchestration
│   ├── api/                      # FastAPI routes and middleware
│   │   ├── routes/              # API route definitions
│   │   ├── middleware.py        # Custom middleware
│   │   └── auth.py              # Authentication logic
│   ├── core/                     # Core business logic
│   │   ├── models.py            # Pydantic models
│   │   └── base_agent.py        # Base agent class
│   ├── services/                 # External service integrations
│   │   ├── llm_service.py       # Claude LLM integration
│   │   ├── s3_service.py        # AWS S3 integration
│   │   ├── dynamodb_service.py  # DynamoDB integration
│   │   └── sqs_service.py       # SQS integration
│   ├── config/                   # Configuration management
│   └── main.py                   # FastAPI application entry point
├── tests/                        # Test suite
│   ├── unit/                    # Unit tests
│   ├── integration/             # Integration tests
│   └── performance/             # Performance tests
├── terraform/                    # Infrastructure as Code
│   ├── modules/                 # Terraform modules
│   └── environments/            # Environment-specific configs
├── .github/workflows/           # GitHub Actions CI/CD
├── docker-compose.yml           # Local development environment
├── docker-compose.prod.yml      # Production environment
└── Dockerfile                   # Container definition
```

### Adding New Agents

1. **Create agent class**
   ```python
   # src/agents/my_agent.py
   from src.core.base_agent import BaseAgent
   from src.core.models import AgentType, Task
   
   class MyAgent(BaseAgent):
       def __init__(self, **kwargs):
           super().__init__(agent_type=AgentType.CUSTOM, **kwargs)
       
       async def execute_task(self, task: Task):
           # Implement your agent logic
           return {"result": "success"}
   ```

2. **Register agent**
   ```python
   # Update src/agents/__init__.py
   from .my_agent import MyAgent
   __all__ = [..., "MyAgent"]
   ```

3. **Add tests**
   ```python
   # tests/unit/test_my_agent.py
   import pytest
   from src.agents.my_agent import MyAgent
   
   @pytest.mark.unit
   class TestMyAgent:
       def test_agent_creation(self):
           agent = MyAgent()
           assert agent is not None
   ```

### Running Tests

```bash
# Install development dependencies
poetry install

# Run all tests
poetry run pytest

# Run specific test categories
poetry run pytest tests/unit/          # Unit tests
poetry run pytest tests/integration/   # Integration tests
poetry run pytest tests/performance/   # Performance tests

# Run with coverage
poetry run pytest --cov=src --cov-report=html

# Run specific test file
poetry run pytest tests/unit/test_llm_service.py -v
```

### Code Quality

```bash
# Format code
poetry run black src/ tests/
poetry run isort src/ tests/

# Lint code
poetry run flake8 src/ tests/

# Type checking
poetry run mypy src/

# Security scan
poetry run bandit -r src/

# All quality checks
poetry run pre-commit run --all-files
```

## 🚀 Deployment

### AWS Deployment

1. **Configure AWS credentials**
   ```bash
   aws configure
   # or set environment variables
   export AWS_ACCESS_KEY_ID=your-key
   export AWS_SECRET_ACCESS_KEY=your-secret
   ```

2. **Deploy infrastructure**
   ```bash
   cd terraform/
   terraform init
   terraform plan -var-file="production.tfvars"
   terraform apply -var-file="production.tfvars"
   ```

3. **Build and push Docker image**
   ```bash
   # Build image
   docker build -t resume-analyzer .
   
   # Tag for ECR
   docker tag resume-analyzer:latest \
     123456789012.dkr.ecr.us-east-1.amazonaws.com/resume-analyzer:latest
   
   # Push to ECR
   aws ecr get-login-password --region us-east-1 | \
     docker login --username AWS --password-stdin \
     123456789012.dkr.ecr.us-east-1.amazonaws.com
   
   docker push 123456789012.dkr.ecr.us-east-1.amazonaws.com/resume-analyzer:latest
   ```

4. **Deploy to ECS**
   ```bash
   aws ecs update-service \
     --cluster resume-analyzer-prod \
     --service resume-analyzer-prod \
     --force-new-deployment
   ```

### Environment Variables

Key environment variables for production:

```bash
# Application
DEBUG=false
LOG_LEVEL=WARNING
API_WORKERS=4

# Security
SECRET_KEY=your-super-secret-key
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Database
DATABASE_URL=postgresql://user:pass@host:5432/dbname
REDIS_URL=redis://host:6379/0

# AWS
AWS_REGION=us-east-1
AWS_S3_BUCKET=your-bucket
AWS_DYNAMODB_TABLE=your-table
AWS_SQS_QUEUE_URL=https://sqs.region.amazonaws.com/account/queue

# Claude API
CLAUDE_API_KEY=your-api-key
CLAUDE_MODEL=claude-3-5-sonnet-20241022
```

## 📊 Monitoring

### Metrics

The application exposes Prometheus metrics at `/metrics`:

- `http_requests_total`: Total HTTP requests
- `http_request_duration_seconds`: Request duration
- `llm_requests_total`: LLM API requests
- `agent_tasks_total`: Agent task executions
- `analysis_completion_time`: Time to complete analysis

### Logging

Structured JSON logging with correlation IDs:

```json
{
  "timestamp": "2023-12-01T10:00:00Z",
  "level": "INFO",
  "logger": "src.agents.parser_agent",
  "message": "Resume parsing completed",
  "correlation_id": "req_123456",
  "user_id": "user_789",
  "analysis_id": "analysis_abc",
  "duration": 1.23
}
```

### Health Checks

- `/health/live`: Liveness probe
- `/health/ready`: Readiness probe  
- `/health/`: Detailed health status

## 🔒 Security

### Security Features

- **Authentication**: JWT-based authentication
- **Rate Limiting**: Request rate limiting per user
- **Input Validation**: Comprehensive input validation
- **File Upload Security**: File type and size validation
- **CORS Protection**: Configurable CORS policies
- **Security Headers**: Standard security headers
- **Secrets Management**: AWS Secrets Manager integration

### Security Scanning

Automated security scanning in CI/CD:

- **Dependency Scanning**: Safety, pip-audit
- **Code Analysis**: Bandit, Semgrep
- **Container Scanning**: Trivy, Grype
- **Infrastructure**: Checkov, TFSec
- **Secret Detection**: TruffleHog, detect-secrets

### Security Best Practices

1. **Never commit secrets** to version control
2. **Use environment variables** for configuration
3. **Validate all inputs** at API boundaries
4. **Implement proper error handling** to avoid information leakage
5. **Keep dependencies updated** and scan for vulnerabilities
6. **Use HTTPS** in production
7. **Implement proper logging** without sensitive data

## 🤝 Contributing

### Development Workflow

1. **Fork the repository**
2. **Create a feature branch**
   ```bash
   git checkout -b feature/amazing-feature
   ```
3. **Make your changes**
4. **Run tests and quality checks**
   ```bash
   poetry run pytest
   poetry run pre-commit run --all-files
   ```
5. **Commit with conventional commits**
   ```bash
   git commit -m "feat: add amazing new feature"
   ```
6. **Push and create PR**
   ```bash
   git push origin feature/amazing-feature
   ```

### Commit Convention

Use [Conventional Commits](https://www.conventionalcommits.org/):

- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation changes
- `style:` Code style changes
- `refactor:` Code refactoring
- `test:` Test additions or changes
- `chore:` Build process or auxiliary tool changes

### Code Review Guidelines

- **Keep PRs small** and focused
- **Write descriptive commit messages**
- **Include tests** for new features
- **Update documentation** as needed
- **Follow the style guide**
- **Add performance considerations** for significant changes

## 📈 Performance

### Performance Metrics

- **API Response Time**: < 200ms for most endpoints
- **Analysis Completion**: < 30 seconds for full analysis
- **Throughput**: 100+ analyses per minute
- **Memory Usage**: < 512MB per container
- **CPU Usage**: < 80% under normal load

### Optimization Features

- **Caching**: Redis-based LLM response caching
- **Rate Limiting**: Token bucket algorithm
- **Connection Pooling**: Database and HTTP connections
- **Async Processing**: Non-blocking I/O operations
- **Auto Scaling**: ECS auto scaling based on CPU/memory

### Performance Testing

```bash
# Load testing with pytest-benchmark
poetry run pytest tests/performance/ --benchmark-only

# API load testing (requires test environment)
poetry run locust -f tests/load/locustfile.py
```

## 🔧 Troubleshooting

### Common Issues

#### Agent Tasks Failing
```bash
# Check agent logs
docker-compose logs resume-analyzer | grep "agent"

# Check task status
curl "http://localhost:8000/api/v1/analysis/status/{analysis_id}"
```

#### Database Connection Issues
```bash
# Check database connectivity
docker-compose exec postgres pg_isready

# Check connection string
echo $DATABASE_URL
```

#### High Memory Usage
```bash
# Monitor container resources
docker stats

# Check for memory leaks in logs
docker-compose logs resume-analyzer | grep -i "memory\|oom"
```

#### LLM API Failures
```bash
# Check LLM service metrics
curl "http://localhost:8000/metrics" | grep llm

# Verify API key and configuration
curl -H "x-api-key: $CLAUDE_API_KEY" \
  "https://api.anthropic.com/v1/models"
```

### Debug Mode

Enable debug mode for detailed logging:

```bash
export DEBUG=true
export LOG_LEVEL=DEBUG
docker-compose up resume-analyzer
```

### Performance Issues

1. **Check metrics dashboard** in Grafana
2. **Review slow query logs** in PostgreSQL
3. **Monitor Redis cache hit ratio**
4. **Check AWS service limits**
5. **Review ECS service auto-scaling**

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **FastAPI**: For the excellent web framework
- **Claude/Anthropic**: For providing advanced LLM capabilities
- **AWS**: For cloud infrastructure services
- **Open Source Community**: For all the amazing tools and libraries

## 📞 Support

- **Documentation**: [Full API Documentation](docs/)
- **Issues**: [GitHub Issues](https://github.com/your-org/resume-analyzer/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-org/resume-analyzer/discussions)
- **Email**: support@yourcompany.com

---

**Built with ❤️ using FastAPI and AI**