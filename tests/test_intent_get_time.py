"""Tests for HassGetCurrentTime intent handler."""

from unittest.mock import patch

import pytest

from .conftest import TEST_DATETIME


@pytest.mark.asyncio
async def test_get_time(async_converse):
    """Test HassGetCurrentTime intent."""
    with patch("default_agent.intents.get_current_time.datetime") as mock_datetime:
        mock_datetime.now.return_value = TEST_DATETIME
        success, response = await async_converse("what time is it")
    assert success, "Intent recognition failed"
    assert response == "1:02 AM"
