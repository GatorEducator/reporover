"""Test suite for the status module."""

from typing import List

import hypothesis.strategies as st
import pytest
from hypothesis import given

from reporover.constants import StatusCode
from reporover.status import get_status_from_codes


@pytest.mark.parametrize(
    "status_codes,expected",
    [
        # test case 1: empty list should return False (no failures)
        ([], False),
        # test case 2: all success status codes should return False
        (
            [[StatusCode.SUCCESS, StatusCode.WORKING, StatusCode.CREATED]],
            False,
        ),
        # test case 3: one failure among success codes should return True
        (
            [[StatusCode.SUCCESS, StatusCode.FAILURE, StatusCode.WORKING]],
            True,
        ),
        # test case 4: multiple lists with no failures should return False
        (
            [
                [StatusCode.SUCCESS, StatusCode.WORKING],
                [StatusCode.CREATED, StatusCode.SUCCESS],
            ],
            False,
        ),
        # test case 5: multiple lists with one containing a failure should return True
        (
            [
                [StatusCode.SUCCESS, StatusCode.WORKING],
                [StatusCode.FAILURE, StatusCode.SUCCESS],
            ],
            True,
        ),
        # test case 6: multiple lists all containing failures should return True
        (
            [
                [StatusCode.FAILURE, StatusCode.WORKING],
                [StatusCode.FAILURE, StatusCode.SUCCESS],
            ],
            True,
        ),
        # test case 7: single element list with failure should return True
        ([[StatusCode.FAILURE]], True),
        # test case 8: single element list with success should return False
        ([[StatusCode.SUCCESS]], False),
    ],
)
def test_get_status_from_codes(
    status_codes: List[List[StatusCode | None]], expected: bool
) -> None:
    """Test the get_status_from_codes function with various inputs."""
    # get the result of the function under test
    result = get_status_from_codes(status_codes)
    # check that the result matches the expected outcome
    assert result == expected


@pytest.mark.property
@given(
    st.lists(
        st.lists(
            st.sampled_from(list(StatusCode)),
            min_size=0,
            max_size=10,
        ),
        min_size=0,
        max_size=10,
    )
)
def test_get_status_from_codes_property(
    status_codes: List[List[StatusCode | None]],
) -> None:
    """Use property-based testing to verify the get_status_from_codes function."""
    # calculate the expected result manually based on our property
    expected = any(
        StatusCode.FAILURE in internal_status_code
        for internal_status_code in status_codes
    )
    # get the result of the function under test
    result = get_status_from_codes(status_codes)
    # check that the result matches our expected property
    assert result == expected
    # verify the function's logic explicitly
    if expected:
        # if we expect True, at least one list should have a FAILURE
        assert any(
            StatusCode.FAILURE in internal_list
            for internal_list in status_codes
        )
    else:
        # if we expect False, no list should have a FAILURE
        assert all(
            StatusCode.FAILURE not in internal_list
            for internal_list in status_codes
        )
