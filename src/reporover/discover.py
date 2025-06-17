"""Module for discovering GitHub repositories using search criteria."""

from typing import Optional

import github
from rich.console import Console
from rich.table import Table

from reporover.constants import StatusCode


def search_repositories(  # noqa: PLR0913
    token: str,
    language: Optional[str],
    stars: Optional[int],
    forks: Optional[int],
    created_after: Optional[str],
    updated_after: Optional[str],
    console: Console,
) -> StatusCode:
    """Search for public GitHub repositories matching the provided criteria."""
    try:
        # create a GitHub instance with the provided token
        github_instance = github.Github(token)
        # build the search query based on the provided criteria
        search_query = _build_search_query(
            language, stars, forks, created_after, updated_after
        )
        # display the search query being used
        console.print(f":mag: Search query: {search_query}")
        console.print()
        # perform the search
        repositories = github_instance.search_repositories(search_query)
        # display the results
        _display_search_results(repositories, console)
        return StatusCode.SUCCESS
    except github.GithubException as github_error:
        console.print(f":x: GitHub API error: {github_error}")
        return StatusCode.FAILURE
    except Exception as general_error:
        console.print(f":x: Unexpected error: {general_error}")
        return StatusCode.FAILURE


def _build_search_query(
    language: Optional[str],
    stars: Optional[int],
    forks: Optional[int],
    created_after: Optional[str],
    updated_after: Optional[str],
) -> str:
    """Build a GitHub search query string from the provided criteria."""
    query_parts = []
    # add language filter if provided
    if language:
        query_parts.append(f"language:{language}")
    # add stars filter if provided
    if stars is not None:
        query_parts.append(f"stars:>={stars}")
    # add forks filter if provided
    if forks is not None:
        query_parts.append(f"forks:>={forks}")
    # add created date filter if provided
    if created_after:
        query_parts.append(f"created:>={created_after}")
    # add updated date filter if provided
    if updated_after:
        query_parts.append(f"pushed:>={updated_after}")
    # if no criteria provided, search for all public repositories
    # but limit to a reasonable scope
    if not query_parts:
        query_parts.append("is:public")
    return " ".join(query_parts)


def _display_search_results(repositories, console: Console) -> None:
    """Display the search results in a formatted table."""
    # create a table to display the results
    table = Table(title="Repository Search Results")
    table.add_column("Name", style="cyan", no_wrap=True)
    table.add_column("Description", style="magenta")
    table.add_column("Stars", justify="right", style="green")
    table.add_column("Forks", justify="right", style="yellow")
    table.add_column("Language", style="blue")
    table.add_column("Updated", style="white")
    # add repository information to the table
    # limit to first 10 results to avoid overwhelming output
    repository_count = 0
    max_results = 10
    for repository in repositories:
        if repository_count >= max_results:
            break
        # format the description to handle None values
        description = repository.description or "No description"
        if len(description) > 50:
            description = description[:47] + "..."
        # format the language to handle None values
        language_display = repository.language or "Unknown"
        # format the updated date
        updated_date = repository.updated_at.strftime("%Y-%m-%d")
        # add the row to the table
        table.add_row(
            repository.name,
            description,
            str(repository.stargazers_count),
            str(repository.forks_count),
            language_display,
            updated_date,
        )
        repository_count += 1
    # display the table
    console.print(table)
    console.print()
    # display summary information
    total_count = repositories.totalCount
    console.print(f":information: Found {total_count} repositories total")
    if total_count > max_results:
        console.print(f":information: Showing first {max_results} results")
