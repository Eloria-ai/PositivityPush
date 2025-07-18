# Test Setup Guide for Positivity Push

This document explains how to set up and run tests for the Positivity Push backend.

## Test Dependencies

The following packages are required to run tests:

### Core Testing
```bash
pytest>=7.0.0
pytest-asyncio>=0.21.0
pytest-cov>=4.0.0
```

### Service Dependencies (for integration tests)
```bash
# Already in requirements.txt
supabase>=2.1.0
celery[redis]>=5.3.4
redis>=4.5.2,<5.0.0
openai>=1.33.0,<2.0.0
```

### Mock/Test Utilities
```bash
httpx>=0.24.0  # Already included
pytest-mock>=3.10.0
```

## Installation

1. **Install test dependencies:**
```bash
pip install pytest pytest-asyncio pytest-cov pytest-mock
```

2. **All service dependencies are already in requirements.txt:**
```bash
pip install -r requirements.txt
```

## Environment Setup for Testing

Create a `.env.test` file with test credentials:

```bash
# Test Environment
ENVIRONMENT=test
DEBUG=true

# Test Database (use separate test instance)
SUPABASE_URL=your_test_supabase_url
SUPABASE_SERVICE_KEY=your_test_service_key

# Mock API Keys (can be fake for unit tests)
OPENAI_API_KEY=test_openai_key
STRIPE_SECRET_KEY=sk_test_your_stripe_test_key
WA_TOKEN=test_whatsapp_token

# Test Redis
REDIS_URL=redis://localhost:6379/1  # Use database 1 for tests
```

## Running Tests

### All Tests
```bash
pytest
```

### With Coverage
```bash
pytest --cov=app --cov-report=html
```

### Specific Test Files
```bash
pytest test_onboarding.py
pytest test_scheduled_task.py
```

### Async Tests Only
```bash
pytest -k "async"
```

## Test Structure

```
Back-End/
├── test_onboarding.py           # Onboarding flow tests
├── test_scheduled_task.py       # Celery task tests  
├── tests/                       # Additional test files
│   ├── test_timezone_service.py
│   ├── test_supabase_client.py
│   └── test_ai_coach.py
└── pytest.ini                   # Pytest configuration
```

## Test Configuration

Create `pytest.ini` in the project root:

```ini
[tool:pytest]
asyncio_mode = auto
testpaths = .
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    --verbose
    --tb=short
    --strict-markers
markers =
    slow: marks tests as slow (deselect with '-m "not slow"')
    integration: marks tests as integration tests
    unit: marks tests as unit tests
```

## Mock Services for Testing

For unit tests, mock external services:

```python
import pytest
from unittest.mock import AsyncMock, MagicMock

@pytest.fixture
def mock_openai():
    """Mock OpenAI client for testing"""
    mock = AsyncMock()
    mock.chat.completions.create.return_value.choices[0].message.content = "Test response"
    return mock

@pytest.fixture  
def mock_supabase():
    """Mock Supabase client for testing"""
    mock = MagicMock()
    mock.table.return_value.select.return_value.execute.return_value.data = []
    return mock
```

## Integration Test Requirements

For integration tests that use real services:

1. **Test Supabase Database:** Create separate test database instance
2. **Test Redis:** Use separate Redis database (e.g., database 1)
3. **Mock External APIs:** Always mock Stripe, WhatsApp, OpenAI in tests
4. **Test Data Cleanup:** Ensure tests clean up data after execution

## Common Test Patterns

### Testing Async Functions
```python
import pytest

@pytest.mark.asyncio
async def test_async_function():
    result = await some_async_function()
    assert result is not None
```

### Testing Celery Tasks  
```python
from worker.tasks.daily_messages import send_morning_affirmations

def test_celery_task():
    # Test task synchronously
    result = send_morning_affirmations.apply(args=['UTC'])
    assert result.successful()
```

### Testing Database Operations
```python
@pytest.mark.integration
async def test_database_operation(mock_supabase):
    service = SupabaseService(mock_supabase)
    result = await service.get_active_subscribers()
    assert isinstance(result, list)
```

## Troubleshooting

### Import Errors
If you get import errors, ensure Python path includes the app directory:
```bash
export PYTHONPATH="${PYTHONPATH}:$(pwd)/app"
```

### Async Test Issues
Ensure `pytest-asyncio` is installed and `asyncio_mode = auto` is in pytest.ini

### Database Connection Issues
Verify test environment variables are set correctly in `.env.test`

## CI/CD Integration

For automated testing in CI/CD:

```yaml
# Example GitHub Actions workflow
name: Test
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: pip install -r requirements.txt
      - run: pip install pytest pytest-asyncio pytest-cov
      - run: pytest --cov=app
```