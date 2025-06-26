"""Module for finding private GitHub repositories using search criteria."""

import json
from datetime import datetime
from typing import List, Optional, Set

import github
import requests
from rich import box
from rich.console import Console
from rich.progress import BarColumn, Progress, TextColumn
from rich.table import Table

from reporover.constants import FileSystem, Numbers, StatusCode, Symbols
from reporover.models import (
    DiscoverConfiguration,
    RepoRoverData,
    RepositoryInfo,
)

MAX_DEPTH = Numbers.MAX_DEPTH.value
MAX_DISPLAY = Numbers.MAX_KEEP.value
MAX_FILTER = Numbers.MAX_FILTER.value


def find_repositories(  # noqa: PLR0912, PLR0913, PLR0915
    console: Console,
    token: str,
    organization: str,
    name: Optional[str],
    language: Optional[str],
    stars: Optional[int],
    forks: Optional[int],
    created_after: Optional[str],
    updated_after: Optional[str],
    files: Optional[List[str]],
    max_depth: Optional[int] = Numbers.MAX_DEPTH.value,
    max_filter: Optional[int] = Numbers.MAX_FILTER.value,
    max_display: Optional[int] = Numbers.MAX_KEEP.value,
    save_file: Optional[str] = None,
) -> StatusCode:
    """Find private GitHub repositories in an organization matching the provided criteria."""
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
        # display all of the search criteria as long as they are not None
        if name:
            console.print(f":mag: Repository name fragment: {name}")
        if language:
            console.print(f":mag: Repository programming language: {language}")
        if stars:
            console.print(f":mag: Repository minimum stars: {stars}")
        if forks:
            console.print(f":mag: Repository minimum forks: {forks}")
        if created_after:
            console.print(f":mag: Created after: {created_after} (YYYY-MM-DD)")
        if updated_after:
            console.print(f":mag: Updated after: {updated_after} (YYYY-MM-DD)")
        if files:
            console.print(f":mag: Required files and/or directories: {files}")
            console.print(
                f":mag: Maximum search depth during file filtering: {max_depth}"
            )
        # prepare configuration data for saving; note that this is
        # only for placeholder purposes and will be populated later
        configuration_data = {
            "organization": organization,
            "name": name,
            "language": language,
            "stars": stars,
            "forks": forks,
            "created_after": created_after,
            "updated_after": updated_after,
            "files": files,
            "max_depth": max_depth,
            "max_filter": max_filter,
            "max_display": max_display,
        }
        # filter repositories based on the provided criteria
        filtered_repositories = _filter_repositories_by_criteria(
            repositories,
            name,
            language,
            stars,
            forks,
            created_after,
            updated_after,
            files,
            max_depth,
            token,
            console,
        )
        # display the search results
        _display_find_results(
            filtered_repositories, console, organization, files
        )
        # save results to a JSON file if saving of data was requested
        if save_file:
            success = _save_results_to_json(
                filtered_repositories,
                save_file,
                configuration_data,
                f"organization:{organization}",
                files,
            )
            # saving the file worked correctly and thus this
            # function only needs to display a diagnostic message
            if success:
                console.print(
                    f":information: Find results saved to {save_file}"
                )
            # saving the file did not work and thus this function
            # must return a failure status code so that a calling
            # function can ensure that this is communicated back
            else:
                console.print(
                    f"{Symbols.ERROR.value} Failed to save results to {save_file}"
                )
                return StatusCode.FAILURE
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
    files: Optional[List[str]],
    max_depth: Optional[int],
    token: str,
    console: Console,
) -> list:
    """Filter repositories based on the provided criteria."""
    # initialize the list to hold filtered repositories
    filtered_repos = []
    # convert the repositories paginated list to a list for counting
    # and filtering through the repositories
    try:
        # display a spinner using rich because the process of
        # accessing the repositories can take some time; this is
        # due to the fact that the repositories are paginated
        # and the API needs to fetch all of them and there is
        # the interaction with the GitHub API may have rate limits
        with console.status("Finding Repositories", spinner="dots"):
            repos_list = list(repositories)
            total_repos = len(repos_list)
        console.print()
        console.print(
            f":information: Processing {total_repos} accessible repositories"
        )
        if files:
            console.print(
                f":information: Performing filtering for at most {min(total_repos, MAX_FILTER)} repositories"
            )
        console.print()
    except Exception:
        console.print(f"{Symbols.ERROR.value} Failed to access repositories")
        return []
    # filter the repositories and display output in the
    # context of a progress bar from rich
    max_filter_runs = min(total_repos, MAX_FILTER) if files else total_repos
    with Progress(
        "[progress.description]{task.description}",
        BarColumn(),
        "[progress.percentage]{task.percentage:>3.0f}%",
        TextColumn("[progress.completed]{task.completed}/{task.total}"),
    ) as progress:
        task = progress.add_task(
            "[green]Filtering Repositories", total=max_filter_runs
        )
        repo_count = 0
        # iteratively filter through each of the repositories, only
        # keeping a repository as a match if it meets all criteria
        for repository in repos_list:
            # if files are specified, check the limit for filtering
            if files and repo_count >= MAX_FILTER:
                break
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
                # if files are specified, check if repository contains them
                if files:
                    headers = {
                        "Authorization": f"token {token}",
                        "Accept": "application/vnd.github.v3+json",
                    }
                    if _repository_contains_files(
                        repository, files, max_depth, headers
                    ):
                        filtered_repos.append(repository)
                        progress.console.print(
                            f"{Symbols.CHECK.value} Found all designated files in {repository.name}"
                        )
                # no file filtering needed, repository matches other criteria
                else:
                    filtered_repos.append(repository)
                    progress.console.print(
                        f"{Symbols.CHECK.value} Found matching repository: {repository.name}"
                    )
            # update the progress bar
            if files:
                repo_count += 1
                progress.update(task, advance=1)
            else:
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


def _repository_contains_files(
    repository,
    required_files: List[str],
    max_depth: int,
    headers: dict,
) -> bool:
    """Check if repository contains all required files and directories within specified depth."""
    # convert the required files to a set to ensure
    # that there is no duplicate looking; this guarantees
    # that if there is a duplicate file in the required_files
    # then the return statement will work correctly
    required_files_set: Set[str] = set(required_files)
    try:
        # create a set to hold the found files
        found_files = set()
        # get all files in the repository up to the specified depth
        repo_files = _get_repository_files(repository, max_depth, headers)
        # iterate through the files and directories in the repository
        # that were found and check if the required files are present
        for file_info in repo_files:
            file_name = file_info.get("name", "")
            # found one of the required files and thus
            # it should be added to the set of those files found
            if file_name in required_files:
                found_files.add(file_name)
        # check if all required files were found in the repository;
        # this is done by confirming that the set of required files
        # has the same length as the set of (recursively) found files
        return len(found_files) == len(required_files_set)
    # there was some problem with the repository or the API call,
    # and thus the repository cannot be considered as containing
    # the required files, so therefore return False
    except Exception:
        return False


def _get_repository_files(
    repository, max_depth: int, headers: dict
) -> List[dict]:
    """Get all files and directories in a GitHub repository up to specified depth."""
    # initialize the list of files and directories that
    # are found from the recursive search of the repository
    all_files: List[dict] = []
    # recursively collect all files and directories
    try:
        _collect_files_recursive(
            repository.full_name, "", max_depth, 0, headers, all_files
        )
    except Exception:
        pass
    # return the list of all files and directories found
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
    # stop the recursion if the current depth exceeds the maximum depth;
    # the use of the maximum depth parameter is the means by which this
    # function controls the computational cost of the recursive search
    if current_depth > max_depth:
        return None
    # create the API URL for the GitHub repository so that this
    # function can query the contents of the repository
    api_url = f"https://api.github.com/repos/{repo_full_name}/contents/{path}"
    try:
        # access the GitHub API to get the contents of the repository
        # using the requests library; this is done to access the
        # files and/or directories in the repository at the specified path
        response = requests.get(api_url, headers=headers, timeout=10)
        # something did not work and thus the traversal has failed
        if response.status_code != StatusCode.WORKING.value:
            return
        contents = response.json()
        if not isinstance(contents, list):
            return
        # iterate through all of the files and/or directories that
        # were found at this specific level in the repository
        for item in contents:
            if item.get("type") == FileSystem.FILE.value:
                all_files.append(item)
            elif item.get("type") == FileSystem.DIRECTORY.value:
                all_files.append(item)
                # keep recursively traversing the files and
                # directories in this GitHub repository as long
                # as the maximum depth is not exceeded
                if current_depth < max_depth:
                    _collect_files_recursive(
                        repo_full_name,
                        item.get(
                            FileSystem.PATH.value, FileSystem.EMPTY.value
                        ),
                        max_depth,
                        current_depth + 1,
                        headers,
                        all_files,
                    )
    except Exception:
        return None


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
        with open(save_file, "w", encoding="utf-8") as file:
            json.dump(reporover_data.model_dump(), file, indent=2, default=str)
        return True
    except Exception:
        return False


def _display_find_results(
    repositories: list,
    console: Console,
    organization: str,
    required_files: Optional[List[str]] = None,
) -> None:
    """Display the find results in a formatted table."""
    if required_files:
        table = Table(
            title=f"Repository Find Results for Organization: {organization} (Filtered by Files and/or Directories)",
            box=box.SIMPLE_HEAVY,
        )
        table.add_column("Name", style="cyan", no_wrap=False)
        table.add_column("Description", style="magenta")
        table.add_column("Stars", justify="right", style="green")
        table.add_column("Forks", justify="right", style="yellow")
        table.add_column("Language", style="blue")
        table.add_column("Updated", style="white")
        table.add_column("Private", style="red")
        table.add_column("Files Found", style="bright_green")
    else:
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
        # add repositories to the table
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
            private_status = "Yes" if repository.private else "No"
            if required_files:
                files_display = ", ".join(required_files)
                table.add_row(
                    repository.name,
                    description,
                    str(repository.stargazers_count),
                    str(repository.forks_count),
                    language_display,
                    updated_date,
                    private_status,
                    files_display,
                )
            else:
                table.add_row(
                    repository.name,
                    description,
                    str(repository.stargazers_count),
                    str(repository.forks_count),
                    language_display,
                    updated_date,
                    private_status,
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
