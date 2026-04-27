# Plan: FinPad - Personal Finance Tracker with WhatsApp Integration

**TL;DR**: Build a dual-interface personal finance app where users can log expenses, receive smart notifications, and learn financial habits via both a React web dashboard and WhatsApp chatbot (Evolution API). Backend powered by FastAPI with AI-powered categorization, receipt scanning, and Nigerian bank integration. Focus on NGN currency with gamification to drive engagement.

---

## Architecture Overview

```
┌─────────────────┐     ┌─────────────────┐
│   React Web     │     │    WhatsApp     │
│   Dashboard     │     │   (Evolution)   │
└────────┬────────┘     └────────┬────────┘
         │                       │
         ▼                       ▼
┌─────────────────────────────────────────┐
│           FastAPI Backend               │
│  ┌─────────┬─────────┬────────────────┐ │
│  │ Auth    │ Expense │ AI/ML Service  │ │
│  │ Service │ Service │ (Categorize)   │ │
│  └─────────┴─────────┴────────────────┘ │
└─────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────┐
│   PostgreSQL   │   Redis   │   S3/Blob │
│   (Data)       │  (Cache)  │  (Images) │
└─────────────────────────────────────────┘
```

---

## Phase 1: Project Foundation

### 1. Initialize monorepo structure
- `/backend` - FastAPI application
- `/frontend` - React TypeScript (Vite)
- `/shared` - Common types/schemas
- `/docs` - API documentation, user guides

### 2. Set up FastAPI backend skeleton
- Configure SQLAlchemy + Alembic for PostgreSQL
- Set up Pydantic models for request/response validation
- Configure environment-based settings (dev/staging/prod)
- Add Redis for caching and rate limiting

### 3. Set up React frontend skeleton
- Vite + React + TypeScript
- TailwindCSS for styling
- React Query for API state management
- React Router for navigation

---

## Phase 2: Authentication System

### 4. WhatsApp Registration (No OTP Required)
- User messages bot → Bot detects new user via phone number
- Bot asks for confirmation: "Reply YES to create account"
- User confirms → Account created, linked to WhatsApp ID
- **No OTP needed** - WhatsApp already verifies phone ownership

### 5. Web App Authentication (OTP Required)
- User enters phone number on web
- **Primary**: Send OTP via WhatsApp (FREE via Evolution API)
- **Fallback**: Send OTP via SMS (Termii, ~₦4/message) if no WhatsApp
- User enters OTP → JWT token issued

### 6. Account Linking (OTP Required)
- Existing web user wants to link WhatsApp
- Or existing WhatsApp user wants web access
- OTP sent to verify ownership of both channels

### 7. User profile management
- Display name, profile picture (optional)
- Notification preferences
- Currency settings (default NGN)
- WhatsApp linking status

### Authentication Flow Summary

| Entry Point | OTP Required? | Method |
|-------------|---------------|--------|
| WhatsApp first-time | ❌ No | Simple YES confirmation |
| Web app login | ✅ Yes | WhatsApp OTP (free) → SMS fallback (paid) |
| Link accounts | ✅ Yes | OTP to verify ownership |
| Sensitive actions | ✅ Yes | OTP for security |

## Phase 3: Core Expense Tracking

### 6. Expense data model
```
expenses:
- id, user_id, amount, currency (NGN)
- category_id, description, date
- source (manual/whatsapp/bank_sync)
- receipt_url (optional)
- created_at, updated_at

categories:
- id, name, icon, color, is_custom
- user_id (null for defaults)
```

### 7. Expense CRUD API
- `POST /expenses` - Create expense (manual or AI-assisted)
- `GET /expenses` - List with filters (date range, category)
- `PUT /expenses/{id}` - Update
- `DELETE /expenses/{id}` - Soft delete
- `GET /expenses/summary` - Daily/weekly/monthly aggregations

### 8. Pre-defined categories (Nigeria-relevant)
- Food & Groceries, Transport (fuel, rides), Airtime/Data
- Bills & Utilities, Shopping, Entertainment
- Health, Education, Family/Gifts, Savings

### 9. Web dashboard - Expense UI
- Quick-add expense modal
- Transaction list with infinite scroll
- Category pie chart, spending trends graph
- Monthly budget progress bar

---

## Phase 4: AI-Powered Features

### 10. Auto-categorization service
- Use OpenAI/local LLM to parse descriptions
- Example: "Bought suya 2k" → Food & Groceries, ₦2,000
- Confidence threshold - auto-apply or suggest
- Learn from user corrections

### 11. Receipt scanning (OCR)
- Integrate Tesseract or Cloud Vision API
- Extract: merchant name, amount, date, items
- Store receipt image in S3-compatible storage
- Surface extracted data for user confirmation

---

## Phase 5: WhatsApp Integration

### 12. Evolution API setup
- Self-host Evolution API instance
- Configure webhook endpoint in FastAPI
- Handle: text messages, images (receipts), voice notes

### 13. WhatsApp conversation flows
- **Log expense**: "Spent 5000 on transport" → parsed & logged
- **View summary**: "How much did I spend today?" → returns summary
- **Set reminder**: "Remind me to log expenses at 8pm"
- **Quick actions**: Buttons for common categories

### 14. Notification system
- Daily reminder: "Don't forget to log today's expenses! 📝"
- Weekly summary: "You spent ₦45,000 this week. Top: Food (₦18k)"
- Achievement unlocked: "🔥 7-day streak! Keep it up!"
- Configurable quiet hours

---

## Phase 6: Bank Integration (MVP)

### 15. Mono.co / Okra integration
- Connect Nigerian bank accounts
- Fetch transaction history
- Auto-import transactions with category suggestions
- Re-auth flow for expired tokens

---

## Phase 7: Financial Education & Gamification

### 16. Micro-tips system
- Database of 100+ short financial tips
- Delivered via WhatsApp daily at preferred time
- Categories: savings, budgeting, investing basics, debt management
- "Did You Know?" format for engagement

### 17. Gamification engine
- **Streaks**: Consecutive days logging expenses
- **Badges**: First expense, 7-day streak, first budget, etc.
- **Levels**: Beginner Saver → Pro Budgeter → Finance Master
- **Leaderboard** (optional): Anonymized savings challenges

### 18. Badges data model
```
badges:
- id, name, description, icon, criteria_type

user_badges:
- user_id, badge_id, earned_at

user_stats:
- user_id, current_streak, longest_streak, total_expenses_logged
```

---

## Phase 8: Advanced Features (Post-MVP)

### 19. Budget setting
- Set monthly limits per category
- Alert when approaching/exceeding budget
- Rollover unused budget (optional)

### 20. Savings goals
- Target: "Save ₦100,000 for laptop"
- Track progress, auto-calculate timeline
- Celebrate milestones

### 21. Export & reports
- Download CSV/PDF of transactions
- Monthly email summary (optional)

---

## Folder Structure

```
FinPad/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── routes/
│   │   │   │   ├── auth.py
│   │   │   │   ├── expenses.py
│   │   │   │   ├── categories.py
│   │   │   │   ├── whatsapp.py
│   │   │   │   ├── education.py
│   │   │   │   └── gamification.py
│   │   │   └── deps.py
│   │   ├── core/
│   │   │   ├── config.py
│   │   │   ├── security.py
│   │   │   └── ai_service.py
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── services/
│   │   │   ├── sms_service.py
│   │   │   ├── whatsapp_service.py
│   │   │   ├── ocr_service.py
│   │   │   └── bank_service.py
│   │   └── main.py
│   ├── alembic/
│   ├── tests/
│   └── requirements.txt
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   │   ├── Dashboard.tsx
│   │   │   ├── Expenses.tsx
│   │   │   ├── Education.tsx
│   │   │   └── Profile.tsx
│   │   ├── hooks/
│   │   ├── services/
│   │   └── App.tsx
│   ├── public/
│   └── package.json
│
├── docker-compose.yml
├── .env.example
└── README.md
```

---

## Verification

- **Backend**: Run `pytest` for API tests, test WhatsApp webhook with Evolution API sandbox
- **Frontend**: Run with `npm run dev`, test on mobile viewport
- **Integration**: End-to-end flow - send WhatsApp message → verify logged in web dashboard
- **Manual checks**: OTP delivery, receipt parsing accuracy, notification timing

---

## Key Decisions

- **Evolution API** over official WhatsApp Business API for MVP flexibility and cost
- **Phone-only auth** for simplicity and WhatsApp linking
- **Mono.co/Okra** for Nigerian bank integration (high coverage)
- **PostgreSQL + Redis** for reliability and caching
- **Gamification first** over complex investment features to drive retention
