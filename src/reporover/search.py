"""Search GitHub repositories for files matching specified patterns."""

import fnmatch
from typing import Any, Dict, List, Optional

import requests
from rich.progress import Progress

from reporover.constants import (
    StatusCode,
    Symbols,
)


def matches_repo_pattern(repo_name: str, repo_name_fragment: str) -> bool:
    """Check if repository name matches the fragment pattern (supports wildcards)."""
    if not repo_name_fragment or repo_name_fragment == "*":
        return True
    # support wildcard matching
    if "*" in repo_name_fragment or "?" in repo_name_fragment:
        return fnmatch.fnmatch(repo_name.lower(), repo_name_fragment.lower())
    # fallback to substring matching
    return repo_name_fragment.lower() in repo_name.lower()


def create_repository_url(
    organization_name: Optional[str], language: Optional[str], page: int
) -> str:
    """Create the full URL for a GitHub repository."""
    # search within specific organization
    if organization_name:
        repos_url = f"https://api.github.com/orgs/{organization_name}/repos?per_page=100&page={page}"
    # search all public repositories on GitHub because
    # of the fact that the organization name is not provided
    else:
        search_query = "is:public"
        if language:
            search_query += f" language:{language}"
        repos_url = f"https://api.github.com/search/repositories?q={search_query}&per_page=100&page={page}"
    # return the URL for a specific page of results
    # to be requested from the GitHub API with pagination
    return repos_url


def get_all_repositories(
    organization_name: Optional[str],
    headers: dict,
    progress: Progress,
    max_repos: int,
    language: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Get all repositories from an organization or search globally using pagination."""
    task = progress.add_task("[green]Searching Repositories", total=None)
    # initialize the list to hold all repositories
    all_repositories = []
    # start with the first page of results in the
    # pagination system used by the GitHub API
    page = 1
    # repeatedly query the GitHub API for repositories
    # until one of the stop conditions is met
    while True:
        # define the URL for the GitHub API request
        repos_url = create_repository_url(organization_name, language, page)
        # run the query against the GitHub API
        # and obtain the response
        repos_response = requests.get(repos_url, headers=headers)
        # it was not possible to obtain the list of repositories
        # and thus the overall iterative search is now completed
        if repos_response.status_code != StatusCode.WORKING.value:
            progress.console.print(
                f"{Symbols.ERROR.value} Failed to fetch page {page} of repositories"
            )
            progress.console.print(f"Diagnostic: {repos_response.status_code}")
            progress.stop_task(task)
            break
        # extract and parse the JSON response data
        response_data = repos_response.json()
        # there was an organization specified
        # for the search and thus the list of
        # repositories is the response data itself
        if organization_name:
            repositories = response_data
        # for the GitHub search API, the chosen repositories are
        # in 'items' field, which is what we want for the next step
        else:
            repositories = response_data.get("items", [])
        # there were no repositories from this round of the search
        # and this means that the search is complete
        if not repositories:
            progress.console.print(
                f"{Symbols.CHECK.value} Did not find further repositories on page {page}"
            )
            progress.stop_task(task)
            break
        # add all of the repositories from this page to the list
        # of all repositories found so far
        all_repositories.extend(repositories)
        progress.console.print(
            f"{Symbols.CHECK.value} Found {len(repositories):3} repos on page {page}, total so far: {len(all_repositories)}"
        )
        # check if we've reached the maximum number of repositories
        if max_repos and len(all_repositories) >= max_repos:
            all_repositories = all_repositories[:max_repos]
            progress.console.print(
                f"{Symbols.CHECK.value} Reached maximum repository limit of {max_repos}"
            )
            break
        # go to the next page in the paginated list of GitHub repositories
        page += 1
        # indicate that we've completed a round of pagination, which
        # is going to handle 100 items at a time
        progress.advance(task, 100)
    return all_repositories


def get_all_files_recursive(  # noqa: PLR0913
    organization_name: str,
    repo_name: str,
    headers: dict,
    progress: Progress,
    path: str = "",
    current_depth: int = 0,
    max_depth: int = 2,
) -> List[str]:
    """Recursively get all file names from a repository up to a specified depth."""
    all_files: List[str] = []
    contents_url = f"https://api.github.com/repos/{organization_name}/{repo_name}/contents"
    if path:
        contents_url += f"/{path}"
    progress.console.print(
        f"Debug: Getting contents from: {contents_url} (depth: {current_depth})"
    )
    contents_response = requests.get(contents_url, headers=headers)
    if contents_response.status_code != StatusCode.WORKING.value:
        progress.console.print(
            f"Debug: Failed to get contents for path '{path}' in {repo_name}"
        )
        return all_files
    contents = contents_response.json()
    for item in contents:
        if item["type"] == "file":
            file_path = f"{path}/{item['name']}" if path else item["name"]
            all_files.append(file_path)
            progress.console.print(f"Debug: Found file: {file_path}")
        elif item["type"] == "dir" and current_depth < max_depth:
            dir_path = f"{path}/{item['name']}" if path else item["name"]
            progress.console.print(
                f"Debug: Exploring directory: {dir_path} (depth: {current_depth + 1})"
            )
            # recursively get files from sub-directory
            subdir_files = get_all_files_recursive(
                organization_name,
                repo_name,
                headers,
                progress,
                dir_path,
                current_depth + 1,
                max_depth,
            )
            all_files.extend(subdir_files)
        elif item["type"] == "dir":
            dir_path = f"{path}/{item['name']}" if path else item["name"]
            progress.console.print(
                f"Debug: Skipping directory: {dir_path} (max depth {max_depth} reached)"
            )
    return all_files


def check_patterns_match(
    file_names: List[str],
    file_patterns: List[str],
    match_all: bool,
    progress: Progress,
) -> List[str]:
    """Check if file patterns match the given file names."""
    matched_files = []
    if match_all:
        # all patterns must match
        all_patterns_found = True
        for pattern in file_patterns:
            pattern_matches = [
                name
                for name in file_names
                if pattern.lower() in name.lower()
                or name == pattern
                or fnmatch.fnmatch(name.lower(), pattern.lower())
            ]
            if pattern_matches:
                matched_files.extend(pattern_matches)
                progress.console.print(
                    f"Debug: Pattern '{pattern}' matched: {pattern_matches}"
                )
            else:
                # if any pattern doesn't match, return empty list
                progress.console.print(f"Debug: Pattern '{pattern}' not found")
                all_patterns_found = False
                break
        if not all_patterns_found:
            return []
    else:
        # any pattern can match
        for pattern in file_patterns:
            pattern_matches = [
                name
                for name in file_names
                if pattern.lower() in name.lower()
                or name == pattern
                or fnmatch.fnmatch(name.lower(), pattern.lower())
            ]
            matched_files.extend(pattern_matches)
            if pattern_matches:
                progress.console.print(
                    f"Debug: Pattern '{pattern}' matched: {pattern_matches}"
                )
    return list(set(matched_files))


def search_repositories_for_files(  # noqa: PLR0913
    github_organization_url: str,
    repo_name_fragment: str,
    token: str,
    file_patterns: List[str],
    progress: Progress,
    max_repos_to_search: int,
    max_matching_repos: int,
    max_directory_depth: int,
    match_all: bool = False,
    language: Optional[str] = None,
) -> StatusCode:
    """Search GitHub repositories for files matching specified patterns."""
    # extract the organization name from the GitHub organization URL
    # if url is the empty string, then search globally
    organization_name = None
    if (
        github_organization_url
        and github_organization_url.strip()
        and github_organization_url != ""
    ):
        organization_name = github_organization_url.rstrip("/").split("/")[-1]
    # set up headers for GitHub API requests
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
    }
    # attempt to complete the multiple-stage search process by running
    # both queries against the GitHub API and then searches in the results
    try:
        # --> STEP 1: get all repositories from the organization using pagination
        repositories = get_all_repositories(
            organization_name, headers, progress, max_repos_to_search, language
        )
        progress.console.print(
            f"Debug: Total repositories found: {len(repositories)}"
        )
        # filter repositories by name fragment (supports wildcards)
        matching_repos = [
            repo
            for repo in repositories
            if matches_repo_pattern(repo["name"], repo_name_fragment)
        ]
        progress.console.print(
            f"Debug: Repositories matching '{repo_name_fragment}': {len(matching_repos)}"
        )
        if not matching_repos:
            progress.console.print(
                f"No repositories found matching fragment '{repo_name_fragment}'"
            )
            return StatusCode.SUCCESS
        progress.console.print(
            f"Found {len(matching_repos)} repositories matching '{repo_name_fragment}'"
        )
        # search each repository for the specified file patterns
        found_repositories = []
        for repo in matching_repos:
            repo_name = repo["name"]
            # extract owner name for API calls
            repo_owner = (
                repo["owner"]["login"]
                if organization_name is None
                else organization_name
            )
            progress.console.print(
                f"Searching repository: {repo_owner}/{repo_name}"
            )
            # get all files recursively from the repository
            all_files = get_all_files_recursive(
                repo_owner,
                repo_name,
                headers,
                progress,
                "",
                0,
                max_directory_depth,
            )
            progress.console.print(
                f"Debug: Total files found in {repo_name}: {len(all_files)}"
            )
            # check if file patterns match
            matched_files = check_patterns_match(
                all_files, file_patterns, match_all, progress
            )
            if matched_files:
                found_repositories.append(
                    {
                        "name": repo_name,
                        "owner": repo_owner,
                        "url": repo["html_url"],
                        "matched_files": matched_files,
                    }
                )
                progress.console.print(
                    f"  ✓ Found patterns in {repo_owner}/{repo_name}: {matched_files}"
                )
                # check if we've reached the maximum number of matching repositories
                if (
                    max_matching_repos
                    and len(found_repositories) >= max_matching_repos
                ):
                    progress.console.print(
                        f"Debug: Reached maximum matching repository limit of {max_matching_repos}"
                    )
                    break
        # display summary results
        if found_repositories:
            progress.console.print(
                f"\nFound {len(found_repositories)} repositories with matching files:"
            )
            for repo_info in found_repositories:
                progress.console.print(
                    f"  {repo_info['owner']}/{repo_info['name']}: {', '.join(repo_info['matched_files'])}"
                )
                progress.console.print(f"    URL: {repo_info['url']}")
        else:
            progress.console.print(
                "No repositories found with the specified file patterns"
            )
        return StatusCode.SUCCESS
    except requests.exceptions.RequestException as request_error:  # type: ignore[attr-defined]
        progress.console.print(
            "Failed to search repositories: Network error occurred"
        )
        progress.console.print(f"Diagnostic: {request_error}")
        return StatusCode.FAILURE
    except Exception as general_error:
        progress.console.print(
            "Failed to search repositories: Unexpected error occurred"
        )
        progress.console.print(f"Diagnostic: {general_error}")
        return StatusCode.FAILURE
