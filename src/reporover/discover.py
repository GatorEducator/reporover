"""Module for discovering GitHub repositories using search criteria."""

from typing import List, Optional

import github
import requests
from rich import box
from rich.console import Console
from rich.progress import BarColumn, Progress, TextColumn
from rich.table import Table

from reporover.constants import Numbers, StatusCode, Symbols

MAX_DISPLAY = Numbers.MAX_DISPLAY.value
MAX_FILTER = Numbers.MAX_FILTER.value


def search_repositories(  # noqa: PLR0913
    token: str,
    language: Optional[str],
    stars: Optional[int],
    forks: Optional[int],
    created_after: Optional[str],
    updated_after: Optional[str],
    files: Optional[List[str]],
    topics: Optional[List[str]],
    max_depth: int,
    max_filter: int,
    max_display: int,
    console: Console,
) -> StatusCode:
    """Search for public GitHub repositories matching the provided criteria."""
    global MAX_DISPLAY, MAX_FILTER  # noqa: PLW0603
    MAX_DISPLAY = max_display
    MAX_FILTER = max_filter
    try:
        github_instance = github.Github(token)
        search_query = _build_search_query(
            language, stars, forks, created_after, updated_after, topics
        )
        console.print(f":mag: Search query: {search_query}")
        repositories = github_instance.search_repositories(search_query)
        if files:
            console.print(
                f":mag: Performing filtering for first {max_filter} repositories"
            )
            console.print(
                f":mag: Filtering repositories for files and/or directories: {files}"
            )
            console.print(
                f":mag: Maximum search depth during file filtering: {max_depth}"
            )
            console.print()
            filtered_repositories = _filter_repositories_by_files(
                repositories, files, max_depth, token, console
            )
            _display_search_results_with_files(
                filtered_repositories, console, files
            )
        else:
            console.print()
            console.print(
                f":information: Initially discovered {repositories.totalCount} repositories"
            )
            console.print()
            _display_search_results(repositories, console)
        return StatusCode.SUCCESS
    except github.GithubException as github_error:
        console.print(
            f"{Symbols.ERROR.value} GitHub API error: {github_error}"
        )
        return StatusCode.FAILURE
    except Exception as general_error:
        console.print(
            f"{Symbols.ERROR.value} Unexpected error: {general_error}"
        )
        return StatusCode.FAILURE


def _build_search_query(
    language: Optional[str],
    stars: Optional[int],
    forks: Optional[int],
    created_after: Optional[str],
    updated_after: Optional[str],
    topics: Optional[List[str]],
) -> str:
    """Build a GitHub search query string from the provided criteria."""
    query_parts = []
    if language:
        query_parts.append(f"language:{language}")
    if stars is not None:
        query_parts.append(f"stars:>={stars}")
    if forks is not None:
        query_parts.append(f"forks:>={forks}")
    if created_after:
        query_parts.append(f"created:>={created_after}")
    if updated_after:
        query_parts.append(f"pushed:>={updated_after}")
    if topics:
        for topic in topics:
            query_parts.append(f"topic:{topic}")
    if not query_parts:
        query_parts.append("is:public")
    return " ".join(query_parts)


def _filter_repositories_by_files(
    repositories,
    required_files: List[str],
    max_depth: int,
    token: str,
    console: Console,
) -> List:
    """Filter repositories that contain the specified files and directories within max_depth."""
    filtered_repos = []
    repo_count = 0
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
    }
    _ = console
    max_filter_runs = min(repositories.totalCount, MAX_FILTER)
    with Progress(
        "[progress.description]{task.description}",
        BarColumn(),
        "[progress.percentage]{task.percentage:>3.0f}%",
        TextColumn("[progress.completed]{task.completed}/{task.total}"),
    ) as progress:
        task = progress.add_task(
            "[green]Filtering Repositories", total=max_filter_runs
        )
        for repository in repositories:
            if repo_count >= MAX_FILTER:
                break
            if _repository_contains_files(
                repository, required_files, max_depth, headers
            ):
                filtered_repos.append(repository)
                progress.console.print(
                    f"{Symbols.CHECK.value} Found all designated files in {repository.name}"
                )
            repo_count += 1
            progress.update(task, advance=1)
    return filtered_repos


def _repository_contains_files(
    repository,
    required_files: List[str],
    max_depth: int,
    headers: dict,
) -> bool:
    """Check if repository contains all required files and directories within the specified depth."""
    try:
        found_files = set()
        repo_files = _get_repository_files(repository, max_depth, headers)
        for file_info in repo_files:
            file_name = file_info.get("name", "")
            if file_name in required_files:
                found_files.add(file_name)
        return len(found_files) == len(required_files)
    except Exception:
        return False


def _get_repository_files(
    repository, max_depth: int, headers: dict
) -> List[dict]:
    """Get all files and directories in a GitHub repository up to specified depth."""
    all_files: List[dict] = []
    try:
        _collect_files_recursive(
            repository.full_name, "", max_depth, 0, headers, all_files
        )
    except Exception:
        pass
    return all_files


def _collect_files_recursive(  # noqa: PLR0913
    repo_full_name: str,
    path: str,
    max_depth: int,
    current_depth: int,
    headers: dict,
    all_files: List[dict],
) -> None:
    """Recursively collect files and directories from a GitHub repository up to a maximum depth."""
    if current_depth > max_depth:
        return
    api_url = f"https://api.github.com/repos/{repo_full_name}/contents/{path}"
    try:
        response = requests.get(api_url, headers=headers, timeout=10)
        if response.status_code != StatusCode.WORKING.value:
            return
        contents = response.json()
        if not isinstance(contents, list):
            return
        for item in contents:
            if item.get("type") == "file":
                all_files.append(item)
            elif item.get("type") == "dir":
                all_files.append(item)
                if current_depth < max_depth:
                    _collect_files_recursive(
                        repo_full_name,
                        item.get("path", ""),
                        max_depth,
                        current_depth + 1,
                        headers,
                        all_files,
                    )
    except Exception:
        pass


def _display_search_results(repositories, console: Console) -> None:
    """Display the search results in a formatted table."""
    table = Table(
        title="Repository Search Results (No Filtering by Files and/or Directories)",
        box=box.SIMPLE_HEAVY,
    )
    table.add_column("Name", style="cyan", no_wrap=False)
    table.add_column("Description", style="magenta")
    table.add_column("Stars", justify="right", style="green")
    table.add_column("Forks", justify="right", style="yellow")
    table.add_column("Language", style="blue")
    table.add_column("Updated", style="white")
    repository_count = 0
    max_results = MAX_DISPLAY
    for repository in repositories:
        if repository_count >= max_results:
            break
        if len(repository.name) > Numbers.MAX_NAME_LENGTH.value:
            repository_name = (
                repository.name[: Numbers.MAX_NAME_LENGTH.value - 10]
                + Symbols.ELLIPSIS.value
                + "   "
            )
            repository_name = repository_name.strip()
        else:
            repository_name = repository.name
        description = repository.description or "No description"
        if len(description) > Numbers.MAX_DESCRIPTION_LENGTH.value:
            description = (
                description[: Numbers.MAX_DESCRIPTION_LENGTH.value - 3]
                + Symbols.ELLIPSIS.value
            )
        language_display = repository.language or Symbols.UNKNOWN.value
        updated_date = repository.updated_at.strftime("%Y-%m-%d")
        table.add_row(
            repository_name,
            description,
            str(repository.stargazers_count),
            str(repository.forks_count),
            language_display,
            updated_date,
        )
        repository_count += 1
    total_count = repositories.totalCount
    console.print(table)
    console.print(f":information: Discovered {total_count} total repositories")
    if total_count > max_results:
        console.print(
            f":information: Showing first {max_results} repositories"
        )


def _display_search_results_with_files(
    repositories: List, console: Console, required_files: List[str]
) -> None:
    """Display the search results for repositories filtered by files and/or directories."""
    table = Table(
        title="Repository Search Results (Filtered by Files and/or Directories)",
        box=box.SIMPLE_HEAVY,
    )
    table.add_column("Name", style="cyan", no_wrap=True)
    table.add_column("Description", style="magenta")
    table.add_column("Stars", justify="right", style="green")
    table.add_column("Forks", justify="right", style="yellow")
    table.add_column("Language", style="blue")
    table.add_column("Updated", style="white")
    table.add_column("Files Found", style="bright_green")
    repository_count = 0
    max_results = MAX_DISPLAY
    for repository in repositories:
        if repository_count >= max_results:
            break
        description = repository.description or "No description"
        if len(description) > Numbers.MAX_DESCRIPTION_LENGTH.value:
            description = (
                description[: Numbers.MAX_DESCRIPTION_LENGTH.value - 3]
                + Symbols.ELLIPSIS.value
            )
        language_display = repository.language or Symbols.UNKNOWN.value
        updated_date = repository.updated_at.strftime("%Y-%m-%d")
        files_display = ", ".join(required_files)
        table.add_row(
            repository.name,
            description,
            str(repository.stargazers_count),
            str(repository.forks_count),
            language_display,
            updated_date,
            files_display,
        )
        repository_count += 1
    console.print()
    console.print(table)
    total_count = len(repositories)
    console.print(
        f":information: Found {total_count} repositories after filtering"
    )
    if total_count > max_results:
        console.print(
            f":information: Showing first {max_results} repositories"
        )
