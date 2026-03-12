"""Expense routes - CRUD, summary, and AI-powered endpoints."""

from datetime import date
from typing import Literal

from fastapi import APIRouter, HTTPException, Query, UploadFile, File, status

from app.api.deps import CurrentUserId, DbSession
from app.schemas.expense import (
    ExpenseCreate,
    ExpenseUpdate,
    ExpenseResponse,
    ExpenseSummary,
    CategoryResponse,
)
from app.schemas.ai import (
    ParseExpenseRequest,
    ParsedExpenseResponse,
    ReceiptUploadResponse,
    SmartExpenseCreate,
    AIStatusResponse,
)
from app.services import expense_service
from app.core import ai_service
from app.core.config import get_settings

settings = get_settings()
router = APIRouter()


@router.post("/", response_model=ExpenseResponse, status_code=status.HTTP_201_CREATED)
async def create_expense(
    data: ExpenseCreate,
    db: DbSession,
    user_id: CurrentUserId,
):
    """Create a new expense entry."""
    expense = await expense_service.create_expense(db, user_id, data)
    return _expense_to_response(expense)


@router.get("/", response_model=list[ExpenseResponse])
async def list_expenses(
    db: DbSession,
    user_id: CurrentUserId,
    start_date: date | None = Query(None, description="Filter from date"),
    end_date: date | None = Query(None, description="Filter to date"),
    category_id: int | None = Query(None, description="Filter by category"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    """List expenses with filters (date range, category, etc.)."""
    expenses = await expense_service.list_expenses(
        db, user_id, start_date, end_date, category_id, limit, offset
    )
    return [_expense_to_response(e) for e in expenses]


@router.get("/summary", response_model=ExpenseSummary)
async def expense_summary(
    db: DbSession,
    user_id: CurrentUserId,
    period: Literal["daily", "weekly", "monthly"] = Query("monthly"),
    target_date: date | None = Query(None, description="Date within target period"),
):
    """Get expense summary (daily/weekly/monthly aggregations)."""
    summary = await expense_service.get_expense_summary(db, user_id, period, target_date)
    return summary


@router.get("/categories", response_model=list[CategoryResponse])
async def list_categories(
    db: DbSession,
    user_id: CurrentUserId,
):
    """Get all available categories (system + user custom)."""
    categories = await expense_service.get_all_categories(db, user_id)
    return [
        CategoryResponse(
            id=c.id,
            name=c.name,
            icon=c.icon,
            color=c.color,
            is_custom=c.is_custom,
        )
        for c in categories
    ]


@router.get("/{expense_id}", response_model=ExpenseResponse)
async def get_expense(
    expense_id: int,
    db: DbSession,
    user_id: CurrentUserId,
):
    """Get a single expense by ID."""
    expense = await expense_service.get_expense_by_id(db, expense_id, user_id)
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    return _expense_to_response(expense)


@router.put("/{expense_id}", response_model=ExpenseResponse)
async def update_expense(
    expense_id: int,
    data: ExpenseUpdate,
    db: DbSession,
    user_id: CurrentUserId,
):
    """Update an expense entry."""
    expense = await expense_service.update_expense(db, expense_id, user_id, data)
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    return _expense_to_response(expense)


@router.delete("/{expense_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_expense(
    expense_id: int,
    db: DbSession,
    user_id: CurrentUserId,
):
    """Soft-delete an expense entry."""
    deleted = await expense_service.delete_expense(db, expense_id, user_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Expense not found")
    return None


def _expense_to_response(expense) -> ExpenseResponse:
    """Convert Expense model to response schema."""
    return ExpenseResponse(
        id=expense.id,
        amount=float(expense.amount),
        currency=expense.currency,
        description=expense.description,
        expense_date=expense.expense_date,
        category_id=expense.category_id,
        category_name=expense.category.name if expense.category else None,
        category_icon=expense.category.icon if expense.category else None,
        source=expense.source.value,
        created_at=expense.created_at.isoformat(),
    )


async def _find_category_id(db: DbSession, user_id, category_name: str) -> int | None:
    """Find category ID by name."""
    categories = await expense_service.get_all_categories(db, user_id)
    for cat in categories:
        if cat.name.lower() == category_name.lower():
            return cat.id
    return None


# ============== AI-Powered Endpoints ==============

@router.get("/ai/status", response_model=AIStatusResponse)
async def ai_status():
    """Check if AI features are available."""
    return AIStatusResponse(
        configured=ai_service.is_ai_configured(),
        model=settings.AI_MODEL,
        features=["parse_text", "receipt_ocr", "smart_create"] if ai_service.is_ai_configured() else [],
    )


@router.post("/ai/parse", response_model=ParsedExpenseResponse)
async def parse_expense_text(
    data: ParseExpenseRequest,
    db: DbSession,
    user_id: CurrentUserId,
):
    """
    Parse natural language expense into structured data.
    
    Examples:
    - "bought suya 2k" → {amount: 2000, category: "Food & Groceries", ...}
    - "uber to VI 3500" → {amount: 3500, category: "Transport", ...}
    """
    if not ai_service.is_ai_configured():
        raise HTTPException(
            status_code=503,
            detail="AI service not configured. Set GEMINI_API_KEY in environment."
        )
    
    result = await ai_service.parse_expense_text(data.text)
    
    # Find matching category ID
    category_id = await _find_category_id(db, user_id, result["category"])
    
    return ParsedExpenseResponse(
        amount=result["amount"],
        description=result["description"],
        category=result["category"],
        category_id=category_id,
        confidence=result["confidence"],
    )


@router.post("/ai/receipt", response_model=ReceiptUploadResponse)
async def scan_receipt(
    db: DbSession,
    user_id: CurrentUserId,
    file: UploadFile = File(..., description="Receipt image (JPEG/PNG)"),
):
    """
    Extract expense data from a receipt image using AI OCR.
    
    Accepts JPEG or PNG images. Returns extracted merchant, amount, items, date.
    """
    if not ai_service.is_ai_configured():
        raise HTTPException(
            status_code=503,
            detail="AI service not configured. Set GEMINI_API_KEY in environment."
        )
    
    # Validate file type
    if file.content_type not in ["image/jpeg", "image/png", "image/webp"]:
        raise HTTPException(
            status_code=400,
            detail="Invalid file type. Only JPEG, PNG, and WebP images are supported."
        )
    
    # Read image bytes
    image_bytes = await file.read()
    
    # Limit file size (5MB)
    if len(image_bytes) > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large. Maximum size is 5MB.")
    
    result = await ai_service.extract_receipt_data(image_bytes)
    
    # Find matching category ID
    category_id = await _find_category_id(db, user_id, result["category"])
    
    return ReceiptUploadResponse(
        merchant=result["merchant"],
        amount=result["amount"],
        items=result["items"],
        date=result["date"],
        category=result["category"],
        category_id=category_id,
        confidence=result["confidence"],
    )


@router.post("/ai/smart", response_model=ExpenseResponse, status_code=status.HTTP_201_CREATED)
async def smart_create_expense(
    data: SmartExpenseCreate,
    db: DbSession,
    user_id: CurrentUserId,
):
    """
    Create expense with AI assistance.
    
    If `use_ai=true` and `text` is provided, AI will parse the text to extract
    amount, description, and category. Manual overrides take precedence.
    """
    amount = data.amount
    description = data.description
    category_id = data.category_id
    expense_date_str = data.expense_date
    
    # Use AI to parse text if enabled
    if data.use_ai and data.text and ai_service.is_ai_configured():
        parsed = await ai_service.parse_expense_text(data.text)
        
        # Use AI results if manual values not provided
        if amount is None:
            amount = parsed["amount"]
        if description is None:
            description = parsed["description"]
        if category_id is None:
            category_id = await _find_category_id(db, user_id, parsed["category"])
    
    # Validate we have required fields
    if amount is None:
        raise HTTPException(
            status_code=400,
            detail="Could not determine amount. Please specify amount manually."
        )
    
    # Parse date
    from datetime import date as date_type
    if expense_date_str:
        expense_date = date_type.fromisoformat(expense_date_str)
    else:
        expense_date = date_type.today()
    
    # Create expense
    expense_data = ExpenseCreate(
        amount=amount,
        description=description,
        category_id=category_id,
        expense_date=expense_date,
    )
    
    expense = await expense_service.create_expense(db, user_id, expense_data)
    return _expense_to_response(expense)
