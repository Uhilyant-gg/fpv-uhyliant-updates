"""Turn a hanging test into a failure that shows where it hung.

Without this a stuck test keeps CI "in progress" for hours with no log.
"""

import faulthandler
import sys

import pytest

HANG_LIMIT_SECONDS = 180


@pytest.fixture(autouse=True)
def _hang_watchdog(request):
    faulthandler.dump_traceback_later(HANG_LIMIT_SECONDS, exit=True, file=sys.stderr)
    try:
        yield
    finally:
        faulthandler.cancel_dump_traceback_later()
