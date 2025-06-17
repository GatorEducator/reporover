# RepoRover Plan

## Documentation Requirements

All documentation should follow these standards:

- README files should use clear section headers with emoji prefixes for visual organization.
- Code examples in documentation should be complete and runnable.
- All command-line examples should include the `$` prompt prefix to indicate terminal commands.
- Documentation should specify exact file paths when referencing project files.
- All URLs in documentation should be complete and functional.
- Source code examples should be as realistic as possible, reflecting actual usage patterns.
- All documentation should be written in Markdown format and visible on GitHub.
- A special version of the documentation in the README.md file is always
maintained in the file called `README_PYTHON.md`. The purpose of this file is to
contain all the same content in the `README.md` file, excepting the fact that it
should not contain emojis or graphics or other elements that do not appear on PyPI.

## Project Structure Requirements

The project should maintain this structure:

- Source code should be in `src/reporover/` directory.
- Tests should be in `tests/` directory with matching structure to source.
- Documentation should be in `docs/` directory.
- Configuration files should be in the project root.
- GitHub Actions workflows should be in `.github/workflows/` directory.

## Infrastructure Requirements

- Use `uv` for managing the dependencies, virtual environments, and task running.
- System should be written so that they work on MacOS, Linux, and Windows.
- System should support Python 3.11, 3.12, and 3.13.
- The `pyproject.toml` file should be used to manage dependencies and encoded project metadata.

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
requirements above in the subsection called "Code Requirements".
- Test cases should have a descriptive name that starts with `test_`.
- Test cases should be grouped by the function they are testing.
- Test cases should be ordered in a way that makes sense to the reader.
- Test cases should be independent of each other so that they can be run in a
random order without affecting the results or each other.
- Test cases must work both on a local machine and in a CI environment, meaning
that they should work on a laptop and in GitHub Actions.
- Test cases should aim to achieve full function, statement, and branch coverage
so as to ensure that the function in the program is thoroughly tested.

## Code Generation Guidelines

When generating new code or test cases, follow these specific patterns:

### Function and Class Patterns

- All functions must have type hints for parameters and return values.
- Use `Path` from `pathlib` for all file system operations, never string paths.
- Rich console output should use the existing `rich` patterns in the codebase.
- All CLI commands should use Typer with explicit type annotations.
- Error handling should use specific exception types, not generic `Exception`.
- If a function contains comments inside of it and the function is going
to be refactored, never remove those comments that are still relevant to
the new implementation of the function. Only delete comments or remove all of
the comments from a function subject to refactoring if it is absolutely needed.

### Import Organization

- Group imports in this order: standard library, third-party, local imports.
- Use absolute imports for all local modules (`from reporover.module import ...`).
- Import only what is needed, avoid wildcard imports.
- Follow the existing import patterns seen in the codebase.

### Naming Conventions

- Use snake_case for all functions, variables, and module names.
- Use PascalCase for class names.
- Constants should be UPPER_SNAKE_CASE.
- Private functions should start with underscore.
- CLI argument should use hyphens (handled by Typer).
- CLI sub-commands should be a single word like `clone` or `commit`.

### Testing Patterns

- Test files should mirror the source structure (e.g., `tests/test_main.py` for
`src/reporover/main.py`).
- Use descriptive test names that explain what is being tested.
- Group related tests in the same file and use clear organization.
- Mock external dependencies (GitHub API, file system) in tests.
- Use pytest fixtures for common test setup.
- Include both positive and negative test cases.
- Test edge cases and error conditions.
- Write property-based test cases using Hypothesis where applicable. Make sure
that all the property-based are marked with the decorator called `@pytest.mark.property`
so that they can be run separately from the other tests when needed.

### CLI Command Patterns

- All commands should provide helpful messages for use with the `--help`
provided by Typer.
- Use consistent parameter names across commands (e.g., `github_org_url`
and `repo_prefix`).
- Include progress indicators for long-running operations.
- Validate inputs early and provide clear feedback.
- Use the existing Rich console styling patterns.

### Error Handling Patterns

- Catch specific exceptions and provide meaningful error messages.
- Use early returns to avoid deep nesting.
- Log errors appropriately without exposing sensitive information.
- Provide actionable error messages to users.

### GitHub API Integration

- When appropriate to do so and unless instructed otherwise,
  use the PyGitHub approach unless it is not a good idea to do so.
- Use the existing request patterns with proper authentication.
- Handle rate limiting and network errors gracefully.
- Cache responses when appropriate to avoid redundant API calls.
- Follow the existing patterns for API endpoint construction.

### File Operations

- Use `pathlib.Path` for all file operations.
- Handle file permissions and access errors gracefully.
- Use context managers for file operations.
- Validate file paths and existence before operations.

## Context Requirements for LLM Assistance

To generate the most accurate code, always provide:

### Essential Context

- The specific module or function being modified or extended.
- Related functions or classes that might be affected.
- Existing error handling patterns in similar functions.
- The expected input/output format for the new functionality.

### Testing Context

- Existing test patterns for similar functionality.
- Mock objects and fixtures already in use.
- Test data structures and formats.
- Integration test requirements vs unit test requirements.

### Integration Context

- How the new code fits into existing CLI commands.
- Dependencies on other modules or external services.
- Configuration requirements or environment variables.
- Backward compatibility requirements.

## New Features

### `discover` Command

#### Task Guidelines

- The implementation of this command should adhere to all the rules described in
all the previous sections.
- The implementation should proceed on a small-scale basis. It must implement a
part of a feature before checking back to confirm that the systems is as desired
and whether or not it is in accordance with the rules described in this
document.

#### Task Description

- A command-line interface implemented in Typer that is similar to the ones
provided previously in that it should accept a GitHub access token.
- The overall purpose of the `discover` command is to query the GitHub REST API
through the use of PyGitHub to search for public GitHub repositories that match
the provided search criteria. If it is not possible to implement a feature using
the PyGitHub library, then it is acceptable to use the `requests` library.
- The search criteria:
    - Could all be `None` if they are not provided.
    - Must be specified as command-line arguments.
    - As a start, they should focus on the following:
        - `language`: The programming language of the repository.
        - `stars`: The minimum number of stars the repository should have.
        - `forks`: The minimum number of forks the repository should have.
        - `created_after`: The date after which the repository was created.
        - `updated_after`: The date after which the repository was last updated.
    - The critical advanced feature in the following:
        - `files`: A list of exact file names that the repository should
        contain.
        - `max_depth`: The maximum depth of the repository's directory structure
        to search for the files. For this critical advanced feature, the value
        of `max_depth` should be an integer greater than or equal to 0. The
        value of zero should indicate that the search should only recursively
        search into the root of the repository. A value of 1 would indicate that
        the search should recursively go into all of the directories that are
        contained in the root of the repository, and so on.
        - An example of this critical advanced feature would allow this
        subcommand to discover repositories that only contain a `uv.lock` file
        and a `pyproject.toml` file in the root of the repository.
        - Please note that for this critical advanced feature, the word "files"
        designates either a file or a "directory". This means that the feature
        should work correctly whether it is searching for a directory called
        `tests` or a file called `uv.lock`.
        - Please note that this critical advanced feature requires the existence
        of all the files specified in the `files` argument of the command-line.
    - The additional advanced features of the search criteria are the following:
        - `topics`: A list of topics that the repository should have.
        - `license`: The license of the repository.
        - `size`: The minimum size of the repository in kilobytes.
        - `has_issues`: Whether the repository should have issues enabled.
        - `has_wiki`: Whether the repository should have a wiki enabled.
