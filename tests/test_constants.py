"""Test cases for constants module."""

from enum import Enum

from reporover.constants import Data


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
