#!/usr/bin/env bash
# ChronoMind AI — One-command startup
# Usage: bash start.sh

set -e

echo ""
echo "⏱  ChronoMind AI — Starting up..."
echo ""

# ─── Backend ──────────────────────────────────────────────────────
echo "📦 Setting up backend..."
cd backend

if [ ! -f ".env" ]; then
  cp .env.example .env
  echo "⚠️  Created backend/.env — add your GROQ_API_KEY before using AI features"
fi

if [ ! -d "venv" ]; then
  echo "🐍 Creating Python virtual environment..."
  python3 -m venv venv
fi

source venv/bin/activate
pip install -r requirements.txt -q

echo "🚀 Starting FastAPI backend on http://localhost:8000"
uvicorn app.main:app --reload --port 8000 &
BACKEND_PID=$!

cd ..

# ─── Frontend ─────────────────────────────────────────────────────
echo "📦 Setting up frontend..."
cd frontend

if [ ! -d "node_modules" ]; then
  echo "📥 Installing npm packages..."
  npm install
fi

echo "🎨 Starting React frontend on http://localhost:5173"
npm run dev &
FRONTEND_PID=$!

cd ..

echo ""
echo "✅ ChronoMind AI is running!"
echo "   Frontend: http://localhost:5173"
echo "   Backend:  http://localhost:8000"
echo "   API Docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop both servers"

# Wait for both
wait $BACKEND_PID $FRONTEND_PID
