# Contributing to tableau-agent-toolkit

Thank you for your interest in contributing! This document provides guidelines for
development setup and contribution workflow.

## How to Contribute

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/my-feature`)
3. Make your changes
4. Ensure all tests pass
5. Submit a pull request

## Development Setup

```bash
# Clone your fork
git clone https://github.com/your-username/tableau-agent-toolkit.git
cd tableau-agent-toolkit

# Install with dev dependencies
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install
```

## Code Style

- **Linting and formatting**: We use [ruff](https://docs.astral.sh/ruff/) as the
  sole linter and formatter. Run `ruff check .` and `ruff format .` before
  committing.
- **Type checking**: We use [mypy](https://mypy.readthedocs.io/) in strict mode.
  Run `mypy src/` before committing.

## Running Tests

```bash
# Run all unit tests
pytest tests/unit -x -q

# Run with coverage
pytest tests/unit --cov=tableau_agent_toolkit --cov-report=term-missing
```

## Commit Messages

We follow [Conventional Commits](https://www.conventionalcommits.org/):

- `feat(scope): description` for new features
- `fix(scope): description` for bug fixes
- `docs(scope): description` for documentation changes
- `refactor(scope): description` for code refactoring
- `test(scope): description` for test additions
- `chore(scope): description` for build/tooling changes
