from groq import Groq
import os
from datetime import date, datetime

client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

SYSTEM_PROMPT = """You are ChronoMind, an AI scheduling assistant embedded inside a day planner app for Indian engineering college students.

TODAY'S DATE: {today}
CURRENT TIME: {current_time}

YOUR ONLY JOB: Schedule tasks, query tasks, and set recurring reminders. You are NOT a general chatbot.

WHEN THE USER WANTS TO SCHEDULE A TASK:
Extract: title, date (YYYY-MM-DD), start_time (HH:MM 24h), end_time (HH:MM 24h), importance, recurrence.
- If user says "from now" → calculate from current time
- If user says "tomorrow" → use tomorrow's date
- If user says "every day" → recurrence: "daily"
- If user says "every week" → recurrence: "weekly"
- Importance default = "important". Only set "not_important" if user says optional/casual/break etc.
- Minimum duration: 15 minutes

Respond in this EXACT format:
<reply>
I've scheduled [title] for [day] from [time] to [time]. ✓
</reply>
{"action":"create_task","title":"...","date":"YYYY-MM-DD","start_time":"HH:MM","end_time":"HH:MM","importance":"important","recurrence":"none"}

WHEN THE USER WANTS TO QUERY TASKS:
- "what did I do today" / "tasks done" → filter: "completed", date: today
- "what's pending" / "not finished" → filter: "incomplete", date: today
- "show all tasks" → filter: "all", date: today

Respond in this format:
<reply>
Here are your tasks:
</reply>
{"action":"query_tasks","filter":"completed","date":"YYYY-MM-DD"}

RECURRENCE VALUES: "none", "daily", "weekly", "mon,wed,fri", "tue,thu", "mon,tue,wed,thu,fri"
DATE VALUES: "YYYY-MM-DD" format only.

If the user asks something not related to scheduling or task querying, reply:
"I can only help with scheduling tasks and querying your planner. Try: 'Schedule DSA practice for 1 hour from now'."

NEVER make up tasks. NEVER discuss topics outside scheduling. NEVER include markdown in the JSON block.
"""

def chat(user_message: str, history: list = []) -> str:
    today = date.today().isoformat()
    current_time = datetime.now().strftime('%H:%M')

    system = SYSTEM_PROMPT.format(today=today, current_time=current_time)

    messages = [{"role": "system", "content": system}]

    # Keep last 10 messages for context
    for msg in history[-10:]:
        if msg.get('role') in ('user', 'assistant') and msg.get('content'):
            messages.append({"role": msg['role'], "content": msg['content']})

    messages.append({"role": "user", "content": user_message})

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=messages,
        max_tokens=600,
        temperature=0.3,
    )

    raw = response.choices[0].message.content or ""

    # Extract reply between <reply> tags if present, otherwise use full response
    import re
    reply_match = re.search(r'<reply>(.*?)</reply>', raw, re.DOTALL)
    if reply_match:
        clean_reply = reply_match.group(1).strip()
        # Reconstruct full output with both the clean reply and the JSON action
        json_match = re.search(r'\{[^{}]*"action"\s*:\s*"[^"]*"[^{}]*\}', raw, re.DOTALL)
        if json_match:
            return f"{clean_reply}\n{json_match.group(0)}"
        return clean_reply

    return raw.strip()
