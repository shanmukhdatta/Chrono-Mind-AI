# ⏱ ChronoMind AI — Plan Smarter. Live Fuller.
An AI-powered day planner for college students. OCR timetable import, LangGraph agentic scheduling, voice input, and a glassmorphic 24-hour calendar.

---

## 🏗 Project Structure

```
chronomind/
├── backend/               # FastAPI + LangGraph AI backend
│   ├── app/
│   │   ├── agents/        # LangGraph scheduling agent
│   │   ├── api/           # Route handlers
│   │   ├── models/        # SQLAlchemy models + Pydantic schemas
│   │   ├── services/      # OCR, auth, scheduler logic
│   │   └── utils/         # FastAPI dependencies
│   ├── main.py            # Entry point (run this)
│   ├── requirements.txt
│   └── .env.example
└── frontend/              # React + Vite + Framer Motion
    ├── src/
    │   ├── components/
    │   │   ├── ui/        # Design system components
    │   │   ├── layout/    # Navbar, Sidebar
    │   │   └── pages/     # Landing, Dashboard, Calendar, etc.
    │   ├── store.js       # Zustand global state
    │   ├── api.js         # Axios client
    │   └── App.jsx        # Router
    ├── package.json
    └── vite.config.js
```

---

## ⚡ Quick Start (5 minutes)

### Prerequisites
- Python 3.10+
- Node.js 18+
- A free **Groq API key** → https://console.groq.com

### Tesseract OCR (for timetable image upload)
- **Windows:** Download installer from https://github.com/UB-Mannheim/tesseract/wiki
  Then add to PATH: `C:\Program Files\Tesseract-OCR`
- **Mac:** `brew install tesseract`
- **Linux/Ubuntu:** `sudo apt-get install tesseract-ocr`
- **Note:** If tesseract is not installed, the app still runs — timetable upload
  will skip OCR and return demo data. You can still enter your timetable manually.

---

### 1. Backend Setup

```bash
cd chronomind/backend

# Copy env file and fill in your keys
cp .env.example .env
# Edit .env — add your GROQ_API_KEY (required)

# Create virtual environment
python -m venv venv

# Activate it
# Mac/Linux:
source venv/bin/activate
# Windows:
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start the server
uvicorn app.main:app --reload --port 8000
```

Backend runs at: http://localhost:8000
API docs at: http://localhost:8000/docs

---

### 2. Frontend Setup

```bash
cd chronomind/frontend

# Install dependencies
npm install

# Start the dev server
npm run dev
```

Frontend runs at: http://localhost:5173

---

### 3. Try the Demo

1. Open http://localhost:5173
2. Click **"Try Demo Free"** — no sign up needed
3. Explore the Dashboard, Calendar, and AI Assistant

---

## 🔑 Environment Variables

Edit `backend/.env`:

```env
# Required
GROQ_API_KEY=your-groq-api-key-here

# Optional — for Google OAuth login
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret

# Auto-generated on first run
SECRET_KEY=change-this-in-production
```

Get a free Groq API key at: https://console.groq.com/keys

---

## 🧠 AI Features

### LangGraph Agent
The scheduling agent has 3 nodes:
1. **parse_intent** — LLM understands what the user wants
2. **execute_tools** — calls scheduling tools (find_slot, create_task, etc.)
3. **synthesize** — generates a friendly confirmation message

### Tools available to the agent
| Tool | Description |
|------|-------------|
| `schedule_task` | Find best free slot and create a task |
| `find_slots` | List available time slots for a day |
| `list_tasks` | Show tasks for today/tomorrow |
| `complete_task` | Mark a task as done |

### LLM Models (via Groq)
- **Primary**: `llama-3.3-70b-versatile` (agent reasoning)
- **OCR parsing**: `llama-3.1-8b-instant` (fast, cheap)

---

## 🎨 Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 18 + Vite + Framer Motion |
| Styling | Tailwind CSS + Glassmorphism |
| State | Zustand |
| Backend | FastAPI (async) |
| AI Agent | LangGraph + LangChain |
| LLM | Groq (Llama 3.3 70B) |
| OCR | PaddleOCR + Groq LLM parsing |
| Database | SQLite (dev) → PostgreSQL (prod) |
| Auth | JWT + Google OAuth 2.0 |

---

## 📱 Pages

| Route | Description |
|-------|-------------|
| `/` | Landing page — Apple-style scroll |
| `/login` | Email + demo login |
| `/register` | Create account |
| `/onboarding` | 3-step timetable upload wizard |
| `/dashboard` | Stats, today's tasks, progress ring |
| `/calendar` | 24-hour horizontal timeline |
| `/assistant` | AI chat + voice input |
| `/profile` | Settings + preferences |

---

## 🚀 Production Deployment

### Backend (Render.com)
1. Push to GitHub
2. New Web Service → connect repo → `backend/` directory
3. Build command: `pip install -r requirements.txt`
4. Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
5. Add env vars in Render dashboard

### Frontend (Vercel)
1. Connect repo → `frontend/` directory
2. Framework: Vite
3. Add env var: `VITE_API_URL=https://your-backend.onrender.com`
4. Update `vite.config.js` proxy to use env var

---

## 🐛 Common Issues

**PaddleOCR install fails**
```bash
pip install paddlepaddle paddleocr
# If still failing, the app will use the Groq LLM fallback automatically
```

**Port 8000 in use**
```bash
uvicorn app.main:app --reload --port 8001
# Then update frontend/vite.config.js proxy target
```

**"Demo login failed"**
- Make sure backend is running on port 8000
- Check that `.env` file exists in `backend/`

---

## 📄 License

MIT © 2026 ChronoMind AI
