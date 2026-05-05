import logging
from fastapi import APIRouter, Depends

logger = logging.getLogger(__name__)
from fastapi.responses import JSONResponse
from middleware.auth import get_current_user
from models.response import StandardResponse
from services.firebase_service import get_db
from services.task_service import get_stats

router = APIRouter(prefix="/api")

@router.get("/profile")
async def get_profile(current_user: dict = Depends(get_current_user)):
    try:
        stats = get_stats(current_user['uid'])
        return StandardResponse.success_response({
            'uid': current_user['uid'],
            'email': current_user.get('email', ''),
            'name': current_user.get('name', ''),
            **stats
        })
    except Exception as e:
        logger.error(f"Profile error: {e}")
        return JSONResponse(status_code=500, content=StandardResponse.error_response("Internal server error"))

@router.delete("/profile/data")
async def delete_all_user_data(current_user: dict = Depends(get_current_user)):
    """Permanently delete all tasks, notifications for this user"""
    try:
        db = get_db()
        uid = current_user['uid']
        user_ref = db.collection('users').document(uid)

        # Delete tasks in batches
        for collection_name in ['tasks', 'notifications']:
            docs = user_ref.collection(collection_name).get()
            batch = db.batch()
            count = 0
            for doc in docs:
                batch.delete(doc.reference)
                count += 1
                if count >= 500:
                    batch.commit()
                    batch = db.batch()
                    count = 0
            if count > 0:
                batch.commit()

        return StandardResponse.success_response({'deleted': True})
    except Exception as e:
        logger.error(f"Delete all data error: {e}")
        return JSONResponse(status_code=500, content=StandardResponse.error_response("Failed to delete data"))
