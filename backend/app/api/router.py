from fastapi import APIRouter

from app.api.routes import auth, expenses, categories, whatsapp, education, gamification

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(expenses.router, prefix="/expenses", tags=["Expenses"])
api_router.include_router(categories.router, prefix="/categories", tags=["Categories"])
api_router.include_router(whatsapp.router, prefix="/whatsapp", tags=["WhatsApp"])
api_router.include_router(education.router, prefix="/education", tags=["Education"])
api_router.include_router(gamification.router, prefix="/gamification", tags=["Gamification"])
