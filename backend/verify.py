"""
ChronoMind AI - Startup Verification Script
Run: python verify.py
Checks imports and configuration before starting the server.
"""
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


def ok(message: str) -> None:
    print(f"[OK] {message}")


def warn(message: str) -> None:
    print(f"[WARN] {message}")


def err(message: str) -> None:
    print(f"[ERROR] {message}")


print("ChronoMind AI - Verification\n" + "=" * 40)

errors = []
warnings = []

if sys.version_info < (3, 10):
    errors.append(f"Python 3.10+ required, got {sys.version}")
else:
    ok(f"Python {sys.version.split()[0]}")

imports = [
    ("fastapi", "FastAPI"),
    ("uvicorn", "Uvicorn"),
    ("sqlalchemy", "SQLAlchemy"),
    ("aiosqlite", "aiosqlite"),
    ("pydantic", "Pydantic"),
    ("jose", "python-jose"),
    ("passlib", "passlib"),
    ("langchain", "LangChain"),
    ("langchain_groq", "LangChain-Groq"),
    ("langgraph", "LangGraph"),
    ("PIL", "Pillow"),
]

for module, name in imports:
    try:
        __import__(module)
        ok(name)
    except ImportError:
        errors.append(f"MISSING: {name} - run: pip install -r requirements.txt")

try:
    import pytesseract

    version = pytesseract.get_tesseract_version()
    ok(f"pytesseract (tesseract {version})")
except ImportError:
    warnings.append("pytesseract not installed - OCR will use fallback demo data")
    warn("pytesseract not installed")
except Exception:
    warnings.append(
        "tesseract-ocr system binary not found - OCR will use demo data. "
        "Install from: https://github.com/UB-Mannheim/tesseract/wiki"
    )
    warn("tesseract binary not found (OCR will still work with demo data)")

env_file = Path(".env")
if not env_file.exists():
    errors.append(".env file missing - copy .env.example to .env")
    err(".env file missing")
else:
    ok(".env file found")

groq_key = os.getenv("GROQ_API_KEY", "")
if not groq_key or groq_key == "your-groq-api-key-here":
    warnings.append(
        "GROQ_API_KEY not set - AI chat will return a setup message instead of working. "
        "Get a free key at https://console.groq.com/keys"
    )
    warn("GROQ_API_KEY not configured (AI features disabled)")
else:
    ok(f"GROQ_API_KEY configured ({groq_key[:8]}...)")

print("\n" + "=" * 40)
if errors:
    err(f"{len(errors)} ERROR(S) - fix before starting:\n")
    for item in errors:
        print(f"   -> {item}")
    sys.exit(1)

if warnings:
    warn(f"{len(warnings)} WARNING(S) - app will run but some features limited:\n")
    for item in warnings:
        print(f"   -> {item}")

ok("Ready to start! Run: uvicorn app.main:app --reload --port 8000")
