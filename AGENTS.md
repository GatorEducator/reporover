# AGENTS.md

This document provides guidelines for AI agents contributing to this repository.
For more detailed instructions, especially for Gemini agents, please refer to
`GEMINI.md`.

## Build, Lint, and Test Commands

- **Install dependencies:** `uv sync --dev`
- **Run all tasks:** `uv run task all`
- **Run all linters:** `uv run task lint`
- **Format code:** `uv run task format` (check), `uv run task format-fix` (fix)
- **Lint code:** `uv run task check`
- **Type check:** `uv run task mypy`, `uv run task ty`, `uv run task symbex`
- **Test all:** `uv run task test`
- **Test with coverage:** `uv run task test-coverage`
- **Test variants:** `uv run task test-not-property`, `uv run task test-not-random`,
  `uv run task test-silent`
- **Run a single test:** `pytest tests/test_file.py::test_function` or
  `uv run pytest tests/test_file.py::test_function`
- **Markdown lint:** `uv run task markdownlint`

## Code Requirements

All the Python code should follow these standards:

- **Function bodies:** No blank lines within function bodies - keep code
  contiguous.
- **Docstrings:** Single-line docstrings starting with a capital letter, ending
  with a period.
- **Comments:** Other comments start with a lowercase letter; preserve existing
  comments during refactoring.
- **Imports:** Group imports in this order: standard library, third-party, local
  imports. Use absolute imports (`from reporover.module import`).
- **Formatting:** Use `ruff format` (line length 79 for lint, 88 for isort);
  trailing commas enabled.
- **Types:** All functions must have type hints for parameters and return values.
- **Naming:** snake_case for functions/variables, PascalCase for classes,
  UPPER_SNAKE_CASE for constants.
- **File operations:** Use `pathlib.Path` for all file system operations, never
  string paths.
- **Error handling:** Use specific exceptions, not generic `Exception`; provide
  meaningful error messages.
- **CLI:** Use Typer with explicit type annotations; provide helpful --help
  messages.
- **GitHub API:** Prefer PyGitHub unless requests library is more appropriate.

## Project Structure Requirements

- Source code in `src/reporover/` directory.
- Tests in `tests/` directory with matching structure to source.
- Use `uv` for dependency management, virtual environments, and task running.
- Support Python 3.11, 3.12, and 3.13 on MacOS, Linux, and Windows.
- Use Pydantic models for data validation and JSON serialization.

## Test Requirements

All test cases should follow these standards:

- Since a test case is a Python function, it should always follow the code
  requirements above.
- Test cases should have a descriptive name that starts with `test_`.
- Test cases should be grouped by the function they are testing.
- Test cases should be ordered in a way that makes sense to the reader.
- Test cases should be independent of each other so that they can be run in a
  random order without affecting the results or each other.
- Test cases must work both on a local machine and in a CI environment.
- Test cases should aim to achieve full function, statement, and branch
  coverage.
- Property-based tests must be marked with `@pytest.mark.property`.

## Making Changes

1.  **Understand:** Thoroughly understand the request and the relevant codebase.
    Use the available tools to explore the code.
2.  **Plan:** Formulate a clear plan before making any changes.
3.  **Implement:** Make small, incremental changes.
4.  **Verify:** Run `uv run task all` to ensure your changes are correct and
    follow the project's style.
5.  **Commit:** Write a clear and concise commit message explaining the "why" of
    your changes.
