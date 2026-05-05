import logging
from fastapi import APIRouter, Depends, Request

logger = logging.getLogger(__name__)
from fastapi.responses import JSONResponse
from middleware.auth import get_current_user
from models.assistant import ChatRequest
from models.response import StandardResponse
from services.groq_service import chat
from services.task_service import get_tasks, create_task
from models.task import TaskCreate
import json

router = APIRouter(prefix="/api")

def parse_action_from_reply(reply: str):
    """Extract JSON action block from Groq reply"""
    import re
    # Look for JSON object in the reply
    json_pattern = r'\{[^{}]*"action"\s*:\s*"[^"]*"[^{}]*\}'
    matches = re.findall(json_pattern, reply, re.DOTALL)
    for match in matches:
        try:
            action = json.loads(match)
            if 'action' in action:
                return action
        except json.JSONDecodeError:
            continue
    return None

@router.post("/assistant/chat")
async def assistant_chat(
    request: Request,
    body: ChatRequest,
    current_user: dict = Depends(get_current_user)
):
    try:
        history = [{"role": msg.role, "content": msg.content} for msg in body.conversation_history]
        reply = chat(body.message, history)

        # Parse action from reply
        action = parse_action_from_reply(reply)
        action_result = None

        if action:
            if action.get('action') == 'create_task':
                try:
                    task_data = TaskCreate(
                        title=action.get('title', 'Untitled Task'),
                        date=action.get('date', ''),
                        start_time=action.get('start_time', '09:00'),
                        end_time=action.get('end_time', '10:00'),
                        importance=action.get('importance', 'important'),
                        recurrence=action.get('recurrence', 'none'),
                    )
                    created_task = create_task(current_user['uid'], task_data)
                    action_result = {'type': 'task_created', 'task': created_task}
                except Exception as e:
                    action_result = {'type': 'error', 'message': str(e)}

            elif action.get('action') == 'query_tasks':
                try:
                    filter_type = action.get('filter', 'all')
                    query_date = action.get('date', None)
                    tasks = get_tasks(current_user['uid'], date=query_date, status=filter_type)
                    action_result = {'type': 'tasks_list', 'tasks': tasks, 'filter': filter_type, 'date': query_date}
                except Exception as e:
                    action_result = {'type': 'error', 'message': str(e)}

        return StandardResponse.success_response({
            "reply": reply,
            "action": action,
            "action_result": action_result
        })

    except Exception as e:
        logger.error(f"Assistant error: {e}")
        return JSONResponse(
            status_code=500,
            content=StandardResponse.error_response("Assistant temporarily unavailable")
        )
