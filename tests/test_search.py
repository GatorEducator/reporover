"""Test cases for the search module."""

from reporover.search import create_repository_url


def test_create_repository_url_with_organization_name_only():
    """Test creating repository url for organization without language filter."""
    result = create_repository_url("testorg", None, 1)
    expected = "https://api.github.com/orgs/testorg/repos?per_page=100&page=1"
    assert result == expected


def test_create_repository_url_with_organization_name_and_language():
    """Test creating repository url for organization with language filter."""
    input = ["python"]
    result = create_repository_url("testorg", input, 2)
    expected = "https://api.github.com/orgs/testorg/repos?per_page=100&page=2"
    assert result == expected


def test_create_repository_url_without_organization_name_or_language():
    """Test creating repository url for global search without language filter."""
    result = create_repository_url(None, None, 1)
    expected = "https://api.github.com/search/repositories?q=is:public&per_page=100&page=1"
    assert result == expected


def test_create_repository_url_without_organization_name_with_language():
    """Test creating repository url for global search with language filter."""
    input = ["javascript"]
    result = create_repository_url(None, input, 3)
    expected = "https://api.github.com/search/repositories?q=is:public language:javascript&per_page=100&page=3"
    assert result == expected


def test_create_repository_url_with_empty_organization_name():
    """Test creating repository url when organization name is empty string."""
    result = create_repository_url("", None, 1)
    expected = "https://api.github.com/search/repositories?q=is:public&per_page=100&page=1"
    assert result == expected


def test_create_repository_url_with_empty_organization_name_and_language():
    """Test creating repository url when organization name is empty string with language."""
    input = ["go"]
    result = create_repository_url("", input, 1)
    expected = "https://api.github.com/search/repositories?q=is:public language:go&per_page=100&page=1"
    assert result == expected


def test_create_repository_url_different_page_numbers():
    """Test creating repository url with various page numbers."""
    result_page_5 = create_repository_url("myorg", None, 5)
    result_page_10 = create_repository_url(None, None, 10)
    assert "page=5" in result_page_5
    assert "page=10" in result_page_10


def test_create_repository_url_special_characters_in_organization():
    """Test creating repository url with special characters in organization name."""
    input = ["python"]
    result = create_repository_url("my-org_123", input, 1)
    expected = (
        "https://api.github.com/orgs/my-org_123/repos?per_page=100&page=1"
    )
    assert result == expected


def test_create_repository_url_special_characters_in_language():
    """Test creating repository url with special characters in language name."""
    input = ["c++"]
    result = create_repository_url(None, input, 1)
    expected = "https://api.github.com/search/repositories?q=is:public language:c++&per_page=100&page=1"
    assert result == expected
