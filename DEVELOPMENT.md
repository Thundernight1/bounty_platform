# Development Guide

This guide covers development workflow, best practices, and contribution guidelines for the Bounty Platform.

## Table of Contents
- [Setup](#setup)
- [Development Workflow](#development-workflow)
- [Testing](#testing)
- [Database Migrations](#database-migrations)
- [Code Quality](#code-quality)
- [Docker Development](#docker-development)
- [Debugging](#debugging)

---

## Setup

### Prerequisites
- Python 3.11+
- PostgreSQL 15+ (or use Docker)
- Redis (optional, for Celery)
- Git

### Local Development Setup

1. **Clone and setup environment**:
```bash
git clone <repository-url>
cd bounty_platform

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install development tools
pip install -e .
```

2. **Configure environment**:
```bash
cp .env.example .env
# Edit .env with your settings
```

3. **Setup database**:
```bash
# Option 1: Use Docker
docker-compose -f docker-compose.dev.yml up db -d

# Option 2: Use local PostgreSQL
createdb bounty_platform

# Run migrations
alembic upgrade head
```

4. **Start development server**:
```bash
uvicorn backend.main_v2:app --reload --host 0.0.0.0 --port 8000
```

---

## Development Workflow

### Branch Strategy
- `main` - Production-ready code
- `develop` - Integration branch
- `feature/*` - Feature branches
- `bugfix/*` - Bug fix branches
- `hotfix/*` - Critical production fixes

### Making Changes

1. **Create feature branch**:
```bash
git checkout -b feature/your-feature-name
```

2. **Make changes and commit**:
```bash
# Format code
black backend/ tests/

# Run linters
flake8 backend/ tests/
mypy backend/

# Run tests
pytest -v --cov=backend

# Commit
git add .
git commit -m "feat: add new feature"
```

3. **Push and create PR**:
```bash
git push origin feature/your-feature-name
# Create pull request on GitHub
```

### Commit Message Format
Follow conventional commits:
- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation changes
- `style:` - Code style changes (formatting)
- `refactor:` - Code refactoring
- `test:` - Test additions or changes
- `chore:` - Build/tooling changes

---

## Testing

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=backend --cov-report=html

# Run specific test file
pytest tests/test_jobs.py

# Run specific test
pytest tests/test_jobs.py::test_create_job

# Run with verbose output
pytest -v

# Run and stop on first failure
pytest -x
```

### Writing Tests

1. **Use fixtures** (defined in `tests/conftest.py`):
```python
def test_create_job(client, sample_job_payload):
    response = client.post("/jobs", json=sample_job_payload)
    assert response.status_code == 200
```

2. **Test structure**:
```python
def test_feature_name():
    # Arrange
    payload = {...}

    # Act
    response = client.post("/endpoint", json=payload)

    # Assert
    assert response.status_code == 200
    assert response.json()["field"] == "expected"
```

3. **Use parametrize for multiple cases**:
```python
@pytest.mark.parametrize("job_type,expected", [
    ("attack_surface", "pending"),
    ("sca", "pending"),
    ("smart_contract", "pending"),
])
def test_job_types(client, job_type, expected):
    payload = {"job_type": job_type, ...}
    response = client.post("/jobs", json=payload)
    assert response.json()["status"] == expected
```

---

## Database Migrations

### Creating Migrations

```bash
# Auto-generate migration from model changes
alembic revision --autogenerate -m "add new field to job model"

# Create empty migration
alembic revision -m "custom migration"

# Edit migration file in alembic/versions/
```

### Applying Migrations

```bash
# Upgrade to latest
alembic upgrade head

# Upgrade to specific revision
alembic upgrade <revision_id>

# Downgrade one revision
alembic downgrade -1

# Show current revision
alembic current

# Show migration history
alembic history
```

### Migration Best Practices

1. **Always review auto-generated migrations**
2. **Test migrations on development database first**
3. **Include both upgrade and downgrade logic**
4. **Add data migrations separately from schema changes**
5. **Never edit applied migrations**

---

## Code Quality

### Formatting

```bash
# Format with black
black backend/ tests/

# Check formatting
black --check backend/ tests/
```

### Linting

```bash
# Run flake8
flake8 backend/ tests/

# Run mypy for type checking
mypy backend/
```

### Security Scanning

```bash
# Check for security issues
bandit -r backend/

# Check dependencies for vulnerabilities
safety check
```

### Pre-commit Hooks (optional)

```bash
# Install pre-commit
pip install pre-commit

# Setup hooks
pre-commit install

# Run manually
pre-commit run --all-files
```

---

## Docker Development

### Development with Docker

```bash
# Start all services
docker-compose -f docker-compose.dev.yml up

# Start specific service
docker-compose -f docker-compose.dev.yml up backend

# View logs
docker-compose -f docker-compose.dev.yml logs -f backend

# Execute command in container
docker-compose -f docker-compose.dev.yml exec backend bash

# Rebuild after changes
docker-compose -f docker-compose.dev.yml up --build
```

### Docker Compose Services

- `db` - PostgreSQL database
- `redis` - Redis cache/queue
- `backend` - FastAPI application
- `celery_worker` - Background task worker
- `nginx` - Reverse proxy
- `prometheus` - Metrics collection
- `grafana` - Monitoring dashboard

---

## Debugging

### Using Python Debugger

```python
# Add breakpoint
import pdb; pdb.set_trace()

# Or use built-in breakpoint()
breakpoint()
```

### Logging

```python
from backend.logger import get_logger

logger = get_logger(__name__)

logger.info("message", extra_field="value")
logger.error("error occurred", exc_info=True)
```

### Database Queries

```python
# Enable SQL logging
# In .env set: DATABASE_URL=...?echo=True

# Or in code:
import logging
logging.basicConfig()
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)
```

---

## API Documentation

### Accessing Swagger UI

When the server is running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- OpenAPI JSON: http://localhost:8000/openapi.json

### Testing API with curl

```bash
# Create job
curl -X POST http://localhost:8000/jobs \
  -H "Content-Type: application/json" \
  -d '{"project_name": "test", "job_type": "attack_surface", "target_url": "https://example.com", "accept_terms": true}'

# Get job status
curl http://localhost:8000/jobs/{job_id}

# List jobs
curl http://localhost:8000/jobs

# Health check
curl http://localhost:8000/health
```

---

## Troubleshooting

### Common Issues

1. **Database connection error**
   - Check DATABASE_URL in .env
   - Ensure PostgreSQL is running
   - Run migrations: `alembic upgrade head`

2. **Import errors**
   - Ensure virtual environment is activated
   - Reinstall package: `pip install -e .`

3. **Tests failing**
   - Clear test database: `rm test.db`
   - Check test environment variables
   - Run with `-v` flag for details

4. **Docker issues**
   - Clean up: `docker-compose down -v`
   - Rebuild: `docker-compose build --no-cache`
   - Check logs: `docker-compose logs`

---

## Additional Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [Alembic Documentation](https://alembic.sqlalchemy.org/)
- [Pytest Documentation](https://docs.pytest.org/)
- [Docker Documentation](https://docs.docker.com/)
