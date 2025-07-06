# AGENTS.md

## Build, Lint, and Test Commands

- **Install dependencies:** `uv sync --dev` (installs all dependencies including dev group)
- **Run all tasks:** `uv run task all` (runs lint, test, and test-coverage)
- **Run all linters:** `uv run task lint` (runs format, check, ty, mypy, symbex, markdownlint)
- **Format code:** `uv run task format` (check), `uv run task format-fix` (fix)
- **Lint code:** `uv run task check` (runs ruff linting checks)
- **Type check:** `uv run task mypy`, `uv run task ty`, `uv run task symbex`
- **Test all:** `uv run task test` (runs pytest with verbosity and randomization)
- **Test with coverage:** `uv run task test-coverage` (requires 80%+ coverage)
- **Test variants:** `uv run task test-not-property`, `uv run task test-not-random`, `uv run task test-silent`
- **Run a single test:** `pytest tests/test_file.py::test_function` or `uv run pytest tests/test_file.py::test_function`
- **Markdown lint:** `uv run task markdownlint` (lints README.md and docs/plan.md)

## Code Style Guidelines (from docs/plan.md)

- **Function bodies:** No blank lines within function bodies - keep code contiguous
- **Docstrings:** Single-line docstrings starting with capital letter, ending with period
- **Comments:** Other comments start with lowercase letter; preserve existing comments during refactoring
- **Imports:** Standard library, third-party, local imports; use absolute imports (`from reporover.module import`)
- **Formatting:** Use `ruff format` (line length 79 for lint, 88 for isort); trailing commas enabled
- **Types:** All functions must have type hints for parameters and return values
- **Naming:** snake_case for functions/variables, PascalCase for classes, UPPER_SNAKE_CASE for constants
- **File operations:** Use `pathlib.Path` for all file system operations, never string paths
- **Error handling:** Use specific exceptions, not generic `Exception`; provide meaningful error messages
- **CLI:** Use Typer with explicit type annotations; provide helpful --help messages
- **Testing:** Use pytest; property-based tests marked with `@pytest.mark.property`
- **GitHub API:** Prefer PyGitHub unless requests library is more appropriate

## Project Structure Requirements

- Source code in `src/reporover/` directory
- Tests in `tests/` directory with matching structure to source
- Use `uv` for dependency management, virtual environments, and task running
- Support Python 3.11, 3.12, and 3.13 on MacOS, Linux, and Windows
- Use Pydantic models for data validation and JSON serialization

No Cursor or Copilot rules detected. See `pyproject.toml` and `docs/plan.md` for complete details.
