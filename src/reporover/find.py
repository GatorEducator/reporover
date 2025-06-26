"""Module for finding private GitHub repositories using search criteria."""

from typing import Optional

import github
from rich.console import Console
from rich.progress import BarColumn, Progress, TextColumn

from reporover.constants import StatusCode, Symbols


def find_repositories(  # noqa: PLR0913
    console: Console,
    token: str,
    organization: str,
    name: Optional[str],
    language: Optional[str],
    stars: Optional[int],
    forks: Optional[int],
    created_after: Optional[str],
    updated_after: Optional[str],
) -> StatusCode:
    """Find private GitHub repositories in an organization matching the provided criteria."""
    # perform the search of the private repositories that
    # are in the specified GitHub organization using the provided search parameters
    try:
        # create a GitHub API instance using PyGitHub
        # and the provided GitHub access token
        github_instance = github.Github(token)
        # get the organization object to access its repositories
        try:
            org = github_instance.get_organization(organization)
        except github.UnknownObjectException:
            console.print(
                f"{Symbols.ERROR.value} Organization '{organization}' not found or not accessible"
            )
            return StatusCode.FAILURE
        except github.GithubException as github_error:
            console.print(
                f"{Symbols.ERROR.value} Failed to access organization '{organization}': {github_error}"
            )
            return StatusCode.FAILURE
        # get all repositories from the organization
        # note that this will include both public and private repositories
        # that are accessible to the authenticated user
        repositories = org.get_repos()
        console.print(
            f":mag: Searching repositories in organization: {organization}"
        )
        # filter repositories based on the provided criteria
        filtered_repositories = _filter_repositories_by_criteria(
            repositories,
            name,
            language,
            stars,
            forks,
            created_after,
            updated_after,
            console,
        )
        # display the search results
        _display_find_results(filtered_repositories, console, organization)
        return StatusCode.SUCCESS
    # handle any errors that may occur during the process of finding,
    # making sure that the subcommand and then the reporover tool returns
    # the current exit code to communicate with the operating system
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


def _filter_repositories_by_criteria(  # noqa: PLR0913
    repositories,
    name: Optional[str],
    language: Optional[str],
    stars: Optional[int],
    forks: Optional[int],
    created_after: Optional[str],
    updated_after: Optional[str],
    console: Console,
) -> list:
    """Filter repositories based on the provided criteria."""
    # initialize the list to hold filtered repositories
    filtered_repos = []
    # convert the repositories paginated list to a list for counting
    # and filtering through the repositories
    try:
        repos_list = list(repositories)
        total_repos = len(repos_list)
        console.print(
            f":mag: Processing {total_repos} accessible repositories"
        )
        console.print()
    except Exception:
        console.print(f"{Symbols.ERROR.value} Failed to access repositories")
        return []
    # filter the repositories and display output in the
    # context of a progress bar from rich
    with Progress(
        "[progress.description]{task.description}",
        BarColumn(),
        "[progress.percentage]{task.percentage:>3.0f}%",
        TextColumn("[progress.completed]{task.completed}/{task.total}"),
    ) as progress:
        task = progress.add_task(
            "[green]Filtering Repositories", total=total_repos
        )
        # iteratively filter through each of the repositories, only
        # keeping a repository as a match if it meets all criteria
        for repository in repos_list:
            # check if the repository matches all the specified criteria
            if _repository_matches_criteria(
                repository,
                name,
                language,
                stars,
                forks,
                created_after,
                updated_after,
            ):
                filtered_repos.append(repository)
                progress.console.print(
                    f"{Symbols.CHECK.value} Found matching repository: {repository.name}"
                )
            # update the progress bar
            progress.update(task, advance=1)
    # return the filtered repositories
    return filtered_repos


def _repository_matches_criteria(  # noqa: PLR0911, PLR0913
    repository,
    name: Optional[str],
    language: Optional[str],
    stars: Optional[int],
    forks: Optional[int],
    created_after: Optional[str],
    updated_after: Optional[str],
) -> bool:
    """Check if a repository matches all the specified criteria."""
    try:
        # check name fragment if specified
        if name and name not in repository.name:
            return False
        # check language if specified
        if language and repository.language != language:
            return False
        # check minimum stars if specified
        if stars is not None and repository.stargazers_count < stars:
            return False
        # check minimum forks if specified
        if forks is not None and repository.forks_count < forks:
            return False
        # check created after date if specified
        if created_after:
            try:
                from datetime import datetime

                created_date = repository.created_at.date()
                after_date = datetime.strptime(
                    created_after, "%Y-%m-%d"
                ).date()
                if created_date < after_date:
                    return False
            except (ValueError, AttributeError):
                return False
        # check updated after date if specified
        if updated_after:
            try:
                from datetime import datetime

                updated_date = repository.updated_at.date()
                after_date = datetime.strptime(
                    updated_after, "%Y-%m-%d"
                ).date()
                if updated_date < after_date:
                    return False
            except (ValueError, AttributeError):
                return False
        # if all criteria pass, return True
        return True
    # if there was any error checking the criteria,
    # consider the repository as not matching
    except Exception:
        return False


def _display_find_results(
    repositories: list, console: Console, organization: str
) -> None:
    """Display the find results in a formatted table."""
    from rich import box
    from rich.table import Table

    from reporover.constants import Symbols

    table = Table(
        title=f"Repository Find Results for Organization: {organization}",
        box=box.SIMPLE_HEAVY,
    )
    table.add_column("Name", style="cyan", no_wrap=False)
    table.add_column("Description", style="magenta")
    table.add_column("Stars", justify="right", style="green")
    table.add_column("Forks", justify="right", style="yellow")
    table.add_column("Language", style="blue")
    table.add_column("Updated", style="white")
    table.add_column("Private", style="red")
    # add repositories to the table
    for repository in repositories:
        description = repository.description or "No description"
        if len(description) > 50:  # noqa: PLR2004
            description = description[:47] + "..."
        language_display = repository.language or Symbols.UNKNOWN.value
        updated_date = repository.updated_at.strftime("%Y-%m-%d")
        private_status = "Yes" if repository.private else "No"
        table.add_row(
            repository.name,
            description,
            str(repository.stargazers_count),
            str(repository.forks_count),
            language_display,
            updated_date,
            private_status,
        )
    console.print()
    console.print(table)
    console.print(
        f":information: Found {len(repositories)} repositories matching criteria"
    )
