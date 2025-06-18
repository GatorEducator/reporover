"""Create Pydantic models for RepoRover data structures."""

from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class RepositoryInfo(BaseModel):
    """Model for GitHub repository information."""

    name: str = Field(..., description="The name of the repository")
    url: str = Field(..., description="The URL of the repository")
    description: Optional[str] = Field(
        None, description="The description of the repository"
    )
    language: Optional[str] = Field(
        None, description="The programming language of the repository"
    )
    stars: int = Field(
        ..., description="The number of stars the repository has"
    )
    forks: int = Field(
        ..., description="The number of forks the repository has"
    )
    created_at: datetime = Field(
        ..., description="The date when the repository was created"
    )
    updated_at: datetime = Field(
        ..., description="The date when the repository was last updated"
    )
    files: Optional[List[str]] = Field(
        None,
        description="List of files found in the repository that match the search criteria",
    )


class DiscoverConfiguration(BaseModel):
    """Model for discover command configuration."""

    command: str = Field(
        default="discover", description="The subcommand that was run"
    )
    language: Optional[str] = Field(
        None, description="Programming language filter"
    )
    stars: Optional[int] = Field(None, description="Minimum number of stars")
    forks: Optional[int] = Field(None, description="Minimum number of forks")
    created_after: Optional[str] = Field(
        None, description="Date after which repository was created"
    )
    updated_after: Optional[str] = Field(
        None, description="Date after which repository was updated"
    )
    files: Optional[List[str]] = Field(
        None, description="List of files to search for"
    )
    topics: Optional[List[str]] = Field(
        None, description="List of topics to filter by"
    )
    max_depth: Optional[int] = Field(
        None, description="Maximum depth for file search"
    )
    max_filter: Optional[int] = Field(
        None, description="Maximum number of repositories to filter"
    )
    max_display: Optional[int] = Field(
        None, description="Maximum number of repositories to display"
    )
    search_query: str = Field(
        ..., description="The constructed GitHub search query"
    )


class RepoRoverData(BaseModel):
    """Model for the complete RepoRover data structure."""

    reporover: Dict[str, object] = Field(
        ..., description="Container for RepoRover data"
    )

    @classmethod
    def create_discover_data(
        cls,
        configuration: DiscoverConfiguration,
        repositories: List[RepositoryInfo],
    ) -> "RepoRoverData":
        """Create a RepoRoverData instance for discover command results."""
        return cls(
            reporover={
                "configuration": configuration.model_dump(exclude_none=True),
                "repos": [
                    repo.model_dump(exclude_none=True) for repo in repositories
                ],
            }
        )
