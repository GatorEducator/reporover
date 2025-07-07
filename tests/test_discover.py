"""Test cases for discover module."""

# ruff: noqa: PLR2004

import json
import os
import tempfile
from unittest.mock import Mock, patch

import pytest
from github import GithubException
from hypothesis import given
from hypothesis import strategies as st
from rich.console import Console

import reporover.discover
from reporover.constants import Numbers, StatusCode
from reporover.discover import (
    _build_search_query,
    _display_search_results,
    _repository_contains_files,
    _save_results_to_json,
    discover_repositories,
    extract_configuration_from_data,
    extract_repos_from_data,
    load_results_from_json,
)
from reporover.models import DiscoverConfiguration, RepositoryInfo


class TestBuildSearchQuery:
    """Test cases for the _build_search_query function."""

    def test_build_search_query_with_all_criteria(self):
        """Test _build_search_query with all search criteria provided."""
        result = _build_search_query(
            language="python",
            stars=100,
            forks=50,
            created_after="2023-01-01",
            updated_after="2023-06-01",
            topics=None,
        )
        expected = "language:python stars:>=100 forks:>=50 created:>=2023-01-01 pushed:>=2023-06-01"
        assert result == expected

    def test_build_search_query_with_language_only(self):
        """Test _build_search_query with only language criteria provided."""
        result = _build_search_query(
            language="javascript",
            stars=None,
            forks=None,
            created_after=None,
            updated_after=None,
            topics=None,
        )
        expected = "language:javascript"
        assert result == expected

    def test_build_search_query_with_stars_only(self):
        """Test _build_search_query with only stars criteria provided."""
        result = _build_search_query(
            language=None,
            stars=200,
            forks=None,
            created_after=None,
            updated_after=None,
            topics=[],
        )
        expected = "stars:>=200"
        assert result == expected

    def test_build_search_query_with_forks_only(self):
        """Test _build_search_query with only forks criteria provided."""
        result = _build_search_query(
            language=None,
            stars=None,
            forks=75,
            created_after=None,
            updated_after=None,
            topics=None,
        )
        expected = "forks:>=75"
        assert result == expected

    def test_build_search_query_with_created_after_only(self):
        """Test _build_search_query with only created_after criteria provided."""
        result = _build_search_query(
            language=None,
            stars=None,
            forks=None,
            created_after="2022-12-01",
            updated_after=None,
            topics=None,
        )
        expected = "created:>=2022-12-01"
        assert result == expected

    def test_build_search_query_with_updated_after_only(self):
        """Test _build_search_query with only updated_after criteria provided."""
        result = _build_search_query(
            language=None,
            stars=None,
            forks=None,
            created_after=None,
            updated_after="2023-03-15",
            topics=None,
        )
        expected = "pushed:>=2023-03-15"
        assert result == expected

    def test_build_search_query_with_zero_stars(self):
        """Test _build_search_query with zero stars value."""
        result = _build_search_query(
            language=None,
            stars=0,
            forks=None,
            created_after=None,
            updated_after=None,
            topics=None,
        )
        expected = "stars:>=0"
        assert result == expected

    def test_build_search_query_with_zero_forks(self):
        """Test _build_search_query with zero forks value."""
        result = _build_search_query(
            language=None,
            stars=None,
            forks=0,
            created_after=None,
            updated_after=None,
            topics=[],
        )
        expected = "forks:>=0"
        assert result == expected

    def test_build_search_query_with_no_criteria(self):
        """Test _build_search_query with no criteria provided."""
        result = _build_search_query(
            language=None,
            stars=None,
            forks=None,
            created_after=None,
            updated_after=None,
            topics=None,
        )
        expected = "is:public"
        assert result == expected

    def test_build_search_query_with_empty_string_language(self):
        """Test _build_search_query with empty string language."""
        result = _build_search_query(
            language="",
            stars=None,
            forks=None,
            created_after=None,
            updated_after=None,
            topics=None,
        )
        expected = "is:public"
        assert result == expected

    def test_build_search_query_with_empty_string_dates(self):
        """Test _build_search_query with empty string dates."""
        result = _build_search_query(
            language=None,
            stars=None,
            forks=None,
            created_after="",
            updated_after="",
            topics=None,
        )
        expected = "is:public"
        assert result == expected

    def test_build_search_query_with_partial_criteria(self):
        """Test _build_search_query with partial criteria provided."""
        result = _build_search_query(
            language="go",
            stars=None,
            forks=25,
            created_after=None,
            updated_after="2023-01-01",
            topics=[],
        )
        expected = "language:go forks:>=25 pushed:>=2023-01-01"
        assert result == expected


class TestDisplaySearchResults:
    """Test cases for the _display_search_results function."""

    @pytest.fixture
    def console(self):
        """Create a console fixture for testing."""
        return Console()

    @pytest.fixture
    def mock_repository(self):
        """Create a mock repository for testing."""
        repo = Mock()
        repo.name = "test-repo"
        repo.description = "A test repository"
        repo.stargazers_count = 150
        repo.forks_count = 25
        repo.language = "Python"
        repo.updated_at.strftime.return_value = "2023-06-15"
        return repo

    @pytest.fixture
    def mock_repository_no_description(self):
        """Create a mock repository with no description."""
        repo = Mock()
        repo.name = "no-desc-repo"
        repo.description = None
        repo.stargazers_count = 75
        repo.forks_count = 10
        repo.language = "JavaScript"
        repo.updated_at.strftime.return_value = "2023-05-20"
        return repo

    @pytest.fixture
    def mock_repository_no_language(self):
        """Create a mock repository with no language."""
        repo = Mock()
        repo.name = "no-lang-repo"
        repo.description = "Repository without language"
        repo.stargazers_count = 50
        repo.forks_count = 5
        repo.language = None
        repo.updated_at.strftime.return_value = "2023-04-10"
        return repo

    @pytest.fixture
    def mock_repository_long_description(self):
        """Create a mock repository with long description."""
        repo = Mock()
        repo.name = "long-desc-repo"
        repo.description = "This is a very long description that exceeds the maximum length limit and should be truncated"
        repo.stargazers_count = 300
        repo.forks_count = 100
        repo.language = "Java"
        repo.updated_at.strftime.return_value = "2023-07-01"
        return repo

    def test_display_search_results_single_repository(
        self, console, mock_repository
    ):
        """Test _display_search_results with a single repository."""
        repositories = Mock()
        repositories.__iter__ = Mock(return_value=iter([mock_repository]))
        repositories.totalCount = 1
        with (
            patch.object(console, "print") as mock_print,
            patch("reporover.discover.Progress"),
        ):
            _display_search_results(repositories, console)
            assert mock_print.call_count >= 2

    def test_display_search_results_no_description(
        self, console, mock_repository_no_description
    ):
        """Test _display_search_results with repository having no description."""
        repositories = Mock()
        repositories.__iter__ = Mock(
            return_value=iter([mock_repository_no_description])
        )
        repositories.totalCount = 1
        with (
            patch.object(console, "print") as mock_print,
            patch("reporover.discover.Progress"),
        ):
            _display_search_results(repositories, console)
            assert mock_print.call_count >= 2

    def test_display_search_results_no_language(
        self, console, mock_repository_no_language
    ):
        """Test _display_search_results with repository having no language."""
        repositories = Mock()
        repositories.__iter__ = Mock(
            return_value=iter([mock_repository_no_language])
        )
        repositories.totalCount = 1
        with (
            patch.object(console, "print") as mock_print,
            patch("reporover.discover.Progress"),
        ):
            _display_search_results(repositories, console)
            assert mock_print.call_count >= 2

    def test_display_search_results_long_description(
        self, console, mock_repository_long_description
    ):
        """Test _display_search_results with repository having long description."""
        repositories = Mock()
        repositories.__iter__ = Mock(
            return_value=iter([mock_repository_long_description])
        )
        repositories.totalCount = 1
        with (
            patch.object(console, "print") as mock_print,
            patch("reporover.discover.Progress"),
        ):
            _display_search_results(repositories, console)
            assert mock_print.call_count >= 2

    def test_display_search_results_multiple_repositories(
        self, console, mock_repository, mock_repository_no_description
    ):
        """Test _display_search_results with multiple repositories."""
        repositories = Mock()
        repositories.__iter__ = Mock(
            return_value=iter(
                [mock_repository, mock_repository_no_description]
            )
        )
        repositories.totalCount = 2
        with (
            patch.object(console, "print") as mock_print,
            patch("reporover.discover.Progress"),
        ):
            _display_search_results(repositories, console)
            assert mock_print.call_count >= 2

    def test_display_search_results_max_display_limit(self, console):
        """Test _display_search_results respects MAX_DISPLAY limit."""
        mock_repos = []
        for i in range(15):
            repo = Mock()
            repo.name = f"repo-{i}"
            repo.description = f"Description {i}"
            repo.stargazers_count = i * 10
            repo.forks_count = i * 2
            repo.language = "Python"
            repo.updated_at.strftime.return_value = "2023-06-01"
            mock_repos.append(repo)
        repositories = Mock()
        repositories.__iter__ = Mock(return_value=iter(mock_repos))
        repositories.totalCount = 15
        with (
            patch.object(console, "print") as mock_print,
            patch("reporover.discover.Progress"),
        ):
            _display_search_results(repositories, console)
            assert mock_print.call_count >= 2

    def test_display_search_results_empty_repositories(self, console):
        """Test _display_search_results with empty repository list."""
        repositories = Mock()
        repositories.__iter__ = Mock(return_value=iter([]))
        repositories.totalCount = 0
        with (
            patch.object(console, "print") as mock_print,
            patch("reporover.discover.Progress"),
        ):
            _display_search_results(repositories, console)
            assert mock_print.call_count >= 2

    def test_display_search_results_total_count_exceeds_max(
        self, console, mock_repository
    ):
        """Test _display_search_results when total count exceeds max display."""
        repositories = Mock()
        repositories.__iter__ = Mock(return_value=iter([mock_repository]))
        repositories.totalCount = 50
        with (
            patch.object(console, "print") as mock_print,
            patch("reporover.discover.Progress"),
        ):
            _display_search_results(repositories, console)
            assert mock_print.call_count >= 2

    def test_display_search_results_total_count_equals_max(self, console):
        """Test _display_search_results when total count equals max display."""
        mock_repos = []
        for i in range(Numbers.MAX_KEEP.value):
            repo = Mock()
            repo.name = f"repo-{i}"
            repo.description = f"Description {i}"
            repo.stargazers_count = i * 10
            repo.forks_count = i * 2
            repo.language = "Python"
            repo.updated_at.strftime.return_value = "2023-06-01"
            mock_repos.append(repo)
        repositories = Mock()
        repositories.__iter__ = Mock(return_value=iter(mock_repos))
        repositories.totalCount = Numbers.MAX_KEEP.value
        with (
            patch.object(console, "print") as mock_print,
            patch("reporover.discover.Progress"),
        ):
            _display_search_results(repositories, console)
            assert mock_print.call_count >= 2


class TestSearchRepositories:
    """Test cases for the search_repositories function."""

    @pytest.fixture
    def console(self):
        """Create a console fixture for testing."""
        return Console()

    @pytest.fixture
    def mock_repository(self):
        """Create a mock repository for testing."""
        repo = Mock()
        repo.name = "test-repo"
        repo.description = "A test repository"
        repo.stargazers_count = 150
        repo.forks_count = 25
        repo.language = "Python"
        repo.updated_at.strftime.return_value = "2023-06-15"
        return repo

    @patch("reporover.discover.github.Github")
    def test_search_repositories_success(
        self, mock_github_class, console, mock_repository
    ):
        """Test search_repositories with successful search."""
        mock_github_instance = Mock()
        mock_github_class.return_value = mock_github_instance
        mock_repositories = Mock()
        mock_repositories.__iter__ = Mock(return_value=iter([mock_repository]))
        mock_repositories.totalCount = 1
        mock_github_instance.search_repositories.return_value = (
            mock_repositories
        )
        with (
            patch.object(console, "print"),
            patch("reporover.discover.Progress"),
        ):
            result = discover_repositories(
                token="fake_token",
                language="python",
                stars=100,
                forks=50,
                created_after="2023-01-01",
                updated_after="2023-06-01",
                files=None,
                max_depth=0,
                max_filter=100,
                max_display=10,
                console=console,
                topics=[""],
            )
        assert result == StatusCode.SUCCESS
        mock_github_class.assert_called_once_with("fake_token")
        mock_github_instance.search_repositories.assert_called_once()

    @patch("reporover.discover.github.Github")
    def test_search_repositories_with_none_values(
        self, mock_github_class, console, mock_repository
    ):
        """Test search_repositories with None values for optional parameters."""
        mock_github_instance = Mock()
        mock_github_class.return_value = mock_github_instance
        mock_repositories = Mock()
        mock_repositories.__iter__ = Mock(return_value=iter([mock_repository]))
        mock_repositories.totalCount = 1
        mock_github_instance.search_repositories.return_value = (
            mock_repositories
        )
        with (
            patch.object(console, "print"),
            patch("reporover.discover.Progress"),
        ):
            result = discover_repositories(
                token="fake_token",
                language=None,
                stars=None,
                forks=None,
                created_after=None,
                updated_after=None,
                files=None,
                max_depth=0,
                max_filter=100,
                max_display=10,
                console=console,
                topics=[""],
            )
        assert result == StatusCode.SUCCESS

    @patch("reporover.discover.github.Github")
    def test_search_repositories_github_exception(
        self, mock_github_class, console
    ):
        """Test search_repositories with GitHub API exception."""
        mock_github_instance = Mock()
        mock_github_class.return_value = mock_github_instance
        mock_github_instance.search_repositories.side_effect = GithubException(
            status=404, data="Not found"
        )
        with patch.object(console, "print") as mock_print:
            result = discover_repositories(
                token="invalid_token",
                language="python",
                stars=100,
                forks=50,
                created_after="2023-01-01",
                updated_after="2023-06-01",
                files=None,
                max_depth=0,
                max_filter=100,
                max_display=10,
                console=console,
                topics=[""],
            )
        assert result == StatusCode.FAILURE
        mock_print.assert_called()

    @patch("reporover.discover.github.Github")
    def test_search_repositories_general_exception(
        self, mock_github_class, console
    ):
        """Test search_repositories with general exception."""
        mock_github_instance = Mock()
        mock_github_class.return_value = mock_github_instance
        mock_github_instance.search_repositories.side_effect = Exception(
            "Network error"
        )
        with patch.object(console, "print") as mock_print:
            result = discover_repositories(
                token="fake_token",
                language="python",
                stars=100,
                forks=50,
                created_after="2023-01-01",
                updated_after="2023-06-01",
                files=None,
                max_depth=0,
                max_filter=100,
                max_display=10,
                console=console,
                topics=[""],
            )
        assert result == StatusCode.FAILURE
        mock_print.assert_called()

    @patch("reporover.discover.github.Github")
    def test_search_repositories_empty_results(
        self, mock_github_class, console
    ):
        """Test search_repositories with empty search results."""
        mock_github_instance = Mock()
        mock_github_class.return_value = mock_github_instance
        mock_repositories = Mock()
        mock_repositories.__iter__ = Mock(return_value=iter([]))
        mock_repositories.totalCount = 0
        mock_github_instance.search_repositories.return_value = (
            mock_repositories
        )
        with (
            patch.object(console, "print"),
            patch("reporover.discover.Progress"),
        ):
            result = discover_repositories(
                token="fake_token",
                language="obscure_language",
                stars=10000,
                forks=5000,
                created_after="2023-01-01",
                updated_after="2023-06-01",
                files=None,
                max_depth=0,
                max_filter=100,
                max_display=10,
                console=console,
                topics=[""],
            )
        assert result == StatusCode.SUCCESS

    @patch("reporover.discover.github.Github")
    def test_search_repositories_with_zero_values(
        self, mock_github_class, console, mock_repository
    ):
        """Test search_repositories with zero values for stars and forks."""
        mock_github_instance = Mock()
        mock_github_class.return_value = mock_github_instance
        mock_repositories = Mock()
        mock_repositories.__iter__ = Mock(return_value=iter([mock_repository]))
        mock_repositories.totalCount = 1
        mock_github_instance.search_repositories.return_value = (
            mock_repositories
        )
        with (
            patch.object(console, "print"),
            patch("reporover.discover.Progress"),
        ):
            result = discover_repositories(
                token="fake_token",
                language="python",
                stars=0,
                forks=0,
                created_after="2023-01-01",
                updated_after="2023-06-01",
                files=None,
                max_depth=0,
                max_filter=100,
                max_display=10,
                console=console,
                topics=[""],
            )
        assert result == StatusCode.SUCCESS

    @patch("reporover.discover.github.Github")
    def test_search_repositories_max_retrieve_and_display_updated(
        self, mock_github_class, console, mock_repository
    ):
        """Test search_repositories updates global MAX_RETRIEVE and MAX_DISPLAY values."""
        mock_github_instance = Mock()
        mock_github_class.return_value = mock_github_instance
        mock_repositories = Mock()
        mock_repositories.__iter__ = Mock(return_value=iter([mock_repository]))
        mock_repositories.totalCount = 1
        mock_github_instance.search_repositories.return_value = (
            mock_repositories
        )
        with (
            patch.object(console, "print"),
            patch("reporover.discover.Progress"),
        ):
            result = discover_repositories(
                token="fake_token",
                language="python",
                stars=100,
                forks=50,
                created_after="2023-01-01",
                updated_after="2023-06-01",
                files=None,
                max_depth=0,
                max_filter=200,
                max_display=20,
                console=console,
                topics=[""],
            )
        assert result == StatusCode.SUCCESS
        assert reporover.discover.MAX_FILTER == 200
        assert reporover.discover.MAX_DISPLAY == 20

    @patch("reporover.discover.github.Github")
    @patch("reporover.discover.Progress")
    def test_search_repositories_query_building_called(
        self, mock_progress_class, mock_github_class, console, mock_repository
    ):
        """Test search_repositories calls query building with correct parameters."""
        mock_github_instance = Mock()
        mock_github_class.return_value = mock_github_instance
        mock_repositories = Mock()
        mock_repositories.__iter__ = Mock(return_value=iter([mock_repository]))
        mock_repositories.totalCount = 1
        mock_github_instance.search_repositories.return_value = (
            mock_repositories
        )
        # mock the Progress context manager
        mock_progress_instance = Mock()
        mock_progress_class.return_value.__enter__ = Mock(
            return_value=mock_progress_instance
        )
        mock_progress_class.return_value.__exit__ = Mock(return_value=None)
        mock_progress_instance.add_task.return_value = "task_id"
        mock_progress_instance.update = Mock()
        with patch(
            "reporover.discover._build_search_query"
        ) as mock_build_query:
            mock_build_query.return_value = "language:python stars:>=100"
            with patch.object(console, "print"):
                result = discover_repositories(
                    token="fake_token",
                    language="python",
                    stars=100,
                    forks=None,
                    created_after=None,
                    updated_after=None,
                    files=None,
                    max_depth=0,
                    max_filter=100,
                    max_display=10,
                    console=console,
                    topics=[""],
                )
        assert result == StatusCode.SUCCESS
        mock_build_query.assert_called_once_with(
            "python", 100, None, None, None, [""]
        )

    @patch("reporover.discover.github.Github")
    @patch("reporover.discover.Progress")
    def test_search_repositories_display_results_called(
        self, mock_progress_class, mock_github_class, console, mock_repository
    ):
        """Test search_repositories calls display results function."""
        mock_github_instance = Mock()
        mock_github_class.return_value = mock_github_instance
        mock_repositories = Mock()
        mock_repositories.__iter__ = Mock(return_value=iter([mock_repository]))
        mock_repositories.totalCount = 1
        mock_github_instance.search_repositories.return_value = (
            mock_repositories
        )
        # mock the Progress context manager
        mock_progress_instance = Mock()
        mock_progress_class.return_value.__enter__ = Mock(
            return_value=mock_progress_instance
        )
        mock_progress_class.return_value.__exit__ = Mock(return_value=None)
        mock_progress_instance.add_task.return_value = "task_id"
        mock_progress_instance.update = Mock()
        with patch(
            "reporover.discover._display_search_results"
        ) as mock_display:
            with patch.object(console, "print"):
                result = discover_repositories(
                    token="fake_token",
                    language="python",
                    stars=100,
                    forks=50,
                    created_after="2023-01-01",
                    updated_after="2023-06-01",
                    files=None,
                    max_depth=0,
                    max_filter=100,
                    max_display=10,
                    console=console,
                    topics=[""],
                )
        assert result == StatusCode.SUCCESS
        mock_display.assert_called_once_with(mock_repositories, console)


class TestLoadResultsFromJson:
    """Test cases for the load_results_from_json function."""

    @pytest.fixture
    def valid_json_data(self):
        """Create valid JSON data for testing."""
        return {
            "reporover": {
                "configuration": {
                    "language": "python",
                    "stars": 100,
                    "forks": 50,
                    "created_after": "2023-01-01",
                    "updated_after": "2023-06-01",
                    "files": ["README.md"],
                    "topics": ["web"],
                    "max_depth": 3,
                    "max_filter": 100,
                    "max_display": 10,
                    "search_query": "language:python stars:>=100",
                    "timestamp": "2023-07-01T12:00:00Z",
                },
                "repositories": [
                    {
                        "name": "test-repo",
                        "url": "https://github.com/user/test-repo",
                        "description": "A test repository",
                        "language": "Python",
                        "stars": 150,
                        "forks": 25,
                        "created_at": "2023-01-01T00:00:00Z",
                        "updated_at": "2023-06-15T00:00:00Z",
                        "files": ["README.md"],
                    }
                ],
            }
        }

    @pytest.fixture
    def temp_json_file(self, tmp_path, valid_json_data):
        """Create a temporary JSON file with valid data."""
        json_file = tmp_path / "test_data.json"
        with open(json_file, "w", encoding="utf-8") as file:
            json.dump(valid_json_data, file, indent=2)
        return str(json_file)

    @pytest.fixture
    def invalid_json_file(self, tmp_path):
        """Create a temporary file with invalid JSON."""
        json_file = tmp_path / "invalid.json"
        with open(json_file, "w", encoding="utf-8") as file:
            file.write("invalid json content {")
        return str(json_file)

    @pytest.fixture
    def empty_json_file(self, tmp_path):
        """Create a temporary empty JSON file."""
        json_file = tmp_path / "empty.json"
        with open(json_file, "w", encoding="utf-8") as file:
            json.dump({}, file)
        return str(json_file)

    def test_load_results_from_json_success(self, temp_json_file):
        """Test load_results_from_json with valid JSON file."""
        result = load_results_from_json(temp_json_file)
        assert result is not None
        assert hasattr(result, "reporover")
        assert "configuration" in result.reporover
        assert "repositories" in result.reporover

    def test_load_results_from_json_file_not_found(self):
        """Test load_results_from_json with non-existent file."""
        result = load_results_from_json("non_existent_file.json")
        assert result is None

    def test_load_results_from_json_invalid_json(self, invalid_json_file):
        """Test load_results_from_json with invalid JSON."""
        result = load_results_from_json(invalid_json_file)
        assert result is None

    def test_load_results_from_json_empty_file(self, empty_json_file):
        """Test load_results_from_json with empty JSON file."""
        result = load_results_from_json(empty_json_file)
        assert result is None

    def test_load_results_from_json_malformed_data(self, tmp_path):
        """Test load_results_from_json with malformed data structure."""
        malformed_data = {"invalid": "structure"}
        json_file = tmp_path / "malformed.json"
        with open(json_file, "w", encoding="utf-8") as file:
            json.dump(malformed_data, file)
        result = load_results_from_json(str(json_file))
        assert result is None

    def test_load_results_from_json_missing_required_fields(self, tmp_path):
        """Test load_results_from_json with missing required fields."""
        incomplete_data = {"configuration": {"language": "python"}}
        json_file = tmp_path / "incomplete.json"
        with open(json_file, "w", encoding="utf-8") as file:
            json.dump(incomplete_data, file)
        result = load_results_from_json(str(json_file))
        assert result is None

    def test_load_results_from_json_validates_data_structure(
        self, temp_json_file
    ):
        """Test load_results_from_json validates the loaded data structure."""
        result = load_results_from_json(temp_json_file)
        assert result is not None
        assert hasattr(result, "reporover")
        assert isinstance(result.reporover, dict)
        assert "configuration" in result.reporover
        assert "repositories" in result.reporover


class TestExtractConfigurationFromData:
    """Test cases for the extract_configuration_from_data function."""

    @pytest.fixture
    def mock_reporover_data_valid(self):
        """Create mock RepoRoverData with valid configuration."""
        mock_data = Mock()
        mock_data.reporover = {
            "configuration": {
                "language": "python",
                "stars": 100,
                "forks": 50,
                "created_after": "2023-01-01",
                "updated_after": "2023-06-01",
                "files": ["README.md"],
                "topics": ["web"],
                "max_depth": 3,
                "max_filter": 100,
                "max_display": 10,
                "search_query": "language:python stars:>=100",
                "timestamp": "2023-07-01T12:00:00Z",
            }
        }
        return mock_data

    @pytest.fixture
    def mock_reporover_data_no_config(self):
        """Create mock RepoRoverData with no configuration."""
        mock_data = Mock()
        mock_data.reporover = {}
        return mock_data

    @pytest.fixture
    def mock_reporover_data_none_config(self):
        """Create mock RepoRoverData with None configuration."""
        mock_data = Mock()
        mock_data.reporover = {"configuration": None}
        return mock_data

    @pytest.fixture
    def mock_reporover_data_invalid_config(self):
        """Create mock RepoRoverData with invalid configuration type."""
        mock_data = Mock()
        mock_data.reporover = {"configuration": "invalid_string"}
        return mock_data

    @pytest.fixture
    def mock_reporover_data_empty_config(self):
        """Create mock RepoRoverData with empty configuration."""
        mock_data = Mock()
        mock_data.reporover = {"configuration": {}}
        return mock_data

    def test_extract_configuration_from_data_success(
        self, mock_reporover_data_valid
    ):
        """Test extract_configuration_from_data with valid data."""
        result = extract_configuration_from_data(mock_reporover_data_valid)
        assert result is not None
        assert hasattr(result, "language")
        assert result.language == "python"
        assert result.stars == 100
        assert result.forks == 50

    def test_extract_configuration_from_data_no_configuration_key(
        self, mock_reporover_data_no_config
    ):
        """Test extract_configuration_from_data with no configuration key."""
        result = extract_configuration_from_data(mock_reporover_data_no_config)
        assert result is None

    def test_extract_configuration_from_data_none_configuration(
        self, mock_reporover_data_none_config
    ):
        """Test extract_configuration_from_data with None configuration."""
        result = extract_configuration_from_data(
            mock_reporover_data_none_config
        )
        assert result is None

    def test_extract_configuration_from_data_invalid_type(
        self, mock_reporover_data_invalid_config
    ):
        """Test extract_configuration_from_data with invalid configuration type."""
        result = extract_configuration_from_data(
            mock_reporover_data_invalid_config
        )
        assert result is None

    def test_extract_configuration_from_data_empty_configuration(
        self, mock_reporover_data_empty_config
    ):
        """Test extract_configuration_from_data with empty configuration."""
        result = extract_configuration_from_data(
            mock_reporover_data_empty_config
        )
        assert result is None

    def test_extract_configuration_from_data_malformed_reporover_data(self):
        """Test extract_configuration_from_data with malformed RepoRoverData."""
        mock_data = Mock()
        mock_data.reporover.get.side_effect = Exception("Access error")
        result = extract_configuration_from_data(mock_data)
        assert result is None

    def test_extract_configuration_from_data_missing_required_fields(self):
        """Test extract_configuration_from_data with missing required fields."""
        mock_data = Mock()
        mock_data.reporover = {"configuration": {"language": "python"}}
        result = extract_configuration_from_data(mock_data)
        assert result is None

    def test_extract_configuration_from_data_exception_handling(self):
        """Test extract_configuration_from_data handles exceptions properly."""
        mock_data = Mock()
        mock_data.reporover = {"configuration": {"invalid": "data"}}
        result = extract_configuration_from_data(mock_data)
        assert result is None

    def test_extract_configuration_from_data_with_partial_data(self):
        """Test extract_configuration_from_data with partial valid data."""
        mock_data = Mock()
        mock_data.reporover = {
            "configuration": {
                "language": "javascript",
                "stars": None,
                "forks": None,
                "created_after": None,
                "updated_after": None,
                "files": None,
                "topics": None,
                "max_depth": 3,
                "max_filter": 100,
                "max_display": 10,
                "search_query": "language:javascript",
                "timestamp": "2023-07-01T12:00:00Z",
            }
        }
        result = extract_configuration_from_data(mock_data)
        # this should have parsed in a valid fashion and
        # thus the result should not be none and there should
        # be data in the result, evident after some checks
        assert result is not None
        assert result.language == "javascript"
        assert result.max_depth == 3


class TestExtractReposFromData:
    """Test cases for the extract_repos_from_data function."""

    @pytest.fixture
    def mock_reporover_data_valid(self):
        """Create mock RepoRoverData with valid repositories."""
        mock_data = Mock()
        mock_data.reporover = {
            "repos": [
                {
                    "name": "test-repo",
                    "url": "https://github.com/user/test-repo",
                    "description": "A test repository",
                    "language": "Python",
                    "stars": 150,
                    "forks": 25,
                    "created_at": "2023-01-01T00:00:00Z",
                    "updated_at": "2023-06-15T00:00:00Z",
                    "files": ["README.md"],
                }
            ]
        }
        return mock_data

    @pytest.fixture
    def mock_reporover_data_no_repos(self):
        """Create mock RepoRoverData with no repositories."""
        mock_data = Mock()
        mock_data.reporover = {}
        return mock_data

    @pytest.fixture
    def mock_reporover_data_none_repos(self):
        """Create mock RepoRoverData with None repositories."""
        mock_data = Mock()
        mock_data.reporover = {"repos": None}
        return mock_data

    @pytest.fixture
    def mock_reporover_data_invalid_repos(self):
        """Create mock RepoRoverData with invalid repositories type."""
        mock_data = Mock()
        mock_data.reporover = {"repos": "invalid_string"}
        return mock_data

    @pytest.fixture
    def mock_reporover_data_empty_repos(self):
        """Create mock RepoRoverData with empty repositories list."""
        mock_data = Mock()
        mock_data.reporover = {"repos": []}
        return mock_data

    @pytest.fixture
    def mock_reporover_data_invalid_repo_item(self):
        """Create mock RepoRoverData with invalid repository items."""
        mock_data = Mock()
        mock_data.reporover = {
            "repos": [
                "not_a_dict",
                {"invalid_data": "missing_required_fields"},
            ]
        }
        return mock_data

    @pytest.fixture
    def mock_reporover_data_multiple_repos(self):
        """Create mock RepoRoverData with multiple repositories."""
        mock_data = Mock()
        mock_data.reporover = {
            "repos": [
                {
                    "name": "repo-1",
                    "url": "https://github.com/user/repo-1",
                    "description": "First test repository",
                    "language": "Python",
                    "stars": 150,
                    "forks": 25,
                    "created_at": "2023-01-01T00:00:00Z",
                    "updated_at": "2023-06-15T00:00:00Z",
                },
                {
                    "name": "repo-2",
                    "url": "https://github.com/user/repo-2",
                    "description": "Second test repository",
                    "language": "JavaScript",
                    "stars": 75,
                    "forks": 10,
                    "created_at": "2023-02-01T00:00:00Z",
                    "updated_at": "2023-05-15T00:00:00Z",
                },
            ]
        }
        return mock_data

    def test_extract_repos_from_data_success(self, mock_reporover_data_valid):
        """Test extract_repos_from_data with valid data."""
        result = extract_repos_from_data(mock_reporover_data_valid)
        assert result is not None
        assert len(result) == 1
        assert isinstance(result[0], RepositoryInfo)
        assert result[0].name == "test-repo"
        assert result[0].stars == 150
        assert result[0].forks == 25

    def test_extract_repos_from_data_multiple_repos(
        self, mock_reporover_data_multiple_repos
    ):
        """Test extract_repos_from_data with multiple repositories."""
        result = extract_repos_from_data(mock_reporover_data_multiple_repos)
        assert result is not None
        assert len(result) == 2
        assert result[0].name == "repo-1"
        assert result[0].language == "Python"
        assert result[1].name == "repo-2"
        assert result[1].language == "JavaScript"

    def test_extract_repos_from_data_no_repositories_key(
        self, mock_reporover_data_no_repos
    ):
        """Test extract_repos_from_data with no repositories key."""
        result = extract_repos_from_data(mock_reporover_data_no_repos)
        assert result is None

    def test_extract_repos_from_data_none_repositories(
        self, mock_reporover_data_none_repos
    ):
        """Test extract_repos_from_data with None repositories."""
        result = extract_repos_from_data(mock_reporover_data_none_repos)
        assert result is None

    def test_extract_repos_from_data_invalid_type(
        self, mock_reporover_data_invalid_repos
    ):
        """Test extract_repos_from_data with invalid repositories type."""
        result = extract_repos_from_data(mock_reporover_data_invalid_repos)
        assert result is None

    def test_extract_repos_from_data_empty_repositories(
        self, mock_reporover_data_empty_repos
    ):
        """Test extract_repos_from_data with empty repositories list."""
        result = extract_repos_from_data(mock_reporover_data_empty_repos)
        assert result is None

    def test_extract_repos_from_data_invalid_repo_items(
        self, mock_reporover_data_invalid_repo_item
    ):
        """Test extract_repos_from_data with invalid repository items."""
        result = extract_repos_from_data(mock_reporover_data_invalid_repo_item)
        assert result is None

    def test_extract_repos_from_data_malformed_reporover_data(self):
        """Test extract_repos_from_data with malformed RepoRoverData."""
        mock_data = Mock()
        mock_data.reporover.get.side_effect = Exception("Access error")
        result = extract_repos_from_data(mock_data)
        assert result is None

    def test_extract_repos_from_data_exception_handling(self):
        """Test extract_repos_from_data handles exceptions properly."""
        mock_data = Mock()
        mock_data.reporover = {"repos": [{"invalid": "data"}]}
        result = extract_repos_from_data(mock_data)
        assert result is None


class TestRoundTripSaveLoad:
    """Property-based tests for round-trip save/load operations using Hypothesis."""

    @given(
        language=st.one_of(st.none(), st.text(min_size=1, max_size=20)),
        stars=st.one_of(st.none(), st.integers(min_value=0, max_value=10000)),
        forks=st.one_of(st.none(), st.integers(min_value=0, max_value=1000)),
        created_after=st.one_of(st.none(), st.text(min_size=10, max_size=10)),
        updated_after=st.one_of(st.none(), st.text(min_size=10, max_size=10)),
        files=st.one_of(
            st.none(),
            st.lists(st.text(min_size=1, max_size=20), min_size=1, max_size=5),
        ),
        topics=st.one_of(
            st.none(),
            st.lists(st.text(min_size=1, max_size=15), min_size=1, max_size=3),
        ),
        max_depth=st.integers(min_value=1, max_value=10),
        max_filter=st.integers(min_value=1, max_value=500),
        max_display=st.integers(min_value=1, max_value=100),
        search_query=st.text(min_size=1, max_size=100),
    )
    def test_configuration_round_trip_save_load(  # noqa: PLR0913
        self,
        language,
        stars,
        forks,
        created_after,
        updated_after,
        files,
        topics,
        max_depth,
        max_filter,
        max_display,
        search_query,
    ):
        """Test round-trip save and load of configuration data."""
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
            "search_query": search_query,
        }
        original_config = DiscoverConfiguration(**configuration_data)
        repositories = []
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as temp_file:
            temp_file_path = temp_file.name
        try:
            save_success = _save_results_to_json(
                repositories,
                temp_file_path,
                configuration_data,
                search_query,
                files,
            )
            assert save_success is True
            loaded_data = load_results_from_json(temp_file_path)
            assert loaded_data is not None
            extracted_config = extract_configuration_from_data(loaded_data)
            assert extracted_config is not None
            assert extracted_config.language == original_config.language
            assert extracted_config.stars == original_config.stars
            assert extracted_config.forks == original_config.forks
            assert (
                extracted_config.created_after == original_config.created_after
            )
            assert (
                extracted_config.updated_after == original_config.updated_after
            )
            assert extracted_config.files == original_config.files
            assert extracted_config.topics == original_config.topics
            assert extracted_config.max_depth == original_config.max_depth
            assert extracted_config.max_filter == original_config.max_filter
            assert extracted_config.max_display == original_config.max_display
            assert (
                extracted_config.search_query == original_config.search_query
            )
        finally:
            # the file called temp_file_path should always exist at this
            # point and thus it is a good idea for it to be unlinked so
            # that there are no dependencies between this test and others
            os.unlink(temp_file_path)


class TestRepositoryContainsFiles:
    """Test cases for the _repository_contains_files function."""

    @pytest.fixture
    def mock_repository(self):
        """Create a mock repository for testing."""
        repo = Mock()
        repo.full_name = "test-owner/test-repo"
        return repo

    @pytest.fixture
    def headers(self):
        """Create mock headers for testing."""
        return {
            "Authorization": "token fake_token",
            "Accept": "application/vnd.github.v3+json",
        }

    @pytest.fixture
    def mock_repo_files_basic(self):
        """Create mock repository files for basic testing."""
        return [
            {"name": "README.md", "type": "file"},
            {"name": "requirements.txt", "type": "file"},
            {"name": "src", "type": "dir"},
            {"name": "tests", "type": "dir"},
        ]

    def test_repository_contains_files_all_found(
        self, mock_repository, headers, mock_repo_files_basic
    ):
        """Test _repository_contains_files when all required files are found."""
        required_files = ["README.md", "requirements.txt"]
        with patch(
            "reporover.discover._get_repository_files"
        ) as mock_get_files:
            mock_get_files.return_value = mock_repo_files_basic
            result = _repository_contains_files(
                mock_repository, required_files, 2, headers
            )
            assert result is True
            mock_get_files.assert_called_once_with(mock_repository, 2, headers)

    def test_repository_contains_files_partial_found(
        self, mock_repository, headers, mock_repo_files_basic
    ):
        """Test _repository_contains_files when only some required files are found."""
        required_files = ["README.md", "missing_file.txt"]
        with patch(
            "reporover.discover._get_repository_files"
        ) as mock_get_files:
            mock_get_files.return_value = mock_repo_files_basic
            result = _repository_contains_files(
                mock_repository, required_files, 2, headers
            )
            assert result is False
            mock_get_files.assert_called_once_with(mock_repository, 2, headers)

    def test_repository_contains_files_none_found(
        self, mock_repository, headers, mock_repo_files_basic
    ):
        """Test _repository_contains_files when no required files are found."""
        required_files = ["missing1.txt", "missing2.txt"]
        with patch(
            "reporover.discover._get_repository_files"
        ) as mock_get_files:
            mock_get_files.return_value = mock_repo_files_basic
            result = _repository_contains_files(
                mock_repository, required_files, 2, headers
            )
            assert result is False
            mock_get_files.assert_called_once_with(mock_repository, 2, headers)

    def test_repository_contains_files_empty_required_list(
        self, mock_repository, headers, mock_repo_files_basic
    ):
        """Test _repository_contains_files with empty required files list."""
        required_files = []
        with patch(
            "reporover.discover._get_repository_files"
        ) as mock_get_files:
            mock_get_files.return_value = mock_repo_files_basic
            result = _repository_contains_files(
                mock_repository, required_files, 2, headers
            )
            assert result is True
            mock_get_files.assert_called_once_with(mock_repository, 2, headers)

    def test_repository_contains_files_empty_repo_files(
        self, mock_repository, headers
    ):
        """Test _repository_contains_files with empty repository files."""
        required_files = ["README.md"]
        with patch(
            "reporover.discover._get_repository_files"
        ) as mock_get_files:
            mock_get_files.return_value = []
            result = _repository_contains_files(
                mock_repository, required_files, 2, headers
            )
            assert result is False
            mock_get_files.assert_called_once_with(mock_repository, 2, headers)

    def test_repository_contains_files_with_directories(
        self, mock_repository, headers, mock_repo_files_basic
    ):
        """Test _repository_contains_files when searching for directories."""
        required_files = ["src", "tests"]
        with patch(
            "reporover.discover._get_repository_files"
        ) as mock_get_files:
            mock_get_files.return_value = mock_repo_files_basic
            result = _repository_contains_files(
                mock_repository, required_files, 2, headers
            )
            assert result is True
            mock_get_files.assert_called_once_with(mock_repository, 2, headers)

    def test_repository_contains_files_mixed_files_and_dirs(
        self, mock_repository, headers, mock_repo_files_basic
    ):
        """Test _repository_contains_files with mixed files and directories."""
        required_files = ["README.md", "src"]
        with patch(
            "reporover.discover._get_repository_files"
        ) as mock_get_files:
            mock_get_files.return_value = mock_repo_files_basic
            result = _repository_contains_files(
                mock_repository, required_files, 2, headers
            )
            assert result is True
            mock_get_files.assert_called_once_with(mock_repository, 2, headers)

    def test_repository_contains_files_case_sensitive(
        self, mock_repository, headers, mock_repo_files_basic
    ):
        """Test _repository_contains_files is case sensitive."""
        required_files = ["readme.md"]
        with patch(
            "reporover.discover._get_repository_files"
        ) as mock_get_files:
            mock_get_files.return_value = mock_repo_files_basic
            result = _repository_contains_files(
                mock_repository, required_files, 2, headers
            )
            assert result is False
            mock_get_files.assert_called_once_with(mock_repository, 2, headers)

    def test_repository_contains_files_exception_handling(
        self, mock_repository, headers
    ):
        """Test _repository_contains_files handles exceptions gracefully."""
        required_files = ["README.md"]
        with patch(
            "reporover.discover._get_repository_files"
        ) as mock_get_files:
            mock_get_files.side_effect = Exception("API error")
            result = _repository_contains_files(
                mock_repository, required_files, 2, headers
            )
            assert result is False
            mock_get_files.assert_called_once_with(mock_repository, 2, headers)

    def test_repository_contains_files_malformed_file_info(
        self, mock_repository, headers
    ):
        """Test _repository_contains_files with malformed file info."""
        required_files = ["README.md"]
        malformed_files = [
            {"type": "file"},
            {"name": "README.md"},
            {"name": "test.py", "type": "file"},
        ]
        with patch(
            "reporover.discover._get_repository_files"
        ) as mock_get_files:
            mock_get_files.return_value = malformed_files
            result = _repository_contains_files(
                mock_repository, required_files, 2, headers
            )
            assert result is True
            mock_get_files.assert_called_once_with(mock_repository, 2, headers)

    def test_repository_contains_files_max_depth_parameter(
        self, mock_repository, headers, mock_repo_files_basic
    ):
        """Test _repository_contains_files passes max_depth parameter correctly."""
        required_files = ["README.md"]
        max_depth = 5
        with patch(
            "reporover.discover._get_repository_files"
        ) as mock_get_files:
            mock_get_files.return_value = mock_repo_files_basic
            _repository_contains_files(
                mock_repository, required_files, max_depth, headers
            )
            mock_get_files.assert_called_once_with(
                mock_repository, max_depth, headers
            )

    def test_repository_contains_files_duplicate_required_files(
        self, mock_repository, headers, mock_repo_files_basic
    ):
        """Test _repository_contains_files with duplicate required files."""
        required_files = ["README.md", "README.md", "requirements.txt"]
        with patch(
            "reporover.discover._get_repository_files"
        ) as mock_get_files:
            mock_get_files.return_value = mock_repo_files_basic
            result = _repository_contains_files(
                mock_repository, required_files, 2, headers
            )
            assert result is True
            mock_get_files.assert_called_once_with(mock_repository, 2, headers)

    def test_repository_contains_files_single_file_match(
        self, mock_repository, headers
    ):
        """Test _repository_contains_files with single file requirement."""
        required_files = ["pyproject.toml"]
        single_file = [{"name": "pyproject.toml", "type": "file"}]
        with patch(
            "reporover.discover._get_repository_files"
        ) as mock_get_files:
            mock_get_files.return_value = single_file
            result = _repository_contains_files(
                mock_repository, required_files, 1, headers
            )
            assert result is True
            mock_get_files.assert_called_once_with(mock_repository, 1, headers)
