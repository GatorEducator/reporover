"""Test cases for constants module."""

# ruff: noqa: PLR2004

from enum import Enum

from reporover.constants import (
    Data,
    GitHubAccessLevel,
    GitHubPullRequestNumber,
    GitHubRepositoryDetails,
    Numbers,
    PullRequestMessages,
    StatusCode,
    Symbols,
)


def test_data_is_enum():
    """Test that Data is an Enum class."""
    assert issubclass(Data, Enum)


def test_usernames_constant_value():
    """Test that USERNAMES has the correct constant value."""
    assert Data.USERNAMES.value == "usernames"


def test_usernames_constant_access():
    """Test that USERNAMES can be accessed as an attribute."""
    assert hasattr(Data, "USERNAMES")


def test_data_enum_members():
    """Test that Data enum has exactly the expected members."""
    expected_members = {"USERNAMES"}
    actual_members = {member.name for member in Data}
    assert actual_members == expected_members


def test_github_access_level_is_enum():
    """Test that GitHubAccessLevel is an Enum class."""
    assert issubclass(GitHubAccessLevel, Enum)


def test_github_access_level_values():
    """Test that GitHubAccessLevel has the correct values."""
    assert GitHubAccessLevel.READ.value == "read"
    assert GitHubAccessLevel.TRIAGE.value == "triage"
    assert GitHubAccessLevel.WRITE.value == "write"
    assert GitHubAccessLevel.MAINTAIN.value == "maintain"
    assert GitHubAccessLevel.ADMIN.value == "admin"


def test_github_access_level_members():
    """Test that GitHubAccessLevel enum has exactly the expected members."""
    expected_members = {"READ", "TRIAGE", "WRITE", "MAINTAIN", "ADMIN"}
    actual_members = {member.name for member in GitHubAccessLevel}
    assert actual_members == expected_members


def test_github_repositority_details_is_enum():
    """Test that GitHubRepositoryDetails is an Enum class."""
    assert issubclass(GitHubRepositoryDetails, Enum)


def test_github_repository_details_values():
    """Test that GitHubRepositoryDetails has the correct values."""
    assert GitHubRepositoryDetails.BRANCH_DEFAULT.value == "main"


def test_github_repository_details_members():
    """Test that GitHubRepositoryDetails enum has exactly the expected members."""
    expected_members = {"BRANCH_DEFAULT"}
    actual_members = {member.name for member in GitHubRepositoryDetails}
    assert actual_members == expected_members


def test_github_pull_request_number_is_enum():
    """Test that GitHubPullRequestNumber is an Enum class."""
    assert issubclass(GitHubPullRequestNumber, Enum)


def test_github_pull_request_number_values():
    """Test that GitHubPullRequestNumber has the correct values."""
    assert GitHubPullRequestNumber.ONE.value == 1
    assert GitHubPullRequestNumber.TWO.value == 2
    assert GitHubPullRequestNumber.THREE.value == 3
    assert GitHubPullRequestNumber.DEFAULT.value == 1


def test_github_pull_request_number_members():
    """Test that GitHubPullRequestNumber enum has exactly the expected members."""
    # DEFAULT is an alias, not a separate member
    expected_members = {
        "ONE",
        "TWO",
        "THREE",
    }
    actual_members = {member.name for member in GitHubPullRequestNumber}
    assert actual_members == expected_members


def test_github_pull_request_number_default_alias():
    """Test that DEFAULT is an alias for ONE with the same value."""
    assert GitHubPullRequestNumber.DEFAULT == GitHubPullRequestNumber.ONE
    assert (
        GitHubPullRequestNumber.DEFAULT.value
        == GitHubPullRequestNumber.ONE.value
    )
    assert GitHubPullRequestNumber.DEFAULT is GitHubPullRequestNumber.ONE


def test_github_pull_request_number_alias_accessibility():
    """Test that both DEFAULT and ONE can be accessed as attributes."""
    assert hasattr(GitHubPullRequestNumber, "DEFAULT")
    assert hasattr(GitHubPullRequestNumber, "ONE")
    # verify that two attributes reference the same object
    assert GitHubPullRequestNumber.DEFAULT is GitHubPullRequestNumber.ONE


def test_pull_request_messages_is_enum():
    """Test that PullRequestMessages is an Enum class."""
    assert issubclass(PullRequestMessages, Enum)


def test_pull_request_messages_values():
    """Test that PullRequestMessages has the correct values."""
    assert PullRequestMessages.MODIFIED_TO_PHRASE.value == (
        "Your access level for this GitHub repository has been modified to"
    )
    assert PullRequestMessages.ASSISTANCE_SENTENCE.value == (
        "Please contact the course instructor for assistance with access to your repository."
    )


def test_pull_request_messages_members():
    """Test that PullRequestMessages enum has exactly the expected members."""
    expected_members = {"MODIFIED_TO_PHRASE", "ASSISTANCE_SENTENCE"}
    actual_members = {member.name for member in PullRequestMessages}
    assert actual_members == expected_members


def test_status_code_is_enum():
    """Test that StatusCode is an Enum class."""
    assert issubclass(StatusCode, Enum)


def test_status_code_values():
    """Test that StatusCode has the correct values."""
    assert StatusCode.WORKING.value == 200
    assert StatusCode.CREATED.value == 201
    assert StatusCode.SUCCESS.value == 204
    assert StatusCode.BAD_REQUEST.value == 400
    assert StatusCode.UNAUTHORIZED.value == 401
    assert StatusCode.FORBIDDEN.value == 403
    assert StatusCode.NOT_FOUND.value == 404
    assert StatusCode.UNPROCESSABLE_ENTITY.value == 422
    assert StatusCode.INTERNAL_SERVER_ERROR.value == 500


def test_status_code_members():
    """Test that StatusCode enum has exactly the expected members."""
    expected_members = {
        "WORKING",
        "CREATED",
        "FAILURE",
        "SUCCESS",
        "BAD_REQUEST",
        "UNAUTHORIZED",
        "FORBIDDEN",
        "NOT_FOUND",
        "UNPROCESSABLE_ENTITY",
        "INTERNAL_SERVER_ERROR",
    }
    actual_members = {member.name for member in StatusCode}
    assert actual_members == expected_members


def test_numbers_is_enum():
    """Test that Numbers is an Enum class."""
    assert issubclass(Numbers, Enum)


def test_numbers_values():
    """Test that Numbers has the correct values."""
    assert Numbers.MAX_DISPLAY.value == 10
    assert Numbers.MAX_FILTER.value == 100
    assert Numbers.MAX_DESCRIPTION_LENGTH.value == 50


def test_numbers_members():
    """Test that Numbers enum has exactly the expected members."""
    expected_members = {
        "MAX_DISPLAY",
        "MAX_FILTER",
        "MAX_DESCRIPTION_LENGTH",
    }
    actual_members = {member.name for member in Numbers}
    assert actual_members == expected_members


def test_symbols_is_enum():
    """Test that Symbols is an Enum class."""
    assert issubclass(Symbols, Enum)


def test_symbols_values():
    """Test that Symbols has the correct values."""
    assert Symbols.ELLIPSIS.value == "..."
    assert Symbols.ERROR.value == ""
    assert Symbols.CHECK.value == "󰄬"
    assert Symbols.UNKNOWN.value == "Unknown"


def test_symbols_members():
    """Test that Symbols enum has exactly the expected members."""
    expected_members = {"ELLIPSIS", "ERROR", "CHECK", "UNKNOWN"}
    actual_members = {member.name for member in Symbols}
    assert actual_members == expected_members


def test_all_enums_accessible():
    """Test that all enum constants can be accessed as attributes."""
    # GitHubAccessLevel
    assert hasattr(GitHubAccessLevel, "READ")
    assert hasattr(GitHubAccessLevel, "TRIAGE")
    assert hasattr(GitHubAccessLevel, "WRITE")
    assert hasattr(GitHubAccessLevel, "MAINTAIN")
    assert hasattr(GitHubAccessLevel, "ADMIN")
    # GitHubPullRequestNumber
    assert hasattr(GitHubPullRequestNumber, "ONE")
    assert hasattr(GitHubPullRequestNumber, "TWO")
    assert hasattr(GitHubPullRequestNumber, "THREE")
    assert hasattr(GitHubPullRequestNumber, "DEFAULT")
    # PullRequestMessages
    assert hasattr(PullRequestMessages, "MODIFIED_TO_PHRASE")
    assert hasattr(PullRequestMessages, "ASSISTANCE_SENTENCE")
    # StatusCode
    assert hasattr(StatusCode, "WORKING")
    assert hasattr(StatusCode, "CREATED")
    assert hasattr(StatusCode, "SUCCESS")
    assert hasattr(StatusCode, "BAD_REQUEST")
    assert hasattr(StatusCode, "UNAUTHORIZED")
    assert hasattr(StatusCode, "FORBIDDEN")
    assert hasattr(StatusCode, "NOT_FOUND")
    assert hasattr(StatusCode, "UNPROCESSABLE_ENTITY")
    assert hasattr(StatusCode, "INTERNAL_SERVER_ERROR")
    # Numbers
    assert hasattr(Numbers, "MAX_DISPLAY")
    assert hasattr(Numbers, "MAX_FILTER")
    assert hasattr(Numbers, "MAX_DESCRIPTION_LENGTH")
    # Symbols
    assert hasattr(Symbols, "ELLIPSIS")
    assert hasattr(Symbols, "ERROR")
    assert hasattr(Symbols, "CHECK")
    assert hasattr(Symbols, "UNKNOWN")


def test_numbers_constant_access():
    """Test that Numbers constants can be accessed as attributes."""
    assert hasattr(Numbers, "MAX_DISPLAY")
    assert hasattr(Numbers, "MAX_FILTER")
    assert hasattr(Numbers, "MAX_DESCRIPTION_LENGTH")


def test_numbers_constant_types():
    """Test that Numbers constants have the correct types."""
    assert isinstance(Numbers.MAX_DISPLAY.value, int)
    assert isinstance(Numbers.MAX_FILTER.value, int)
    assert isinstance(Numbers.MAX_DESCRIPTION_LENGTH.value, int)


def test_numbers_constant_values_are_positive():
    """Test that Numbers constants have positive values."""
    assert Numbers.MAX_DISPLAY.value > 0
    assert Numbers.MAX_FILTER.value > 0
    assert Numbers.MAX_DESCRIPTION_LENGTH.value > 0


def test_symbols_constant_access():
    """Test that Symbols constants can be accessed as attributes."""
    assert hasattr(Symbols, "ELLIPSIS")
    assert hasattr(Symbols, "ERROR")
    assert hasattr(Symbols, "CHECK")
    assert hasattr(Symbols, "UNKNOWN")


def test_symbols_constant_types():
    """Test that Symbols constants have the correct types."""
    assert isinstance(Symbols.ELLIPSIS.value, str)
    assert isinstance(Symbols.ERROR.value, str)
    assert isinstance(Symbols.CHECK.value, str)
    assert isinstance(Symbols.UNKNOWN.value, str)


def test_symbols_ellipsis_is_unicode():
    """Test that ELLIPSIS is the correct Unicode character."""
    assert Symbols.ELLIPSIS.value == "..."
    assert len(Symbols.ELLIPSIS.value) == 3


def test_symbols_check_is_icon():
    """Test that CHECK is the correct icon character."""
    assert Symbols.CHECK.value == "󰄬"
    assert len(Symbols.CHECK.value) == 1


def test_symbols_unknown_is_word():
    """Test that UNKNOWN is the word 'Unknown'."""
    assert Symbols.UNKNOWN.value == "Unknown"
    assert isinstance(Symbols.UNKNOWN.value, str)


def test_all_enum_classes_are_subclasses_of_enum():
    """Test that all constant classes are subclasses of Enum."""
    assert issubclass(Data, Enum)
    assert issubclass(GitHubAccessLevel, Enum)
    assert issubclass(GitHubPullRequestNumber, Enum)
    assert issubclass(GitHubRepositoryDetails, Enum)
    assert issubclass(PullRequestMessages, Enum)
    assert issubclass(StatusCode, Enum)
    assert issubclass(Numbers, Enum)
    assert issubclass(Symbols, Enum)


def test_enum_members_are_unique():
    """Test that enum members within each enum are unique."""
    # check Numbers enum uniqueness
    numbers_values = [member.value for member in Numbers]
    assert len(numbers_values) == len(set(numbers_values))
    # check Symbols enum uniqueness
    symbols_values = [member.value for member in Symbols]
    assert len(symbols_values) == len(set(symbols_values))
