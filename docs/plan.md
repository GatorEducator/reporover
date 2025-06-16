# RepoRover Plan

## Infrastructure Requirements

- Use `uv` for managing the dependencies, virtual environments, and task running
- System should be written so that they work on MacOS, Linux, and Windows
- System should support Python 3.11, 3.12, and 3.13.
- The `pyproject.toml` file should be used to manage dependencies and project metadata.

## Code Requirements

All the Python code should follow these standards:

- Function bodies should not have any blank lines in them
- Every function should have a docstring that starts with a capital letter and
ends with a period.
- All comments should start with a lowercase letter.
- All command-line interfaces should be created with Typer.

## Test Requirements

All test cases should follow these standards:

- Since a test case is a Python function, it should always follow the code
requirements above.
- Test cases should have a descriptive name that starts with `test_`.
- Test cases should be grouped by the function they are testing.
- Test cases should be ordered in a way that makes sense to the reader.
- Test cases should be independent of each other so that they can be
run in a random order without affecting the results or each other.
- Test cases must work both on a local machine and in a CI environment, 
meaning that they should work on a laptop and in GitHub Actions.
