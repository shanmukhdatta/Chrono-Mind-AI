# ChronoMind AI 🧠⏰

**AI-Powered Day Planner for College Students**  
Built with FastAPI · LangGraph · Groq · React · Firebase

## Live Deployments 🚀
- **Frontend App:** [https://chronomind-ai.vercel.app](https://chronomind-ai.vercel.app) *(Update with your Vercel URL)*
- **Backend API Docs:** [https://chronomind-backend.onrender.com/docs](https://chronomind-backend.onrender.com/docs) *(Update with your Render URL)*

---

## Quick Start

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Setup env
cp .env.example .env
# Fill in GROQ_API_KEY, FIREBASE_SERVICE_ACCOUNT_PATH

uvicorn main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install

cp .env.example .env
# Fill in all VITE_FIREBASE_* values and VITE_API_URL

npm run dev
```

---

## Architecture

```
Frontend (React + Vite + Tailwind)
  ├── Pages: Landing, Dashboard, Calendar, Assistant, Profile
  ├── Stores: Zustand (auth, tasks, assistant, timer, notifications, ui)
  ├── Hooks: useAuth, useTasks, useAssistant, useNotifications
  └── Components: TaskCard, AddTaskForm, AssistantPanel, CalendarDay/Week/Month, FocusTimer, ClockWidget

Backend (FastAPI)
  ├── Routers: /api/tasks, /api/assistant/chat, /api/profile, /api/timetable
  ├── Middleware: Firebase ID token auth
  ├── Services: groq_service, task_service, firebase_service, notification_service
  ├── Agents: LangGraph rescheduler (7-node graph)
  └── Scheduler: APScheduler — nightly 23:55 IST
```

## Firebase Setup

1. Go to Firebase Console → Create project
2. Enable **Authentication** → Google Sign-In
3. Enable **Firestore Database** (production mode)
4. Create Firestore indexes (required):
   - Collection: `tasks` → fields: `uid ASC, date ASC, start_time ASC`
   - Collection: `tasks` → fields: `uid ASC, date ASC, completed ASC`
5. Download service account JSON → set `FIREBASE_SERVICE_ACCOUNT_PATH`
6. Copy Firebase web config → fill `VITE_FIREBASE_*` in frontend `.env`

## Features

- ✅ Google Sign-In (Firebase Auth)
- ✅ Add/Edit/Delete tasks with time slots
- ✅ Task priority (Important = auto-rescheduled, Optional = auto-deleted)
- ✅ Recurring tasks (daily, weekly, custom days)
- ✅ Focus timer per task
- ✅ AI scheduling assistant (Groq LLaMA 3.3-70B)
- ✅ Voice input (Web Speech API, en-IN)
- ✅ Calendar views: Day (timeline) / Week / Month
- ✅ LangGraph nightly reschedule agent (23:55 IST)
- ✅ Notifications for rescheduled/deleted tasks
- ✅ Completion rate + streak stats
- ✅ Mobile-responsive layout
- 🔜 Timetable OCR import (Phase 2)

## Built By

**Datta** · Nerds Room · NIT Jalandhar · Batch 2024–2028
