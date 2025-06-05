"""Determine the status of program runs based on codes."""

from typing import List

from reporover.constants import StatusCode


def get_status_from_codes(
    status_codes: List[List[StatusCode]],
) -> bool:
    """Determine the status of program runs based on codes."""
    # determine if there was at least one error
    # in the status codes list by using iteration
    overall_failure = False
    for internal_status_code in status_codes:
        if any(
            status_code == StatusCode.FAILURE
            for status_code in internal_status_code
        ):
            overall_failure = True
    # if there was at least one error, return
    # the overall status that is now True,
    # otherwise will return default value of False
    return overall_failure
