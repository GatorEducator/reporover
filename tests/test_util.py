"""Test suite for the utility functions in the util module."""

import json
from unittest.mock import Mock, patch

import pytest
from hypothesis import given
from hypothesis import strategies as st
from rich.console import Console
from rich.progress import Progress

from reporover.util import print_json_string, read_usernames_from_json


@pytest.fixture
def progress():
    """Create a fixture to set up the Progress object for testing."""
    console = Console()
    progress = Progress(console=console)
    return progress


def test_print_json_string_empty(progress, capsys):
    """Confirm that print_json_string works correctly with an empty JSON string."""
    json_string = "{}"
    print_json_string(json_string, progress)
    captured = capsys.readouterr()
    assert captured.out == ""


def test_print_json_string_single_key_value(progress, capsys):
    """Confirm that print_json_string works correctly with a single key-value pair."""
    json_string = '{"key": "value"}'
    print_json_string(json_string, progress)
    captured = capsys.readouterr()
    assert "key: value" in captured.out


def test_print_json_string_multiple_key_values(progress, capsys):
    """Confirm that print_json_string works correctly with multiple key-value pairs."""
    json_string = '{"key1": "value1", "key2": "value2"}'
    print_json_string(json_string, progress)
    captured = capsys.readouterr()
    assert "key1: value1" in captured.out


def test_print_json_string_special_characters(progress, capsys):
    """Confirm that print_json_string works correctly with special characters in JSON string."""
    json_string = '{"key!@#": "value$%^"}'
    print_json_string(json_string, progress)
    captured = capsys.readouterr()
    assert "key!@#: value$%^" in captured.out


def test_print_json_string_invalid_json(progress):
    """Test print_json_string function with invalid JSON string."""
    json_string = '{"invalid": json}'
    with pytest.raises(json.JSONDecodeError):
        print_json_string(json_string, progress)


def test_read_usernames_from_json_empty(tmp_json_file):
    """Test reading usernames from an empty JSON file."""
    file_path = tmp_json_file({})
    usernames = read_usernames_from_json(file_path)
    assert usernames == []


@pytest.fixture
def tmp_json_file(tmp_path):
    """Fixture to create a temporary JSON file."""

    def create_tmp_json_file(content):
        file_path = tmp_path / "usernames.json"
        with file_path.open("w") as file:
            json.dump(content, file)
        return file_path

    return create_tmp_json_file


def test_read_usernames_from_json_single_username(tmp_json_file):
    """Test reading a single username from a JSON file."""
    file_path = tmp_json_file({"usernames": ["user1"]})
    usernames = read_usernames_from_json(file_path)
    assert usernames == ["user1"]


def test_read_usernames_from_json_multiple_usernames(tmp_json_file):
    """Test reading multiple usernames from a JSON file."""
    file_path = tmp_json_file({"usernames": ["user1", "user2", "user3"]})
    usernames = read_usernames_from_json(file_path)
    assert usernames == ["user1", "user2", "user3"]


def test_read_usernames_from_json_no_usernames_key(tmp_json_file):
    """Test reading usernames from a JSON file with no 'usernames' key."""
    file_path = tmp_json_file({"other_key": ["user1", "user2"]})
    usernames = read_usernames_from_json(file_path)
    assert usernames == []


def test_read_usernames_from_json_mixed_content(tmp_json_file):
    """Test reading usernames from a JSON file with mixed content."""
    file_path = tmp_json_file({"usernames": ["user1"], "other_key": ["user2"]})
    usernames = read_usernames_from_json(file_path)
    assert usernames == ["user1"]


@pytest.mark.property
@given(st.dictionaries(st.text(), st.text()))
def test_print_json_string_property(test_dict):
    """Property-based test for print_json_string with arbitrary dictionaries."""
    mock_console = Mock()
    progress = Mock()
    progress.console = mock_console
    json_string = json.dumps(test_dict)
    print_json_string(json_string, progress)
    if not test_dict:
        mock_console.print.assert_not_called()
    else:
        assert mock_console.print.call_count == len(test_dict)
        for key, value in test_dict.items():
            mock_console.print.assert_any_call(f"  {key}: {value}")


@pytest.mark.property
@given(st.lists(st.text()))
def test_read_usernames_from_json_property(username_list):
    """Property-based test for read_usernames_from_json with arbitrary username lists."""
    # create mock file path and mock file operations;
    # note that this also mocks the context manager behavior of
    # file opening since that is used in the function under test
    mock_path = Mock()
    mock_file = Mock()
    mock_context_manager = Mock()
    mock_context_manager.__enter__ = Mock(return_value=mock_file)
    mock_context_manager.__exit__ = Mock(return_value=None)
    mock_path.open.return_value = mock_context_manager
    # mock json.load to return our test data
    with patch("reporover.util.json.load") as mock_json_load:
        mock_json_load.return_value = {"usernames": username_list}
        # test the function
        result = read_usernames_from_json(mock_path)
        # confirm that the user names are correctly
        # inside of the list after calling the function
        assert result == username_list
