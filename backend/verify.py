"""
ChronoMind AI — Startup Verification Script
Run: python verify.py
Checks all imports and config before starting the server.
"""
import sys

print("ChronoMind AI — Verification\n" + "=" * 40)

errors = []
warnings = []

# Check Python version
if sys.version_info < (3, 10):
    errors.append(f"Python 3.10+ required, got {sys.version}")
else:
    print(f"✅ Python {sys.version.split()[0]}")

# Check core imports
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
        print(f"✅ {name}")
    except ImportError:
        errors.append(f"MISSING: {name} — run: pip install -r requirements.txt")

# Check pytesseract
try:
    import pytesseract
    version = pytesseract.get_tesseract_version()
    print(f"✅ pytesseract (tesseract {version})")
except ImportError:
    warnings.append("pytesseract not installed — OCR will use fallback demo data")
    print(f"⚠️  pytesseract not installed")
except Exception as e:
    warnings.append(f"tesseract-ocr system binary not found — OCR will use demo data. Install from: https://github.com/UB-Mannheim/tesseract/wiki")
    print(f"⚠️  tesseract binary not found (OCR will still work with demo data)")

# Check .env
import os
from pathlib import Path

env_file = Path(".env")
if not env_file.exists():
    errors.append(".env file missing — copy .env.example to .env")
    print("❌ .env file missing")
else:
    print("✅ .env file found")

# Check GROQ key
groq_key = os.getenv("GROQ_API_KEY", "")
if not groq_key or groq_key == "your-groq-api-key-here":
    warnings.append("GROQ_API_KEY not set — AI chat will return a setup message instead of working. Get free key at https://console.groq.com/keys")
    print("⚠️  GROQ_API_KEY not configured (AI features disabled)")
else:
    print(f"✅ GROQ_API_KEY configured ({groq_key[:8]}...)")

# Summary
print("\n" + "=" * 40)
if errors:
    print(f"\n❌ {len(errors)} ERROR(S) — fix before starting:\n")
    for e in errors:
        print(f"   → {e}")
    sys.exit(1)

if warnings:
    print(f"\n⚠️  {len(warnings)} WARNING(S) — app will run but some features limited:\n")
    for w in warnings:
        print(f"   → {w}")

print("\n✅ Ready to start! Run: uvicorn app.main:app --reload --port 8000\n")
