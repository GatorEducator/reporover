"""Test suite for the find module."""

from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest
from rich.console import Console

from reporover.constants import StatusCode
from reporover.find import (
    _repository_matches_criteria,
    find_repositories,
)


class MockRepository:
    """Mock repository object for testing."""

    def __init__(  # noqa: PLR0913
        self,
        name="test-repo",
        language="Python",
        stargazers_count=100,
        forks_count=50,
        created_at=datetime(2023, 1, 1),
        updated_at=datetime(2023, 1, 1),
        private=True,
        html_url="https://github.com/user/test-repo",
        description="A test repository.",
    ):
        """Initialize the mock repository."""
        self.name = name
        self.language = language
        self.stargazers_count = stargazers_count
        self.forks_count = forks_count
        self.created_at = created_at
        self.updated_at = updated_at
        self.private = private
        self.html_url = html_url
        self.description = description


def test_repository_matches_criteria_no_filters():
    """Test that a repository matches with no filters."""
    repo = MockRepository()
    assert _repository_matches_criteria(
        repo, None, None, None, None, None, None
    )


def test_repository_matches_criteria_name_match():
    """Test that a repository matches with a name filter."""
    repo = MockRepository(name="my-awesome-repo")
    assert _repository_matches_criteria(
        repo, "awesome", None, None, None, None, None
    )


def test_repository_matches_criteria_name_no_match():
    """Test that a repository does not match with a name filter."""
    repo = MockRepository(name="my-repo")
    assert not _repository_matches_criteria(
        repo, "awesome", None, None, None, None, None
    )


def test_repository_matches_criteria_language_match():
    """Test that a repository matches with a language filter."""
    repo = MockRepository(language="Python")
    assert _repository_matches_criteria(
        repo, None, "Python", None, None, None, None
    )


def test_repository_matches_criteria_language_no_match():
    """Test that a repository does not match with a language filter."""
    repo = MockRepository(language="JavaScript")
    assert not _repository_matches_criteria(
        repo, None, "Python", None, None, None, None
    )


def test_repository_matches_criteria_stars_match():
    """Test that a repository matches with a stars filter."""
    repo = MockRepository(stargazers_count=150)
    assert _repository_matches_criteria(
        repo, None, None, 100, None, None, None
    )


def test_repository_matches_criteria_stars_no_match():
    """Test that a repository does not match with a stars filter."""
    repo = MockRepository(stargazers_count=50)
    assert not _repository_matches_criteria(
        repo, None, None, 100, None, None, None
    )


def test_repository_matches_criteria_forks_match():
    """Test that a repository matches with a forks filter."""
    repo = MockRepository(forks_count=75)
    assert _repository_matches_criteria(repo, None, None, None, 50, None, None)


def test_repository_matches_criteria_forks_no_match():
    """Test that a repository does not match with a forks filter."""
    repo = MockRepository(forks_count=25)
    assert not _repository_matches_criteria(
        repo, None, None, None, 50, None, None
    )


def test_repository_matches_criteria_created_after_match():
    """Test that a repository matches with a created_after filter."""
    repo = MockRepository(created_at=datetime(2023, 6, 1))
    assert _repository_matches_criteria(
        repo, None, None, None, None, "2023-01-01", None
    )


def test_repository_matches_criteria_created_after_no_match():
    """Test that a repository does not match with a created_after filter."""
    repo = MockRepository(created_at=datetime(2022, 1, 1))
    assert not _repository_matches_criteria(
        repo, None, None, None, None, "2023-01-01", None
    )


def test_repository_matches_criteria_updated_after_match():
    """Test that a repository matches with an updated_after filter."""
    repo = MockRepository(updated_at=datetime(2023, 6, 1))
    assert _repository_matches_criteria(
        repo, None, None, None, None, None, "2023-01-01"
    )


def test_repository_matches_criteria_updated_after_no_match():
    """Test that a repository does not match with an updated_after filter."""
    repo = MockRepository(updated_at=datetime(2022, 1, 1))
    assert not _repository_matches_criteria(
        repo, None, None, None, None, None, "2023-01-01"
    )


def test_repository_matches_criteria_all_match():
    """Test that a repository matches with all filters."""
    repo = MockRepository(
        name="my-awesome-python-repo",
        language="Python",
        stargazers_count=200,
        forks_count=100,
        created_at=datetime(2024, 1, 1),
        updated_at=datetime(2024, 1, 1),
    )
    assert _repository_matches_criteria(
        repo, "awesome", "Python", 150, 75, "2023-01-01", "2023-01-01"
    )


@patch("github.Github")
def test_find_repositories_success(mock_github):
    """Test that find_repositories returns success."""
    # Arrange
    mock_org = MagicMock()
    mock_org.get_repos.return_value = [MockRepository()]
    mock_github.return_value.get_organization.return_value = mock_org
    console = Console()

    # Act
    status = find_repositories(
        console=console,
        token="fake_token",
        organization="test_org",
        name=None,
        language=None,
        stars=None,
        forks=None,
        created_after=None,
        updated_after=None,
        files=None,
    )

    # Assert
    assert status == StatusCode.SUCCESS


@patch("github.Github")
def test_find_repositories_org_not_found(mock_github):
    """Test that find_repositories handles organization not found."""
    # Arrange
    mock_github.return_value.get_organization.side_effect = (
        pytest.importorskip("github").UnknownObjectException(
            404, "Not Found", {}
        )
    )
    console = Console()

    # Act
    status = find_repositories(
        console=console,
        token="fake_token",
        organization="non_existent_org",
        name=None,
        language=None,
        stars=None,
        forks=None,
        created_after=None,
        updated_after=None,
        files=None,
    )

    # Assert
    assert status == StatusCode.FAILURE
