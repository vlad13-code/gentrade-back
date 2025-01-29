# 1. Feature Summary

**Objective**: Refactor Freqtrade utility functions into class-based services for better encapsulation and testability.

**Scope**:

- In scope:
  - Create `FTBacktests`, `FTStrategies`, and `FTUserdir` service classes
  - Maintain existing functionality with improved error handling
  - Add type hints and docstrings
- Out of scope:
  - Modifying Freqtrade core functionality
  - Changing existing database schemas

## 2. Codebase Audit

**Existing implementations**:

- `ft_backtesting.py`: Docker-based backtest execution
- `ft_strategies.py`: Strategy file management
- `ft_userdir.py`: User data directory initialization

**Potential conflicts**:

- Current service layers (service_backtests.py) directly call util functions

## 3. Architectural Alignment

**New structure**:

```plaintext
/app/util/ft/
├── __init__.py
├── backtests.py      # FTBacktests class
├── strategies.py     # FTStrategies class
└── userdir.py        # FTUserdir class
```

**Dependencies**:

- Database: Existing StrategiesORM/BacktestsORM
- Services: service_backtests.py integration
- AI: Maintain LangGraph checkpoint compatibility

## 4. Implementation Blueprint

**FTBacktests (Service)**:

- Responsibility: Dockerized backtest execution management
- Dependencies: python-on-whales, StrategiesORM
- Lifecycle: Request-scoped

**FTStrategies (Service)**:

- Responsibility: Strategy file operations and validation
- Dependencies: OS operations, file I/O
- Lifecycle: Singleton

**FTUserdir (Service)**:

- Responsibility: User directory initialization/management
- Dependencies: Pathlib, Freqtrade configs
- Lifecycle: Singleton

## 5. Phase Implementation

### Phase 1: Foundation

1. Create `FTBaseService` with common utilities
2. Implement class-based services with type hints
3. Add error hierarchy (`FTFileError`, `FTDockerError`)

### Phase 2: Integration

1. Update service_backtests.py to use FTBacktests
2. Modify service_strategies.py to leverage FTStrategies
3. Add dependency injection in routers

### Phase 3: Optimization

1. Implement file operation caching
2. Add Docker connection pooling
3. Create async variants for long-running operations

## 6. Compatibility Strategy

**Migration Needs**:

- Deprecate old util functions with warnings
- Maintain legacy imports until v2.0
- Update API documentation with new patterns

**Testing Surface**:

- Unit: Class method contracts
- Integration: Docker interaction tests
- E2E: Full backtest flow validation

## 7. Security & Performance

**Considerations**:

- File permission validation in FTStrategies
- Docker socket security hardening
- Strategy file size limits (50MB)
- Async I/O for Docker operations

## 8. Confidence Assessment

**Risk Factors**:

- Docker API compatibility breaks
- File path handling differences OS
- Existing migration dependencies

**Validation Plan**:

- 100% test coverage for public methods
- Performance benchmarking vs legacy
- Canary deployment to staging

## 9. Open Questions

1. Should Docker client be abstracted behind interface?
2. How to handle Windows path conventions?
3. Optimal cache TTL for user directories?

Key implementation details from existing code:

```python:app/util/ft/backtests.py
# Sample class skeleton
class FTBacktests:
    def __init__(self, docker_client: Optional[DockerClient] = None):
        self.docker = docker_client or DockerClient()

    async def run_backtest(
        self,
        strategy_name: str,
        user_id: str,
        date_range: str
    ) -> dict[str, Any]:
        """Replace run_backtest_in_docker with class method"""
        # Implementation using existing logic
        # Add type hints and error wrapping
```

This plan maintains the core functionality while improving maintainability through:

1. Better encapsulation of Freqtrade operations
2. Standardized error handling
3. Explicit dependency management
4. Type-safe interfaces
5. Improved testability through class-based patterns
