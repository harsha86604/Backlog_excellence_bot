import os
import openai
import json

openai.api_key = os.getenv("OPENAI_API_KEY")  # Must be defined in .env

def get_response(conversation_history):
    """
    Calls the OpenAI API with the entire conversation context.
    conversation_history should be a list of dicts: [{"role": "user"|"assistant", "content": "..."}].
    """
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=conversation_history,
            temperature=0.7
        )
        return response["choices"][0]["message"]["content"]
    except Exception as e:
        return f"Error from OpenAI: {str(e)}"

def parse_task_suggestion(user_message, ai_response=""):
    """
    Very simplistic example of how to detect an 'action'
    from the user's message or the AI's response.
    For our use, if the message contains "update time", we'll try to extract the task title,
    time spent, and time remaining.
    """
    result = {
        "action": None,
        "task_title": None,
        "time_spent": None,
        "time_remaining": None,
        "assignee": None,
        "title": None,
        "description": None
    }

    msg_lower = user_message.lower()

    if "update time" in msg_lower:
        result["action"] = "update_time"
        try:
            details = user_message.split(":", 1)[1].strip()
            if details.lower().startswith("task"):
                details = details[4:].strip()
            if "spent" in details and "remaining" in details:
                parts = details.split("spent")
                task_title = parts[0].strip()
                remainder = parts[1].strip()
                if "remaining" in remainder:
                    spent_str, remaining_str = remainder.split("remaining", 1)
                    result["task_title"] = task_title
                    result["time_spent"] = float(spent_str.strip())
                    result["time_remaining"] = float(remaining_str.strip())
        except Exception:
            pass
    elif "create task" in msg_lower:
        result["action"] = "create"
        result["title"] = "Example Title from parse_task_suggestion"
        result["description"] = "Example Description from parse_task_suggestion"
    elif "fetch tasks" in msg_lower:
        result["action"] = "fetch"

    return result

def analyze_user_intent(user_message):
    """
    Uses GPT to classify the intent and extract structured info from a user's message.
    Ensures that if action is update_status, the status is from the allowed values.
    """
    valid_statuses = ["To Do", "In Progress", "Blocked", "Done", "Removed"]

    prompt = f"""
You are an intelligent assistant that helps manage tasks using Azure DevOps and also responds to friendly small talk.

Classify this user message:
"{user_message}"

Return a JSON object with:
- action: One of [create_task, update_time, update_assignment, update_status, list_all_tasks, show_my_tasks, delete_task, show_priority_tasks, summarize_tasks, show_pending_tasks, show_completed_tasks, smalltalk, unknown]
- parameters: A dictionary of relevant fields (can be empty if not needed)

⚠ IMPORTANT:
If the action is "update_status", set the status to exactly one of the following:
{valid_statuses}

Only return the JSON. No explanations.

Examples:
{{
  "action": "smalltalk",
  "parameters": {{}}
}}

{{
  "action": "create_task",
  "parameters": {{
    "title": "Fix login",
    "description": "Bug in login flow"
  }}
}}

{{
  "action": "update_time",
  "parameters": {{
    "task_title": "Fix login",
    "time_spent": 2,
    "time_remaining": 3
  }}
}}

{{
  "action": "update_status",
  "parameters": {{
    "task_title": "Fix login",
    "status": "In Progress"
  }}
}}

{{
  "action": "show_pending_tasks",
  "parameters": {{}}
}}

{{
  "action": "show_completed_tasks",
  "parameters": {{}}
}}
{{
  "action": "delete_task",
  "parameters": {{
    "task_title": "Fix login"
  }}
}}
"""

    try:
        res = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0
        )
        json_output = res["choices"][0]["message"]["content"]
        return {
            **json.loads(json_output),
            "raw_response": json_output
        }
    except Exception as e:
        return {
            "action": "unknown",
            "parameters": {},
            "raw_response": f"Error: {str(e)}"
        }