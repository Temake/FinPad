# FinPad 💵

**Personal Finance Tracker with WhatsApp Integration**

Track your daily spending, build smart money habits, and receive financial tips — via a clean web dashboard or WhatsApp.

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| **Backend** | FastAPI, SQLAlchemy, Alembic, PostgreSQL |
| **Frontend** | React, TypeScript, Vite, TailwindCSS |
| **WhatsApp** | Evolution API (self-hosted) |
| **Cache** | Redis |
| **Auth** | JWT + WhatsApp OTP |

## Getting Started

### Prerequisites

- Python 3.12+
- Node.js 18+
- Docker & Docker Compose
- Git

### 1. Clone & Setup

```bash
git clone <repo-url>
cd FinPad
cp .env.example .env
```

### 2. Start Infrastructure

```bash
docker-compose up -d
```

This starts PostgreSQL, Redis, and Evolution API.

### Evolution API quick notes

- Open Manager at `http://localhost:8080/manager`
- Use the same API key configured in `EVOLUTION_API_KEY` (default: `change-me`)
- Create/connect an instance and set your backend `EVOLUTION_INSTANCE` to that exact instance name
- If Manager shows disconnected or QR does not render, run `docker compose pull evolution-api && docker compose up -d evolution-api`

### 3. Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate      # Windows
# source .venv/bin/activate  # macOS/Linux

pip install -r requirements.txt

# Run database migrations
alembic upgrade head

# Start dev server
uvicorn app.main:app --reload --port 8000
```

API docs available at: http://localhost:8000/docs

### 4. Frontend

```bash
cd frontend
npm install
npm run dev
```

App available at: http://localhost:5173

---

## Project Structure

```
FinPad/
├── backend/
│   ├── app/
│   │   ├── api/routes/      # API endpoints
│   │   ├── core/            # Config, DB, security
│   │   ├── models/          # SQLAlchemy models
│   │   ├── schemas/         # Pydantic schemas
│   │   ├── services/        # Business logic
│   │   └── main.py          # FastAPI app
│   ├── alembic/             # DB migrations
│   ├── tests/
│   └── requirements.txt
│
├── frontend/
│   ├── src/
│   │   ├── components/      # Shared UI components
│   │   ├── pages/           # Route pages
│   │   ├── hooks/           # React Query hooks
│   │   ├── services/        # API client
│   │   └── App.tsx
│   └── package.json
│
├── docker-compose.yml
├── .env.example
└── plan.md
```

---

## Development Phases

- [x] **Phase 1**: Project foundation (backend + frontend skeleton)
- [ ] **Phase 2**: Authentication (WhatsApp OTP + JWT)
- [ ] **Phase 3**: Core expense tracking (CRUD + dashboard)
- [ ] **Phase 4**: AI-powered categorization & receipt scanning
- [ ] **Phase 5**: WhatsApp chatbot integration
- [ ] **Phase 6**: Bank integration (Mono.co / Okra)
- [ ] **Phase 7**: Financial education & gamification
- [ ] **Phase 8**: Advanced features (budgets, savings goals, exports)

## License

Private - All rights reserved.
