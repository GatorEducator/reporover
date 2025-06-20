"""Module for discovering GitHub repositories using search criteria."""

from typing import List, Optional

import github
import requests
from rich import box
from rich.console import Console
from rich.progress import BarColumn, Progress, TextColumn
from rich.table import Table

from reporover.constants import Numbers, StatusCode, Symbols

MAX_DEPTH = Numbers.MAX_DEPTH.value
MAX_DISPLAY = Numbers.MAX_KEEP.value
MAX_FILTER = Numbers.MAX_FILTER.value


def search_repositories(  # noqa: PLR0912, PLR0913, PLR0915
    console: Console,
    token: str,
    language: Optional[str],
    stars: Optional[int],
    forks: Optional[int],
    created_after: Optional[str],
    updated_after: Optional[str],
    files: Optional[List[str]],
    topics: Optional[List[str]],
    max_depth: Optional[int] = Numbers.MAX_DEPTH.value,
    max_filter: Optional[int] = Numbers.MAX_FILTER.value,
    max_display: Optional[int] = Numbers.MAX_KEEP.value,
    save_file: Optional[str] = None,
) -> StatusCode:
    """Search for public GitHub repositories matching the provided criteria."""
    # define the global variables based on the command-line arguments
    # that were input by the caller of this function and passed here
    global MAX_DEPTH, MAX_DISPLAY, MAX_FILTER  # noqa: PLW0603
    if max_depth is None:
        max_depth = MAX_DEPTH
    else:
        MAX_DEPTH = max_depth
    if max_filter is None:
        max_filter = MAX_FILTER
    else:
        MAX_FILTER = max_filter
    if max_display is None:
        max_display = MAX_DISPLAY
    else:
        MAX_DISPLAY = max_display
    try:
        # create a GitHub API instance using PyGitHub
        # and the provided GitHub access token
        github_instance = github.Github(token)
        # create the search query based on the provided parameters;
        # note that if there are no provided parameters then this
        # function will create a default, benign query that works
        search_query = _build_search_query(
            language, stars, forks, created_after, updated_after, topics
        )
        console.print(f":mag: Search query: {search_query}")
        # use the GitHub API to search for repositories with PyGitHub
        repositories = github_instance.search_repositories(search_query)
        # prepare configuration data for saving; note that this is
        # only for placeholder purposes and will be populated later
        configuration_data = {
            "language": language,
            "stars": stars,
            "forks": forks,
            "created_after": created_after,
            "updated_after": updated_after,
            "files": files,
            "topics": topics,
            "max_depth": max_depth,
            "max_filter": max_filter,
            "max_display": max_display,
        }
        # if there are files to filter by, then filter the repositories
        # so that only those are ultimately displayed/saved if they
        # contain all of the specified files at the specified depth
        if files:
            # display debugging information about the filtering
            console.print(
                f":mag: Processing the {repositories.totalCount} accessible repositories"
            )
            console.print(
                f":mag: Performing filtering for at most {max_filter} first repositories"
            )
            console.print(
                f":mag: Filtering repositories for files and/or directories: {files}"
            )
            console.print(
                f":mag: Maximum search depth during file filtering: {max_depth}"
            )
            console.print()
            # filter and then display the results of the discover process
            filtered_repositories = _filter_repositories_by_files(
                repositories, files, max_depth, token, console
            )
            _display_search_results_with_files(
                filtered_repositories, console, files
            )
            # save results to a JSON file if saving of data was requested
            if save_file:
                success = _save_results_to_json(
                    filtered_repositories,
                    save_file,
                    configuration_data,
                    search_query,
                    files,
                )
                if success:
                    console.print(
                        f":information: Discovery results saved to {save_file}"
                    )
                else:
                    console.print(
                        f"{Symbols.ERROR.value} Failed to save results to {save_file}"
                    )
                    return StatusCode.FAILURE
        # no additional filtering by files was requested, so these repositories
        # can be displayed (and, if requested, saved) without any more steps
        else:
            console.print()
            console.print(
                f":information: Processing the {repositories.totalCount} accessible repositories"
            )
            console.print()
            _display_search_results(repositories, console)
            # save results if requested
            if save_file:
                # convert the repositories generator (i.e., you have to fetch
                # all of the data incrementally) to list for saving
                repos_list = list(repositories[:max_display])
                # save results to a JSON file if saving of data was requested
                success = _save_results_to_json(
                    repos_list, save_file, configuration_data, search_query
                )
                if success:
                    console.print(
                        f":information: Discovery results saved to {save_file}"
                    )
                else:
                    console.print(
                        f"{Symbols.ERROR.value} Failed to save results to {save_file}"
                    )
                    return StatusCode.FAILURE
        return StatusCode.SUCCESS
    # handle any errors that may occur during the process of discovery,
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


def _build_search_query(  # noqa: PLR0913
    language: Optional[str],
    stars: Optional[int],
    forks: Optional[int],
    created_after: Optional[str],
    updated_after: Optional[str],
    topics: Optional[List[str]],
) -> str:
    """Build a GitHub search query string from the provided criteria."""
    # create a list of search query parts
    query_parts = []
    # add filters to the query based on the provided parameters;
    # note that each of these filters is an index in the list
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
    # since there can be more or more topics, make sure
    # to add all of the provided topics to the query; note
    # that each topic is prefixed with "topic:" and then
    # added to the query_parts list as its own element
    if topics:
        for topic in topics:
            query_parts.append(f"topic:{topic}")
    # the construction requires that there must be some query;
    # as such, if no elements were specified for the parts of
    # the query make the query a benign one that only looks
    # for public repositories on GitHub
    if not query_parts:
        query_parts.append("is:public")
    # return the constructed query by separating the elements
    # with a space to form a valid GitHub search query
    return " ".join(query_parts)


def _filter_repositories_by_files(
    repositories,
    required_files: List[str],
    max_depth: int,
    token: str,
    console: Console,
) -> List:
    """Filter repositories that contain the specified files and directories within max_depth."""
    # initialize the list to hold filtered repositories
    # and setup default values for the filtering
    filtered_repos = []
    repo_count = 0
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
    }
    # console is not used directly in this function,
    # so we can just assign it to a not-used variable
    _ = console
    # filter the repositories and display output in the
    # context of a progress bar from rich
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
        # iteratively filter through each of the repositories, only
        # keeping a repository as a match if it contains all of the
        # specified files at or before the specified depth
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
    # return the filtered repositories
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


def _save_results_to_json(
    repositories: List,
    save_file: str,
    configuration_data: dict,
    search_query: str,
    required_files: Optional[List[str]] = None,
) -> bool:
    """Save the repository search results to a JSON file using Pydantic models."""
    # attempt to use Pydantic models to save the data to
    # a JSON file that will have the required format
    try:
        from reporover.models import (
            DiscoverConfiguration,
            RepoRoverData,
            RepositoryInfo,
        )
        # create the configuration model
        config_dict = configuration_data.copy()
        config_dict["search_query"] = search_query
        # timestamp will be automatically set by the model's default_factory
        configuration = DiscoverConfiguration(**config_dict)

        # create repository models
        repo_models = []
        for repo in repositories:
            repo_info = RepositoryInfo(
                name=repo.name,
                url=repo.html_url,
                description=repo.description,
                language=repo.language,
                stars=repo.stargazers_count,
                forks=repo.forks_count,
                created_at=repo.created_at,
                updated_at=repo.updated_at,
                files=required_files if required_files else None,
            )
            repo_models.append(repo_info)

        # create the complete data structure
        reporover_data = RepoRoverData.create_discover_data(
            configuration, repo_models
        )

        # write to JSON file
        import json

        with open(save_file, "w", encoding="utf-8") as file:
            json.dump(reporover_data.model_dump(), file, indent=2, default=str)

        return True
    except Exception:
        return False


def _display_search_results(repositories, console: Console) -> None:
    """Display the search results in a formatted table when there is no file filtering."""
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
    total_count = repositories.totalCount
    display_count = min(total_count, max_results)
    with Progress(
        "[progress.description]{task.description}",
        BarColumn(),
        "[progress.percentage]{task.percentage:>3.0f}%",
        TextColumn("[progress.completed]{task.completed}/{task.total}"),
    ) as progress:
        task = progress.add_task(
            "[green]Processing Repositories", total=display_count
        )
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
            progress.update(task, advance=1)
    console.print()
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
    total_count = len(repositories)
    display_count = min(total_count, max_results)
    with Progress(
        "[progress.description]{task.description}",
        BarColumn(),
        "[progress.percentage]{task.percentage:>3.0f}%",
        TextColumn("[progress.completed]{task.completed}/{task.total}"),
    ) as progress:
        task = progress.add_task(
            "[green]Processing Repositories", total=display_count
        )
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
            progress.update(task, advance=1)
    console.print()
    console.print(table)
    console.print(
        f":information: Found {total_count} repositories after filtering"
    )
    if total_count > max_results:
        console.print(
            f":information: Showing first {max_results} repositories"
        )
