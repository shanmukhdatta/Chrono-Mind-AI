from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse
from middleware.auth import get_current_user
from models.task import TaskCreate, TaskUpdate
from models.response import StandardResponse
from services.task_service import (
    create_task, get_tasks, get_tasks_range, update_task,
    delete_task, complete_task, get_stats, ConflictError
)
from services.notification_service import (
    get_notifications, mark_notification_read, clear_read_notifications
)

router = APIRouter(prefix="/api")

# ── STATS (must be BEFORE /{task_id} route or 'stats' matches as task_id) ──
@router.get("/tasks/stats")
async def get_task_stats(current_user: dict = Depends(get_current_user)):
    try:
        stats = get_stats(current_user['uid'])
        return StandardResponse.success_response(stats)
    except Exception as e:
        print(f"Error getting stats: {e}")
        return JSONResponse(status_code=500, content=StandardResponse.error_response("Internal server error"))

# ── TASK CRUD ──
@router.get("/tasks")
async def list_tasks(
    date: str = Query(None),
    date_from: str = Query(None),
    date_to: str = Query(None),
    status: str = Query('all'),
    current_user: dict = Depends(get_current_user)
):
    try:
        if date_from and date_to:
            tasks = get_tasks_range(current_user['uid'], date_from, date_to, status)
        else:
            tasks = get_tasks(current_user['uid'], date=date, status=status)
        return StandardResponse.success_response(tasks)
    except Exception as e:
        return JSONResponse(status_code=500, content=StandardResponse.error_response(str(e)))

@router.post("/tasks")
async def create_new_task(body: TaskCreate, current_user: dict = Depends(get_current_user)):
    try:
        task = create_task(current_user['uid'], body)
        return StandardResponse.success_response(task)
    except ConflictError as e:
        return JSONResponse(status_code=409, content=StandardResponse.error_response(str(e)))
    except ValueError as e:
        return JSONResponse(status_code=400, content=StandardResponse.error_response(str(e)))
    except Exception as e:
        print(f"Error creating task: {e}")
        return JSONResponse(status_code=500, content=StandardResponse.error_response("Internal server error"))

@router.patch("/tasks/{task_id}")
async def update_existing_task(task_id: str, body: TaskUpdate, current_user: dict = Depends(get_current_user)):
    try:
        task = update_task(current_user['uid'], task_id, body)
        return StandardResponse.success_response(task)
    except ConflictError as e:
        return JSONResponse(status_code=409, content=StandardResponse.error_response(str(e)))
    except ValueError as e:
        return JSONResponse(status_code=400, content=StandardResponse.error_response(str(e)))
    except Exception as e:
        print(f"Error updating task: {e}")
        return JSONResponse(status_code=500, content=StandardResponse.error_response("Internal server error"))

@router.delete("/tasks/{task_id}")
async def delete_existing_task(task_id: str, current_user: dict = Depends(get_current_user)):
    try:
        delete_task(current_user['uid'], task_id)
        return StandardResponse.success_response({"deleted": True})
    except ValueError as e:
        return JSONResponse(status_code=404, content=StandardResponse.error_response(str(e)))
    except Exception as e:
        print(f"Error deleting task: {e}")
        return JSONResponse(status_code=500, content=StandardResponse.error_response("Internal server error"))

@router.post("/tasks/{task_id}/complete")
async def complete_existing_task(task_id: str, current_user: dict = Depends(get_current_user)):
    try:
        task = complete_task(current_user['uid'], task_id)
        return StandardResponse.success_response(task)
    except ValueError as e:
        return JSONResponse(status_code=404, content=StandardResponse.error_response(str(e)))
    except Exception as e:
        print(f"Error completing task: {e}")
        return JSONResponse(status_code=500, content=StandardResponse.error_response("Internal server error"))

# ── NOTIFICATIONS ──
@router.get("/notifications")
async def list_notifications(current_user: dict = Depends(get_current_user)):
    try:
        notifications = get_notifications(current_user['uid'])
        return StandardResponse.success_response(notifications)
    except Exception as e:
        return JSONResponse(status_code=500, content=StandardResponse.error_response("Failed to fetch notifications"))

@router.patch("/notifications/{notif_id}/read")
async def mark_notif_read(notif_id: str, current_user: dict = Depends(get_current_user)):
    try:
        mark_notification_read(current_user['uid'], notif_id)
        return StandardResponse.success_response({"read": True})
    except Exception as e:
        return JSONResponse(status_code=500, content=StandardResponse.error_response("Failed to mark as read"))

@router.delete("/notifications/clear")
async def clear_notifications(current_user: dict = Depends(get_current_user)):
    try:
        clear_read_notifications(current_user['uid'])
        return StandardResponse.success_response({"cleared": True})
    except Exception as e:
        return JSONResponse(status_code=500, content=StandardResponse.error_response("Failed to clear notifications"))
