"""Test cases for discover module."""

# ruff: noqa: PLR2004

from unittest.mock import Mock, patch

import pytest
from rich.console import Console

from reporover.constants import Numbers, StatusCode
from reporover.discover import (
    _build_search_query,
    _display_search_results,
    search_repositories,
)


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
        with patch.object(console, "print") as mock_print:
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
        with patch.object(console, "print") as mock_print:
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
        with patch.object(console, "print") as mock_print:
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
        with patch.object(console, "print") as mock_print:
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
        with patch.object(console, "print") as mock_print:
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
        with patch.object(console, "print") as mock_print:
            _display_search_results(repositories, console)
            assert mock_print.call_count >= 2

    def test_display_search_results_empty_repositories(self, console):
        """Test _display_search_results with empty repository list."""
        repositories = Mock()
        repositories.__iter__ = Mock(return_value=iter([]))
        repositories.totalCount = 0
        with patch.object(console, "print") as mock_print:
            _display_search_results(repositories, console)
            assert mock_print.call_count >= 2

    def test_display_search_results_total_count_exceeds_max(
        self, console, mock_repository
    ):
        """Test _display_search_results when total count exceeds max display."""
        repositories = Mock()
        repositories.__iter__ = Mock(return_value=iter([mock_repository]))
        repositories.totalCount = 50
        with patch.object(console, "print") as mock_print:
            _display_search_results(repositories, console)
            assert mock_print.call_count >= 2

    def test_display_search_results_total_count_equals_max(self, console):
        """Test _display_search_results when total count equals max display."""
        mock_repos = []
        for i in range(Numbers.MAX_DISPLAY.value):
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
        repositories.totalCount = Numbers.MAX_DISPLAY.value
        with patch.object(console, "print") as mock_print:
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
        with patch.object(console, "print"):
            result = search_repositories(
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
        with patch.object(console, "print"):
            result = search_repositories(
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
        from github import GithubException

        mock_github_instance.search_repositories.side_effect = GithubException(
            status=404, data="Not found"
        )
        with patch.object(console, "print") as mock_print:
            result = search_repositories(
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
            result = search_repositories(
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
        with patch.object(console, "print"):
            result = search_repositories(
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
        with patch.object(console, "print"):
            result = search_repositories(
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
        with patch.object(console, "print"):
            result = search_repositories(
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
        from reporover.discover import MAX_DISPLAY, MAX_FILTER

        assert MAX_FILTER == 200
        assert MAX_DISPLAY == 20

    @patch("reporover.discover.github.Github")
    def test_search_repositories_query_building_called(
        self, mock_github_class, console, mock_repository
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
        with patch(
            "reporover.discover._build_search_query"
        ) as mock_build_query:
            mock_build_query.return_value = "language:python stars:>=100"
            with patch.object(console, "print"):
                result = search_repositories(
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
                result = search_repositories(
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
