"""Tests for HassGetCurrentDate intent handler."""

from unittest.mock import patch

import pytest

from .conftest import TEST_DATETIME


@pytest.mark.asyncio
async def test_get_date(async_converse):
    """Test HassGetCurrentDate intent."""
    with patch("default_agent.intents.get_current_date.datetime") as mock_datetime:
        mock_datetime.now.return_value = TEST_DATETIME
        success, response = await async_converse("what's the date")
    assert success, "Intent recognition failed"
    assert response == "September 17th, 2013"
