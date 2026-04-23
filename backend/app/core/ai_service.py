"""AI Service using Google Gemini for expense categorization and receipt OCR."""

import json
import logging
import re
from typing import TypedDict
from datetime import date

from google import genai
from google.genai import types
from PIL import Image
import io

from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# Configure Gemini client
_client = None
if settings.GEMINI_API_KEY:
    _client = genai.Client(api_key=settings.GEMINI_API_KEY)


# Default categories that match the seeded database categories
DEFAULT_CATEGORIES = [
    "Food & Groceries",
    "Transport",
    "Airtime & Data",
    "Bills & Utilities",
    "Shopping",
    "Entertainment",
    "Health",
    "Education",
    "Family & Gifts",
    "Savings",
    "Other",
]

MAX_PARSED_AMOUNT = 100_000_000.0
MAX_PARSED_DESCRIPTION_LENGTH = 200
AI_PARSE_MIN_CONFIDENCE = 0.55


class ParsedExpense(TypedDict):
    """Structured expense data extracted by AI."""
    amount: float | None
    description: str | None
    category: str
    confidence: float  # 0.0 - 1.0


class ReceiptData(TypedDict):
    """Structured receipt data extracted by AI."""
    merchant: str | None
    amount: float | None
    items: list[str]
    date: str | None  # ISO format
    category: str
    confidence: float


# System prompts
EXPENSE_PARSE_PROMPT = """You are a Nigerian expense parsing assistant. Parse the user's expense message and extract:
1. Amount in Naira (convert "k" = thousand, e.g. "2k" = 2000)
2. A brief description
3. The most appropriate category from this list: {categories}

Common Nigerian terms:
- suya, shawarma, amala = Food & Groceries
- danfo, keke, bolt, uber, fuel, petrol = Transport  
- airtime, data, MTN, Glo, Airtel = Airtime & Data
- NEPA, PHCN, light bill, water = Bills & Utilities
- POS = could be Shopping or Other depending on context

Respond ONLY with valid JSON in this exact format:
{{"amount": <number or null>, "description": "<brief description>", "category": "<exact category name>", "confidence": <0.0-1.0>}}

Examples:
- "bought suya 2k" → {{"amount": 2000, "description": "Suya", "category": "Food & Groceries", "confidence": 0.95}}
- "uber to VI 3500" → {{"amount": 3500, "description": "Uber to VI", "category": "Transport", "confidence": 0.95}}
- "recharged 1k airtime" → {{"amount": 1000, "description": "Airtime recharge", "category": "Airtime & Data", "confidence": 0.95}}
"""

RECEIPT_OCR_PROMPT = """You are analyzing a receipt image from Nigeria. Extract:
1. Merchant/store name
2. Total amount in Naira
3. List of items purchased (brief)
4. Date if visible (format as YYYY-MM-DD)
5. Most appropriate category from: {categories}

Respond ONLY with valid JSON:
{{"merchant": "<name or null>", "amount": <number or null>, "items": ["item1", "item2"], "date": "<YYYY-MM-DD or null>", "category": "<category>", "confidence": <0.0-1.0>}}

If the image is unclear or not a receipt, return:
{{"merchant": null, "amount": null, "items": [], "date": null, "category": "Other", "confidence": 0.0}}
"""


def _get_client():
    """Get the Gemini client instance."""
    if not settings.GEMINI_API_KEY or not _client:
        raise ValueError("GEMINI_API_KEY not configured")
    return _client


def _parse_json_response(text: str) -> dict:
    """Extract and parse JSON from Gemini response."""
    # Try to find JSON in the response
    text = text.strip()
    
    # Remove markdown code blocks if present
    if text.startswith("```"):
        text = re.sub(r"```(?:json)?\n?", "", text)
        text = text.strip()
    
    # Find JSON object in response
    json_match = re.search(r"\{.*\}", text, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group())
        except json.JSONDecodeError:
            pass
    
    raise ValueError(f"Could not parse JSON from response: {text}")


def _normalize_category(category: str | None, categories: list[str]) -> str:
    """Map category values to known categories (case-insensitive), else Other."""
    if not category:
        return "Other"

    lookup = {c.lower(): c for c in categories}
    return lookup.get(str(category).strip().lower(), "Other")


def _validate_ai_parsed_result(result: dict, categories: list[str], fallback_text: str) -> ParsedExpense | None:
    """Treat AI output as untrusted and accept only strictly valid parsed expense data."""
    try:
        amount_raw = result.get("amount")
        amount = float(amount_raw) if amount_raw is not None else None
        if amount is None or amount <= 0 or amount > MAX_PARSED_AMOUNT:
            return None

        confidence = float(result.get("confidence", 0.0))
        if confidence < AI_PARSE_MIN_CONFIDENCE or confidence > 1.0:
            return None

        description = (result.get("description") or fallback_text).strip()
        description = description[:MAX_PARSED_DESCRIPTION_LENGTH]

        category = _normalize_category(result.get("category"), categories)

        return ParsedExpense(
            amount=amount,
            description=description,
            category=category,
            confidence=confidence,
        )
    except (TypeError, ValueError):
        return None


async def parse_expense_text(text: str, custom_categories: list[str] | None = None) -> ParsedExpense:
    """
    Parse natural language expense description into structured data.
    
    Args:
        text: User's expense description (e.g., "bought suya 2k")
        custom_categories: Optional list of user's custom categories
    
    Returns:
        ParsedExpense with amount, description, category, and confidence
    """
    categories = custom_categories or DEFAULT_CATEGORIES
    
    # Deterministic parser is primary for reliability and predictable behavior.
    quick_result = _quick_parse(text)
    if quick_result and quick_result.get("amount"):
        return quick_result
    
    # Use Gemini for complex parsing
    try:
        client = _get_client()
        prompt = EXPENSE_PARSE_PROMPT.format(categories=", ".join(categories))
        
        response = client.models.generate_content(
            model=settings.AI_MODEL,
            contents=f"{prompt}\n\nUser message: {text}",
            config=types.GenerateContentConfig(
                temperature=0.1,  # Low temperature for consistent parsing
                max_output_tokens=200,
            ),
        )
        
        result = _parse_json_response(response.text)
        
        validated = _validate_ai_parsed_result(result, categories, text)
        if validated:
            return validated

        logger.warning("AI output rejected by strict validation rules")
        return ParsedExpense(
            amount=None,
            description=text[:MAX_PARSED_DESCRIPTION_LENGTH],
            category="Other",
            confidence=0.3,
        )
        
    except Exception as e:
        logger.warning(f"AI parsing failed: {e}, using fallback")
        return quick_result or _quick_parse(text) or ParsedExpense(
            amount=None,
            description=text[:MAX_PARSED_DESCRIPTION_LENGTH],
            category="Other",
            confidence=0.3,
        )


def _quick_parse(text: str) -> ParsedExpense | None:
    """Quick regex-based parsing for common patterns."""
    text_lower = text.lower()
    
    # Extract amount (handles "2k", "2000", "2,000", "₦2000")
    amount = None
    amount_patterns = [
        r"₦?\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s*k\b",  # 2k, 2.5k
        r"₦?\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\b",       # 2000, 2,000
    ]
    
    for pattern in amount_patterns:
        match = re.search(pattern, text_lower)
        if match:
            num_str = match.group(1).replace(",", "")
            amount = float(num_str)
            if "k" in text_lower[match.end():match.end()+2]:
                amount *= 1000
            elif pattern == amount_patterns[0]:  # Was the 'k' pattern
                amount *= 1000
            break
    
    # Category detection keywords
    category_keywords = {
        "Food & Groceries": ["food", "suya", "shawarma", "amala", "rice", "eat", "lunch", "dinner", "breakfast", "snack", "restaurant", "eatery", "pepper soup"],
        "Transport": ["uber", "bolt", "danfo", "keke", "taxi", "bus", "fuel", "petrol", "transport", "fare", "okada"],
        "Airtime & Data": ["airtime", "data", "mtn", "glo", "airtel", "9mobile", "recharge", "subscription"],
        "Bills & Utilities": ["nepa", "phcn", "electricity", "light bill", "water", "dstv", "gotv", "cable", "internet", "wifi"],
        "Shopping": ["bought", "shop", "market", "clothes", "shoes", "bag", "pos"],
        "Entertainment": ["movie", "cinema", "club", "party", "outing", "games", "netflix", "spotify"],
        "Health": ["hospital", "clinic", "medicine", "drug", "doctor", "pharmacy", "medical"],
        "Education": ["school", "book", "course", "tuition", "lesson", "training"],
        "Family & Gifts": ["gift", "family", "wedding", "birthday", "send", "transfer"],
    }
    
    category = "Other"
    for cat, keywords in category_keywords.items():
        if any(kw in text_lower for kw in keywords):
            category = cat
            break
    
    if amount:
        return ParsedExpense(
            amount=amount,
            description=text[:100],  # Truncate
            category=category,
            confidence=0.85 if category != "Other" else 0.6,
        )
    
    return None


async def extract_receipt_data(image_bytes: bytes) -> ReceiptData:
    """
    Extract expense data from a receipt image using Gemini Vision.
    
    Args:
        image_bytes: Raw bytes of the receipt image
    
    Returns:
        ReceiptData with merchant, amount, items, date, category
    """
    try:
        client = _get_client()
        
        # Load and validate image
        image = Image.open(io.BytesIO(image_bytes))
        
        prompt = RECEIPT_OCR_PROMPT.format(categories=", ".join(DEFAULT_CATEGORIES))
        
        response = client.models.generate_content(
            model=settings.AI_MODEL,
            contents=[prompt, image],
            config=types.GenerateContentConfig(
                temperature=0.1,
                max_output_tokens=500,
            ),
        )
        
        result = _parse_json_response(response.text)
        
        return ReceiptData(
            merchant=result.get("merchant"),
            amount=float(result.get("amount")) if result.get("amount") else None,
            items=result.get("items", []),
            date=result.get("date"),
            category=result.get("category", "Other"),
            confidence=float(result.get("confidence", 0.5)),
        )
        
    except Exception as e:
        logger.error(f"Receipt OCR failed: {e}")
        return ReceiptData(
            merchant=None,
            amount=None,
            items=[],
            date=None,
            category="Other",
            confidence=0.0,
        )


async def suggest_category(description: str, amount: float | None = None) -> tuple[str, float]:
    """
    Suggest a category for an expense based on description.
    
    Returns:
        Tuple of (category_name, confidence_score)
    """
    result = await parse_expense_text(description)
    return result["category"], result["confidence"]

# Health check for AI service
def is_ai_configured() -> bool:
    """Check if AI service is properly configured."""
    return bool(settings.GEMINI_API_KEY)
