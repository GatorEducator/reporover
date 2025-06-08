"""Search GitHub repositories for files matching specified patterns."""

from typing import List

import requests
from rich.progress import Progress

from reporover.constants import (
    StatusCode,
)


def get_all_repositories(organization_name: str, headers: dict, progress: Progress) -> List[dict]:
    """Get all repositories from an organization using pagination."""
    all_repositories = []
    page = 1
    while True:
        repos_url = f"https://api.github.com/orgs/{organization_name}/repos?per_page=100&page={page}"
        progress.console.print(f"Debug: Making request to: {repos_url}")
        repos_response = requests.get(repos_url, headers=headers)
        progress.console.print(f"Debug: Response status code: {repos_response.status_code}")
        if repos_response.status_code != StatusCode.WORKING.value:
            progress.console.print(f"Failed to fetch repositories page {page}")
            progress.console.print(f"Diagnostic: {repos_response.status_code}")
            break
        repositories = repos_response.json()
        if not repositories:
            break
        all_repositories.extend(repositories)
        progress.console.print(f"Debug: Found {len(repositories)} repos on page {page}, total so far: {len(all_repositories)}")
        page += 1
    return all_repositories


def get_all_files_recursive(organization_name: str, repo_name: str, headers: dict, progress: Progress, path: str = "") -> List[str]:
    """Recursively get all file names from a repository."""
    all_files = []
    contents_url = f"https://api.github.com/repos/{organization_name}/{repo_name}/contents"
    if path:
        contents_url += f"/{path}"
    progress.console.print(f"Debug: Getting contents from: {contents_url}")
    contents_response = requests.get(contents_url, headers=headers)
    if contents_response.status_code != StatusCode.WORKING.value:
        progress.console.print(f"Debug: Failed to get contents for path '{path}' in {repo_name}")
        return all_files
    contents = contents_response.json()
    for item in contents:
        if item["type"] == "file":
            file_path = f"{path}/{item['name']}" if path else item["name"]
            all_files.append(file_path)
            progress.console.print(f"Debug: Found file: {file_path}")
        elif item["type"] == "dir":
            dir_path = f"{path}/{item['name']}" if path else item["name"]
            progress.console.print(f"Debug: Exploring directory: {dir_path}")
            # recursively get files from subdirectory
            subdir_files = get_all_files_recursive(organization_name, repo_name, headers, progress, dir_path)
            all_files.extend(subdir_files)
    return all_files


def check_patterns_match(file_names: List[str], file_patterns: List[str], match_all: bool, progress: Progress) -> List[str]:
    """Check if file patterns match the given file names."""
    matched_files = []
    if match_all:
        # all patterns must match
        all_patterns_found = True
        for pattern in file_patterns:
            pattern_matches = [
                name for name in file_names
                if pattern.lower() in name.lower() or name == pattern
            ]
            if pattern_matches:
                matched_files.extend(pattern_matches)
                progress.console.print(f"Debug: Pattern '{pattern}' matched: {pattern_matches}")
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
                name for name in file_names
                if pattern.lower() in name.lower() or name == pattern
            ]
            matched_files.extend(pattern_matches)
            if pattern_matches:
                progress.console.print(f"Debug: Pattern '{pattern}' matched: {pattern_matches}")
    return list(set(matched_files))


def search_repositories_for_files(  # noqa: PLR0913
    github_organization_url: str,
    repo_name_fragment: str,
    token: str,
    file_patterns: List[str],
    progress: Progress,
    match_all: bool = False,
) -> StatusCode:
    """Search GitHub repositories for files matching specified patterns."""
    # extract the organization name from the GitHub organization URL
    organization_name = github_organization_url.rstrip("/").split("/")[-1]
    progress.console.print(f"Debug: Organization name extracted: {organization_name}")
    # set up headers for GitHub API requests
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
    }
    try:
        # get all repositories from the organization using pagination
        repositories = get_all_repositories(organization_name, headers, progress)
        progress.console.print(f"Debug: Total repositories found: {len(repositories)}")
        # print first few repository names for debugging
        if repositories:
            progress.console.print("Debug: First few repository names:")
            for i, repo in enumerate(repositories[:5]):
                progress.console.print(f"  {i+1}. {repo['name']}")
        # filter repositories by name fragment
        matching_repos = [
            repo
            for repo in repositories
            if repo_name_fragment.lower() in repo["name"].lower()
        ]
        progress.console.print(f"Debug: Repositories matching '{repo_name_fragment}': {len(matching_repos)}")
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
            progress.console.print(f"Searching repository: {repo_name}")
            # get all files recursively from the repository
            all_files = get_all_files_recursive(organization_name, repo_name, headers, progress)
            progress.console.print(f"Debug: Total files found in {repo_name}: {len(all_files)}")
            # check if file patterns match
            matched_files = check_patterns_match(all_files, file_patterns, match_all, progress)
            if matched_files:
                found_repositories.append(
                    {
                        "name": repo_name,
                        "url": repo["html_url"],
                        "matched_files": matched_files,
                    }
                )
                progress.console.print(
                    f"  ✓ Found patterns in {repo_name}: {matched_files}"
                )
        # display summary results
        if found_repositories:
            progress.console.print(
                f"\nFound {len(found_repositories)} repositories with matching files:"
            )
            for repo_info in found_repositories:
                progress.console.print(
                    f"  {repo_info['name']}: {', '.join(repo_info['matched_files'])}"
                )
                progress.console.print(f"    URL: {repo_info['url']}")
        else:
            progress.console.print(
                "No repositories found with the specified file patterns"
            )
        return StatusCode.SUCCESS
    except requests.exceptions.RequestException as request_error:
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
