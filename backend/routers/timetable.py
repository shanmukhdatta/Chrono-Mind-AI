from fastapi import APIRouter, Depends, File, UploadFile, HTTPException
from middleware.auth import get_current_user
from models.response import StandardResponse

router = APIRouter(prefix="/api")

@router.post("/timetable/upload")
async def upload_timetable(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    """
    Timetable OCR import — DEMO PLACEHOLDER (Phase 2).
    Returns 501 Not Implemented so the frontend can show a coming soon message.
    """
    # Validate file type client-side hint
    allowed = {'image/jpeg', 'image/png', 'image/webp', 'application/pdf'}
    if file.content_type not in allowed:
        raise HTTPException(status_code=400, detail="Please upload a JPG, PNG, WEBP, or PDF file.")

    raise HTTPException(
        status_code=501,
        detail="Timetable OCR import is coming in Phase 2. Stay tuned!"
    )
