# Contributing to Resume Analyzer

Thank you for your interest in contributing to Resume Analyzer! This document provides guidelines and information for contributors.

## 🤝 How to Contribute

### Reporting Issues

Before creating an issue, please:

1. **Check existing issues** to avoid duplicates
2. **Use issue templates** when available
3. **Provide detailed information** including:
   - Steps to reproduce
   - Expected behavior
   - Actual behavior
   - Environment details
   - Screenshots (if applicable)

### Suggesting Features

For feature requests:

1. **Check the roadmap** and existing feature requests
2. **Open a discussion** before creating an issue
3. **Provide clear use cases** and benefits
4. **Consider implementation complexity**

### Code Contributions

1. **Fork the repository**
2. **Create a feature branch** from `main`
3. **Make your changes** following our coding standards
4. **Add tests** for new functionality
5. **Update documentation** as needed
6. **Submit a pull request**

## 🛠️ Development Setup

### Prerequisites

- Python 3.11+
- Docker and Docker Compose
- Poetry for dependency management
- AWS CLI (for infrastructure work)
- Git

### Local Development Environment

1. **Clone your fork**
   ```bash
   git clone https://github.com/YOUR_USERNAME/resume-analyzer.git
   cd resume-analyzer
   ```

2. **Install dependencies**
   ```bash
   pip install poetry
   poetry install
   ```

3. **Set up environment**
   ```bash
   cp .env.example .env
   # Edit .env with your local configuration
   ```

4. **Start development services**
   ```bash
   ./scripts/docker-setup.sh dev
   ```

5. **Run tests**
   ```bash
   poetry run pytest
   ```

### Development Workflow

1. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make changes and commit frequently**
   ```bash
   git add .
   git commit -m "feat: add new feature"
   ```

3. **Keep your branch updated**
   ```bash
   git fetch origin
   git rebase origin/main
   ```

4. **Run quality checks**
   ```bash
   poetry run pre-commit run --all-files
   ```

5. **Push your branch**
   ```bash
   git push origin feature/your-feature-name
   ```

6. **Create a pull request**

## 📝 Coding Standards

### Python Code Style

We follow PEP 8 with these specific guidelines:

- **Line length**: 100 characters maximum
- **Import order**: Use isort configuration
- **Formatting**: Use Black formatter
- **Type hints**: Required for all functions and methods
- **Docstrings**: Google style docstrings

Example:
```python
from typing import Dict, List, Optional

async def process_resume(
    content: str, 
    user_id: str,
    options: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Process resume content and extract information.
    
    Args:
        content: Raw resume text content
        user_id: ID of the user who owns the resume
        options: Optional processing parameters
        
    Returns:
        Dictionary containing extracted resume information
        
    Raises:
        ValueError: If content is empty or invalid
    """
    if not content:
        raise ValueError("Resume content cannot be empty")
        
    # Implementation here
    return {"processed": True}
```

### Code Organization

- **Modules**: Keep modules focused and cohesive
- **Classes**: Single responsibility principle
- **Functions**: Pure functions when possible
- **Error handling**: Explicit error handling with proper exceptions
- **Logging**: Use structured logging with correlation IDs

### Commit Message Convention

Use [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation only changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code change that neither fixes a bug nor adds a feature
- `perf`: Performance improvements
- `test`: Adding missing tests or correcting existing tests
- `chore`: Changes to build process or auxiliary tools

**Examples:**
```
feat(agents): add resume parsing agent
fix(api): handle timeout errors in LLM service
docs: update API documentation
test: add unit tests for parser agent
```

## 🧪 Testing Guidelines

### Test Categories

1. **Unit Tests** (`tests/unit/`)
   - Test individual functions and classes
   - Mock external dependencies
   - Fast execution (< 1 second per test)

2. **Integration Tests** (`tests/integration/`)
   - Test component interactions
   - Use test databases and services
   - May take longer to execute

3. **Performance Tests** (`tests/performance/`)
   - Benchmark critical functions
   - Test under load conditions
   - Monitor resource usage

### Writing Tests

- **Use pytest fixtures** for test setup
- **Mock external services** in unit tests
- **Test both success and failure cases**
- **Use descriptive test names**
- **Keep tests independent** and idempotent

Example:
```python
import pytest
from unittest.mock import AsyncMock, Mock

from src.agents.parser_agent import ParserAgent
from src.services.llm_service import LLMService

@pytest.mark.unit
class TestParserAgent:
    @pytest.fixture
    def mock_llm_service(self):
        service = Mock(spec=LLMService)
        service.generate_completion = AsyncMock(return_value="parsed data")
        return service
    
    @pytest.fixture
    def parser_agent(self, mock_llm_service):
        return ParserAgent(llm_service=mock_llm_service)
    
    async def test_parse_resume_success(self, parser_agent, sample_resume_text):
        """Test successful resume parsing."""
        task = Task(
            type="test_task",
            input_data={"content": sample_resume_text}
        )
        
        result = await parser_agent.execute_task(task)
        
        assert "parsed_data" in result
        assert result["parsed_data"] is not None
    
    async def test_parse_resume_empty_content(self, parser_agent):
        """Test parsing with empty content."""
        task = Task(
            type="test_task",
            input_data={"content": ""}
        )
        
        with pytest.raises(ValueError, match="empty"):
            await parser_agent.execute_task(task)
```

### Running Tests

```bash
# All tests
poetry run pytest

# Specific category
poetry run pytest tests/unit/
poetry run pytest tests/integration/
poetry run pytest tests/performance/

# With coverage
poetry run pytest --cov=src --cov-report=html

# Specific test file
poetry run pytest tests/unit/test_parser_agent.py -v

# Run with markers
poetry run pytest -m "unit"
poetry run pytest -m "integration"
```

## 📖 Documentation

### Code Documentation

- **Docstrings**: All public functions, classes, and modules
- **Type hints**: Required for all function signatures
- **Comments**: Explain complex logic and business rules
- **README updates**: Update README for new features

### API Documentation

- **OpenAPI/Swagger**: Automatically generated from FastAPI
- **Examples**: Provide request/response examples
- **Error codes**: Document all possible error responses

### Architecture Documentation

- **Decision records**: Document significant architectural decisions
- **Diagrams**: Update architecture diagrams for major changes
- **Deployment guides**: Keep deployment documentation current

## 🔍 Code Review Process

### Submitting Pull Requests

1. **Use the PR template** (will be created automatically)
2. **Provide clear description** of changes
3. **Link related issues** using keywords (fixes #123)
4. **Add screenshots** for UI changes
5. **Mark as draft** if work in progress

### Review Criteria

Reviewers will check for:

- **Functionality**: Does the code work as intended?
- **Tests**: Are there sufficient tests?
- **Code quality**: Follows coding standards?
- **Documentation**: Is documentation updated?
- **Performance**: Are there performance implications?
- **Security**: Are there security considerations?

### Review Process

1. **Automated checks** must pass (CI/CD pipeline)
2. **At least one approval** from code owners
3. **All conversations resolved**
4. **Squash and merge** or rebase merge

## 🛡️ Security Guidelines

### Security Considerations

- **Never commit secrets** or credentials
- **Validate all inputs** at API boundaries
- **Use parameterized queries** for database operations
- **Implement proper error handling** without information leakage
- **Follow OWASP guidelines** for web security

### Reporting Security Issues

For security vulnerabilities:

1. **Do not create public issues**
2. **Email security@yourcompany.com** with details
3. **Use encrypted communication** if possible
4. **Allow reasonable time** for response

## 🚀 Release Process

### Release Schedule

- **Major releases**: Quarterly
- **Minor releases**: Monthly
- **Patch releases**: As needed for critical fixes

### Release Checklist

- [ ] Update version numbers
- [ ] Update CHANGELOG.md
- [ ] Run full test suite
- [ ] Update documentation
- [ ] Create release notes
- [ ] Tag release in Git
- [ ] Deploy to staging
- [ ] Deploy to production
- [ ] Announce release

## 🤔 Getting Help

### Communication Channels

- **GitHub Discussions**: General questions and ideas
- **GitHub Issues**: Bug reports and feature requests
- **Slack/Discord**: Real-time chat (if available)
- **Email**: Direct contact for sensitive issues

### Resources

- **Documentation**: [docs/](docs/)
- **API Reference**: Available at `/docs` endpoint
- **Architecture Guide**: [docs/architecture.md](docs/architecture.md)
- **Deployment Guide**: [docs/deployment.md](docs/deployment.md)

## 📋 Issue and PR Templates

### Bug Report Template

```markdown
**Describe the bug**
A clear and concise description of what the bug is.

**To Reproduce**
Steps to reproduce the behavior:
1. Go to '...'
2. Click on '....'
3. Scroll down to '....'
4. See error

**Expected behavior**
A clear and concise description of what you expected to happen.

**Screenshots**
If applicable, add screenshots to help explain your problem.

**Environment:**
 - OS: [e.g. iOS]
 - Browser [e.g. chrome, safari]
 - Version [e.g. 22]

**Additional context**
Add any other context about the problem here.
```

### Feature Request Template

```markdown
**Is your feature request related to a problem? Please describe.**
A clear and concise description of what the problem is.

**Describe the solution you'd like**
A clear and concise description of what you want to happen.

**Describe alternatives you've considered**
A clear and concise description of any alternative solutions.

**Additional context**
Add any other context or screenshots about the feature request here.
```

### Pull Request Template

```markdown
## Description
Brief description of changes.

## Type of Change
- [ ] Bug fix (non-breaking change which fixes an issue)
- [ ] New feature (non-breaking change which adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Documentation update

## Testing
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Manual testing completed

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Code is commented (particularly complex areas)
- [ ] Documentation updated
- [ ] No new warnings
```

## 🎯 Contribution Areas

We welcome contributions in these areas:

### High Priority
- Performance optimizations
- Additional LLM provider integrations
- Enhanced security features
- Mobile-responsive UI improvements

### Medium Priority
- Additional file format support
- Internationalization (i18n)
- Advanced analytics features
- Third-party integrations

### Low Priority
- Code refactoring
- Documentation improvements
- Test coverage improvements
- DevOps enhancements

Thank you for contributing to Resume Analyzer! 🚀