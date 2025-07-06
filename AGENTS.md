# AGENTS.md

## Build, Lint, and Test Commands
- **Install dependencies:** `uv pip install -r requirements.txt` (or use `uv`/`pipx` as described in README)
- **Lint:** `task lint` (runs ruff, mypy, ty, symbex, markdownlint)
- **Format:** `task format` (check), `task format-fix` (fix)
- **Typecheck:** `task mypy`, `task ty`, `task symbex`
- **Test all:** `task test` (runs pytest with verbosity)
- **Test with coverage:** `task test-coverage`
- **Run a single test:** `pytest tests/test_file.py::test_function`

## Code Style Guidelines
- **Imports:** Use single-line imports, sorted by isort/ruff; trailing commas enabled.
- **Formatting:** Use `ruff format` (line length 79 for lint, 88 for isort).
- **Types:** All functions should be fully typed; use mypy and ty for enforcement.
- **Naming:** Use snake_case for functions/variables, PascalCase for classes.
- **Error Handling:** Use exceptions, not return codes; prefer explicit error messages.
- **Docs:** Use docstrings for all public functions/classes (pydocstyle enforced, but D203/D213/E501 ignored).
- **Testing:** Use pytest; property-based tests marked with `@pytest.mark.property`.
- **Markdown:** Lint with pymarkdown; config in `.pymarkdown.cfg`.

No Cursor or Copilot rules detected. See `pyproject.toml` for more details.
