"""
ChronoMind AI — OCR Service (CPU-safe, pytesseract-based)
"""
import io
import json
import logging
from PIL import Image

from app.config import settings

logger = logging.getLogger(__name__)

TIMETABLE_PROMPT = """You are an expert at reading college timetable images.

The following is raw OCR text extracted from a timetable image. Parse it into structured JSON.

OCR TEXT:
{ocr_text}

Return ONLY valid JSON (no markdown, no explanation):
{{
  "timetable": {{
    "Monday": [
      {{"start": "09:00", "end": "10:00", "subject": "Mathematics", "location": "Room 101"}}
    ],
    "Tuesday": [],
    "Wednesday": [],
    "Thursday": [],
    "Friday": [],
    "Saturday": [],
    "Sunday": []
  }},
  "confidence": 0.85
}}

Rules:
- Times in 24-hour HH:MM format
- Empty array [] for days with no classes
- Capitalize subject names properly
- location is optional, use null if not found
- confidence: 0.0–1.0 based on OCR clarity
"""


async def extract_timetable_from_image(image_bytes: bytes, filename: str) -> dict:
    """Main OCR pipeline: pytesseract → Groq LLM parsing → JSON."""
    ocr_text = _run_tesseract(image_bytes)

    if not settings.GROQ_API_KEY:
        logger.warning("GROQ_API_KEY not set — returning demo timetable")
        return _demo_timetable()

    try:
        result = await _parse_with_llm(ocr_text)
        return result
    except Exception as e:
        logger.error(f"LLM parsing failed: {e}")
        return _demo_timetable()


def _run_tesseract(image_bytes: bytes) -> str:
    """Extract text from image using pytesseract (CPU, no GPU needed)."""
    try:
        import pytesseract
        img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        text = pytesseract.image_to_string(img, lang="eng")
        if not text.strip():
            return "No readable text found in image."
        return text.strip()
    except ImportError:
        logger.warning("pytesseract not installed — using fallback")
        return _pillow_fallback(image_bytes)
    except Exception as e:
        logger.warning(f"Tesseract failed: {e} — using fallback")
        return _pillow_fallback(image_bytes)


def _pillow_fallback(image_bytes: bytes) -> str:
    """If tesseract is unavailable, return image metadata as context."""
    try:
        img = Image.open(io.BytesIO(image_bytes))
        return f"Image {img.size[0]}x{img.size[1]}px. OCR unavailable — demo data will be used."
    except Exception:
        return "Could not read image file."


async def _parse_with_llm(ocr_text: str) -> dict:
    """Use Groq LLM to convert raw OCR text into structured timetable JSON."""
    from langchain_groq import ChatGroq
    from langchain_core.messages import HumanMessage

    llm = ChatGroq(
        api_key=settings.GROQ_API_KEY,
        model="llama-3.1-8b-instant",
        temperature=0,
        max_tokens=2048,
    )

    prompt = TIMETABLE_PROMPT.format(ocr_text=ocr_text)
    response = await llm.ainvoke([HumanMessage(content=prompt)])

    content = response.content.strip()
    # Strip markdown fences if present
    if "```" in content:
        parts = content.split("```")
        for part in parts:
            part = part.strip()
            if part.startswith("json"):
                part = part[4:].strip()
            try:
                return json.loads(part)
            except Exception:
                continue
    return json.loads(content)


def _demo_timetable() -> dict:
    """Fallback timetable when OCR or LLM is unavailable."""
    return {
        "timetable": {
            "Monday": [
                {"start": "09:00", "end": "10:00", "subject": "Mathematics", "location": "LH-1"},
                {"start": "11:00", "end": "13:00", "subject": "Physics Lab", "location": "Lab-3"},
                {"start": "14:00", "end": "15:00", "subject": "Data Structures", "location": "LH-2"},
            ],
            "Tuesday": [
                {"start": "09:00", "end": "10:00", "subject": "Control Systems", "location": "LH-1"},
                {"start": "11:00", "end": "12:00", "subject": "Signal Processing", "location": "LH-3"},
            ],
            "Wednesday": [
                {"start": "09:00", "end": "10:00", "subject": "Mathematics", "location": "LH-1"},
                {"start": "14:00", "end": "15:00", "subject": "Data Structures", "location": "LH-2"},
            ],
            "Thursday": [
                {"start": "09:00", "end": "10:00", "subject": "Control Systems", "location": "LH-1"},
                {"start": "11:00", "end": "13:00", "subject": "DS Lab", "location": "Lab-2"},
            ],
            "Friday": [
                {"start": "09:00", "end": "10:00", "subject": "Mathematics", "location": "LH-1"},
                {"start": "11:00", "end": "12:00", "subject": "Signal Processing", "location": "LH-3"},
            ],
            "Saturday": [],
            "Sunday": [],
        },
        "confidence": 0.5,
    }
