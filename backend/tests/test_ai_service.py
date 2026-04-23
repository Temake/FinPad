"""Tests for AI expense parsing safety and deterministic behavior."""

import pytest

from app.core.ai_service import _validate_ai_parsed_result, parse_expense_text


@pytest.mark.asyncio
async def test_parse_expense_text_prefers_deterministic_parser():
    """Common deterministic patterns should parse without AI dependence."""
    result = await parse_expense_text("Bought suya 2k")
    assert result["amount"] == 2000
    assert result["category"] == "Food & Groceries"
    assert result["confidence"] >= 0.6


def test_validate_ai_parsed_result_rejects_low_confidence():
    """Low-confidence AI output should be rejected as untrusted."""
    result = {
        "amount": 2500,
        "description": "Snacks",
        "category": "Food & Groceries",
        "confidence": 0.2,
    }
    validated = _validate_ai_parsed_result(
        result,
        ["Food & Groceries", "Transport", "Other"],
        "snacks 2500",
    )
    assert validated is None


def test_validate_ai_parsed_result_rejects_invalid_amount():
    """Non-positive or invalid amounts should be rejected."""
    result = {
        "amount": -10,
        "description": "Invalid",
        "category": "Other",
        "confidence": 0.9,
    }
    validated = _validate_ai_parsed_result(result, ["Other"], "invalid")
    assert validated is None
