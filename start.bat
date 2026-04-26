@echo off
echo.
echo  ChronoMind AI -- Starting up...
echo.

:: Backend
cd backend
if not exist ".env" (
  copy .env.example .env
  echo  Created backend\.env -- add your GROQ_API_KEY before using AI features
)
if not exist "venv" (
  echo  Creating Python virtual environment...
  python -m venv venv
)
call venv\Scripts\activate
pip install -r requirements.txt -q
echo  Starting FastAPI backend on http://localhost:8000
start /B uvicorn app.main:app --reload --port 8000
cd ..

:: Frontend
cd frontend
if not exist "node_modules" (
  echo  Installing npm packages...
  npm install
)
echo  Starting React frontend on http://localhost:5173
start /B npm run dev
cd ..

echo.
echo  ChronoMind AI is running!
echo    Frontend: http://localhost:5173
echo    Backend:  http://localhost:8000
echo    API Docs: http://localhost:8000/docs
echo.
pause
