"""Test suite for RepoRover Pydantic models."""

# ruff: noqa: PLR2004

import json
from datetime import datetime

import pytest
from pydantic import ValidationError

from reporover.models import (
    DiscoverConfiguration,
    RepoRoverData,
    RepositoryInfo,
)


class TestRepositoryInfo:
    """Test cases for the RepositoryInfo model."""

    def test_repository_info_creation_with_all_fields(self):
        """Test creating RepositoryInfo with all fields provided."""
        created_at = datetime(2023, 1, 1, 12, 0, 0)
        updated_at = datetime(2023, 12, 1, 12, 0, 0)
        repo_info = RepositoryInfo(
            name="test-repo",
            url="https://github.com/user/test-repo",
            description="A test repository",
            language="Python",
            stars=100,
            forks=50,
            created_at=created_at,
            updated_at=updated_at,
            files=["README.md", "pyproject.toml"],
        )
        assert repo_info.name == "test-repo"
        assert repo_info.url == "https://github.com/user/test-repo"
        assert repo_info.description == "A test repository"
        assert repo_info.language == "Python"
        assert repo_info.stars == 100
        assert repo_info.forks == 50
        assert repo_info.created_at == created_at
        assert repo_info.updated_at == updated_at
        assert repo_info.files == ["README.md", "pyproject.toml"]

    def test_repository_info_creation_with_required_fields_only(self):
        """Test creating RepositoryInfo with only required fields."""
        created_at = datetime(2023, 1, 1, 12, 0, 0)
        updated_at = datetime(2023, 12, 1, 12, 0, 0)
        repo_info = RepositoryInfo(
            name="minimal-repo",
            url="https://github.com/user/minimal-repo",
            description=None,
            language=None,
            stars=0,
            forks=0,
            created_at=created_at,
            updated_at=updated_at,
            files=None,
        )
        assert repo_info.name == "minimal-repo"
        assert repo_info.url == "https://github.com/user/minimal-repo"
        assert repo_info.description is None
        assert repo_info.language is None
        assert repo_info.stars == 0
        assert repo_info.forks == 0
        assert repo_info.created_at == created_at
        assert repo_info.updated_at == updated_at
        assert repo_info.files is None

    def test_repository_info_missing_required_field_name(self):
        """Test RepositoryInfo validation fails when name is missing."""
        created_at = datetime(2023, 1, 1, 12, 0, 0)
        updated_at = datetime(2023, 12, 1, 12, 0, 0)
        with pytest.raises(ValidationError):
            RepositoryInfo(
                url="https://github.com/user/test-repo",
                description=None,
                language=None,
                stars=100,
                forks=50,
                created_at=created_at,
                updated_at=updated_at,
                files=None,
            )  # type: ignore

    def test_repository_info_missing_required_field_url(self):
        """Test RepositoryInfo validation fails when url is missing."""
        created_at = datetime(2023, 1, 1, 12, 0, 0)
        updated_at = datetime(2023, 12, 1, 12, 0, 0)
        with pytest.raises(ValidationError):
            RepositoryInfo(
                name="test-repo",
                description=None,
                language=None,
                stars=100,
                forks=50,
                created_at=created_at,
                updated_at=updated_at,
                files=None,
            )  # type: ignore

    def test_repository_info_missing_required_field_stars(self):
        """Test RepositoryInfo validation fails when stars is missing."""
        created_at = datetime(2023, 1, 1, 12, 0, 0)
        updated_at = datetime(2023, 12, 1, 12, 0, 0)
        with pytest.raises(ValidationError):
            RepositoryInfo(
                name="test-repo",
                url="https://github.com/user/test-repo",
                description=None,
                language=None,
                forks=50,
                created_at=created_at,
                updated_at=updated_at,
                files=None,
            )  # type: ignore

    def test_repository_info_missing_required_field_forks(self):
        """Test RepositoryInfo validation fails when forks is missing."""
        created_at = datetime(2023, 1, 1, 12, 0, 0)
        updated_at = datetime(2023, 12, 1, 12, 0, 0)
        with pytest.raises(ValidationError):
            RepositoryInfo(
                name="test-repo",
                url="https://github.com/user/test-repo",
                description=None,
                language=None,
                stars=100,
                created_at=created_at,
                updated_at=updated_at,
                files=None,
            )  # type: ignore

    def test_repository_info_missing_required_field_created_at(self):
        """Test RepositoryInfo validation fails when created_at is missing."""
        updated_at = datetime(2023, 12, 1, 12, 0, 0)
        with pytest.raises(ValidationError):
            RepositoryInfo(
                name="test-repo",
                url="https://github.com/user/test-repo",
                description=None,
                language=None,
                stars=100,
                forks=50,
                updated_at=updated_at,
                files=None,
            )  # type: ignore

    def test_repository_info_missing_required_field_updated_at(self):
        """Test RepositoryInfo validation fails when updated_at is missing."""
        created_at = datetime(2023, 1, 1, 12, 0, 0)
        with pytest.raises(ValidationError):
            RepositoryInfo(
                name="test-repo",
                url="https://github.com/user/test-repo",
                description=None,
                language=None,
                stars=100,
                forks=50,
                created_at=created_at,
                files=None,
            )  # type: ignore

    def test_repository_info_model_dump_excludes_none_values(self):
        """Test that model_dump excludes None values when exclude_none is True."""
        created_at = datetime(2023, 1, 1, 12, 0, 0)
        updated_at = datetime(2023, 12, 1, 12, 0, 0)
        repo_info = RepositoryInfo(
            name="test-repo",
            url="https://github.com/user/test-repo",
            description=None,
            language=None,
            stars=100,
            forks=50,
            created_at=created_at,
            updated_at=updated_at,
            files=None,
        )
        dumped = repo_info.model_dump(exclude_none=True)
        assert "description" not in dumped
        assert "language" not in dumped
        assert "files" not in dumped
        assert dumped["name"] == "test-repo"
        assert dumped["url"] == "https://github.com/user/test-repo"
        assert dumped["stars"] == 100
        assert dumped["forks"] == 50


class TestDiscoverConfiguration:
    """Test cases for the DiscoverConfiguration model."""

    def test_discover_configuration_creation_with_all_fields(self):
        """Test creating DiscoverConfiguration with all fields provided."""
        config = DiscoverConfiguration(
            command="discover",
            language="Python",
            stars=10,
            forks=5,
            created_after="2023-01-01",
            updated_after="2023-06-01",
            files=["README.md", "pyproject.toml"],
            topics=["python", "cli"],
            max_depth=2,
            max_filter=100,
            max_display=50,
            search_query="language:Python stars:>=10",
        )
        assert config.command == "discover"
        assert config.language == "Python"
        assert config.stars == 10
        assert config.forks == 5
        assert config.created_after == "2023-01-01"
        assert config.updated_after == "2023-06-01"
        assert config.files == ["README.md", "pyproject.toml"]
        assert config.topics == ["python", "cli"]
        assert config.max_depth == 2
        assert config.max_filter == 100
        assert config.max_display == 50
        assert config.search_query == "language:Python stars:>=10"

    def test_discover_configuration_creation_with_required_fields_only(self):
        """Test creating DiscoverConfiguration with only required fields."""
        config = DiscoverConfiguration(
            command="discover",
            language=None,
            stars=None,
            forks=None,
            created_after=None,
            updated_after=None,
            files=None,
            topics=None,
            max_depth=None,
            max_filter=None,
            max_display=None,
            search_query="is:public",
        )
        assert config.command == "discover"
        assert config.language is None
        assert config.stars is None
        assert config.forks is None
        assert config.created_after is None
        assert config.updated_after is None
        assert config.files is None
        assert config.topics is None
        assert config.max_depth is None
        assert config.max_filter is None
        assert config.max_display is None
        assert config.search_query == "is:public"

    def test_discover_configuration_missing_required_search_query(self):
        """Test DiscoverConfiguration validation fails when search_query is missing."""
        with pytest.raises(ValidationError):
            DiscoverConfiguration(
                command="discover",
                language="Python",
                stars=10,
                forks=None,
                created_after=None,
                updated_after=None,
                files=None,
                topics=None,
                max_depth=None,
                max_filter=None,
                max_display=None,
            )  # type: ignore

    def test_discover_configuration_model_dump_excludes_none_values(self):
        """Test that model_dump excludes None values when exclude_none is True."""
        config = DiscoverConfiguration(
            command="discover",
            language="Python",
            stars=10,
            forks=None,
            created_after=None,
            updated_after=None,
            files=None,
            topics=None,
            max_depth=None,
            max_filter=None,
            max_display=None,
            search_query="language:Python",
        )
        dumped = config.model_dump(exclude_none=True)
        assert "forks" not in dumped
        assert "created_after" not in dumped
        assert "updated_after" not in dumped
        assert "files" not in dumped
        assert "topics" not in dumped
        assert "max_depth" not in dumped
        assert "max_filter" not in dumped
        assert "max_display" not in dumped
        assert dumped["command"] == "discover"
        assert dumped["language"] == "Python"
        assert dumped["stars"] == 10
        assert dumped["search_query"] == "language:Python"


class TestRepoRoverData:
    """Test cases for the RepoRoverData model."""

    def test_repo_rover_data_creation(self):
        """Test creating RepoRoverData with valid data structure."""
        data = RepoRoverData(
            reporover={
                "configuration": {
                    "command": "discover",
                    "search_query": "is:public",
                },
                "repos": [
                    {
                        "name": "test-repo",
                        "url": "https://github.com/user/test-repo",
                    }
                ],
            }
        )
        assert "configuration" in data.reporover
        assert "repos" in data.reporover
        config_dict = data.reporover["configuration"]
        repos_list = data.reporover["repos"]
        assert config_dict["command"] == "discover"  # type: ignore
        assert len(repos_list) == 1  # type: ignore

    def test_repo_rover_data_missing_required_field(self):
        """Test RepoRoverData validation fails when reporover is missing."""
        with pytest.raises(ValidationError):
            RepoRoverData()  # type: ignore

    def test_create_discover_data_class_method(self):
        """Test the create_discover_data class method creates proper structure."""
        created_at = datetime(2023, 1, 1, 12, 0, 0)
        updated_at = datetime(2023, 12, 1, 12, 0, 0)
        configuration = DiscoverConfiguration(
            command="discover",
            language="Python",
            stars=10,
            forks=None,
            created_after=None,
            updated_after=None,
            files=None,
            topics=None,
            max_depth=None,
            max_filter=None,
            max_display=None,
            search_query="language:Python",
        )
        repositories = [
            RepositoryInfo(
                name="test-repo",
                url="https://github.com/user/test-repo",
                description=None,
                language=None,
                stars=100,
                forks=50,
                created_at=created_at,
                updated_at=updated_at,
                files=None,
            )
        ]
        data = RepoRoverData.create_discover_data(configuration, repositories)
        assert "configuration" in data.reporover
        assert "repos" in data.reporover
        config_dict = data.reporover["configuration"]
        repos_list = data.reporover["repos"]
        assert config_dict["command"] == "discover"  # type: ignore
        assert config_dict["language"] == "Python"  # type: ignore
        assert config_dict["stars"] == 10  # type: ignore
        assert len(repos_list) == 1  # type: ignore
        assert repos_list[0]["name"] == "test-repo"  # type: ignore

    def test_create_discover_data_with_empty_repositories(self):
        """Test create_discover_data works with empty repository list."""
        configuration = DiscoverConfiguration(
            command="discover",
            language=None,
            stars=None,
            forks=None,
            created_after=None,
            updated_after=None,
            files=None,
            topics=None,
            max_depth=None,
            max_filter=None,
            max_display=None,
            search_query="is:public",
        )
        repositories = []
        data = RepoRoverData.create_discover_data(configuration, repositories)
        assert "configuration" in data.reporover
        assert "repos" in data.reporover
        repos_list = data.reporover["repos"]
        assert len(repos_list) == 0  # type: ignore

    def test_create_discover_data_json_serializable(self):
        """Test that create_discover_data produces JSON-serializable output."""
        created_at = datetime(2023, 1, 1, 12, 0, 0)
        updated_at = datetime(2023, 12, 1, 12, 0, 0)
        configuration = DiscoverConfiguration(
            command="discover",
            language="Python",
            stars=None,
            forks=None,
            created_after=None,
            updated_after=None,
            files=None,
            topics=None,
            max_depth=None,
            max_filter=None,
            max_display=None,
            search_query="language:Python",
        )
        repositories = [
            RepositoryInfo(
                name="test-repo",
                url="https://github.com/user/test-repo",
                description=None,
                language=None,
                stars=100,
                forks=50,
                created_at=created_at,
                updated_at=updated_at,
                files=None,
            )
        ]
        data = RepoRoverData.create_discover_data(configuration, repositories)
        json_str = json.dumps(data.model_dump(), default=str)
        assert isinstance(json_str, str)
        assert len(json_str) > 0
