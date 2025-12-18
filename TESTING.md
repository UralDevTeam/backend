# Testing

This project uses pytest for testing. Tests are organized into different categories:

## Running Tests

### All tests
```bash
uv run pytest
```

### With coverage report
```bash
uv run pytest --cov=src --cov-report=term-missing --cov-report=html
```

### Run specific test file
```bash
uv run pytest tests/test_user_service.py
```

### Run specific test class or method
```bash
uv run pytest tests/test_user_service.py::TestUserServiceListUsers
uv run pytest tests/test_user_service.py::TestUserServiceListUsers::test_list_users_empty
```

### Run only integration tests
```bash
uv run pytest -m integration
```

### Run only unit tests
```bash
uv run pytest -m unit
```

## Test Categories

- **Unit tests**: Fast tests that don't require database or external dependencies
- **Integration tests**: Tests that use the database and test multiple components together

## Test Structure

- `tests/conftest.py` - Contains pytest fixtures for test setup
- `tests/test_user_service.py` - Integration tests for UserService
- `tests/test_other_services.py` - Tests for PingService, AvatarService, etc.
- `tests/test_init_data.py` - Tests for initial data SQL scripts

## Database for Testing

Tests use SQLite in-memory database for fast execution. Some tests that require PostgreSQL-specific features (like `regexp_replace`) are marked as skipped when running with SQLite.

To run all tests including PostgreSQL-specific ones, you would need to configure a PostgreSQL test database.

## Coverage

Coverage reports are generated in:
- Terminal output (with `--cov-report=term-missing`)
- HTML report in `htmlcov/` directory (with `--cov-report=html`)

Current test coverage: ~54% (32 passing tests, 10 skipped)

## Writing New Tests

1. Add test fixtures to `conftest.py` if needed
2. Follow existing test naming conventions: `test_<method>_<scenario>`
3. Use descriptive test docstrings
4. Mark tests appropriately:
   - `@pytest.mark.unit` for unit tests
   - `@pytest.mark.integration` for integration tests
   - `@pytest.mark.asyncio` for async tests
   - `@pytest.mark.skip(reason="...")` for tests requiring specific conditions
