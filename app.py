from flask import Flask, request, render_template, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import json, os, re
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
# Updated import: added update_time_fields for updating time spent and time remaining
from azure_devops import *
from openai_utils import get_response, parse_task_suggestion, analyze_user_intent
from dotenv import load_dotenv
from sqlalchemy import inspect

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# --- User Model ---
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    azure_devops_email = db.Column(db.String(120))
    chat_history = db.Column(db.Text, default='[]')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def chat_history_list(self):
        try:
            return json.loads(self.chat_history)
        except Exception:
            return []
    @chat_history_list.setter
    def chat_history_list(self, value):
        self.chat_history = json.dumps(value)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# --- Helper Functions ---
def format_tasks(tasks):
    """Formats work items to an HTML list."""
    lines = []
    for task in tasks:
        fields = task.get("fields", {})
        title = fields.get("System.Title", "No Title")
        state = fields.get("System.State", "Unknown")
        due = fields.get("Microsoft.VSTS.Scheduling.DueDate", "No date")
        lines.append(f"{title} (State: {state}, Due: {due})")
    return "<br>".join(lines)

def analyze_high_priority_tasks(tasks, user_email=None):
    """
    Returns tasks that are high priority:
      - Either tasks that are overdue (days_remaining < 0)
      - Or tasks with deadlines within 3 days (threshold adjustable)
    If user_email is provided, only tasks assigned to that email are returned.
    """
    high_priority = []
    today = datetime.now().date()
    for task in tasks:
        fields = task.get("fields", {})
        due_date_str = fields.get("Microsoft.VSTS.Scheduling.DueDate")
        days_remaining = None
        if due_date_str:
            try:
                due_date = datetime.strptime(due_date_str, "%Y-%m-%dT00:00:00Z").date()
                days_remaining = (due_date - today).days
            except Exception:
                pass
        if days_remaining is not None and (days_remaining < 0 or days_remaining <= 3):
            task["days_remaining"] = days_remaining
            if user_email:
                assigned = fields.get("System.AssignedTo", "")
                if isinstance(assigned, dict):
                    assigned = assigned.get("uniqueName", "")
                if user_email.lower() in assigned.lower():
                    high_priority.append(task)
            else:
                high_priority.append(task)
    return high_priority

def generate_ai_suggestion(context, tasks):
    """Generates an AI suggestion using OpenAI based on tasks."""
    task_context = "\n".join(
        f"- {t['fields']['System.Title']} (State: {t['fields']['System.State']}, Due: {t['fields'].get('Microsoft.VSTS.Scheduling.DueDate', 'No date')})"
        for t in tasks[:5]
    )
    prompt = f"""
Based on these tasks:
{task_context}

Provide a concise summary regarding: {context}
"""
    return get_response(prompt)

# --- Authentication & Profile Routes ---
@app.route("/register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('chat'))
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        if password != confirm_password:
            flash('Passwords do not match!')
            return redirect(url_for('register'))
        if User.query.filter((User.username == username) | (User.email == email)).first():
            flash('Username or email already exists!')
            return redirect(url_for('register'))
        new_user = User(username=username, email=email, azure_devops_email="")
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        flash('Registration successful! Please login.')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('chat'))
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('chat'))
        flash('Invalid email or password!')
        return redirect(url_for('login'))
    return render_template('login.html')

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route("/profile", methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        new_email = request.form['azure_email'].strip()
        if not re.match(r"^.?<.?>$", new_email):
            flash('Use format: "Display Name <email@domain.com>"')
            return redirect(url_for('profile'))
        # Re-fetch the user from the database for synchronization
        user = User.query.filter_by(id=current_user.id).first()
        if user:
            user.azure_devops_email = new_email
            db.session.commit()
            flash('Profile updated!')
        else:
            flash('User not found in database.')
        return redirect(url_for('profile'))
    return render_template('profile.html')

# --- New Route: Delete Chat History ---
@app.route("/delete_history", methods=["POST"])
@login_required
def delete_history():
    current_user.chat_history_list = []
    db.session.commit()
    return jsonify({"status": "success", "message": "Chat history deleted."})

@app.route("/", methods=["GET", "POST"])
@login_required
def chat():
    if request.method == "POST":
        message = request.form["message"].strip()
        current_user.chat_history_list += [{"type": "user", "text": message}]
        tasks = get_work_items()
        response = ""

        intent = analyze_user_intent(message)
        action = intent.get("action")
        params = intent.get("parameters", {})

        try:
            if action == "smalltalk":
    # For small talk, send the original message directly to GPT for a human-like reply
             response = get_response([{"role": "user", "content": message}])
             
            elif action == "create_task":
                title = params.get("title")
                description = params.get("description", "")
                due_date = params.get("due_date")
                assignee = current_user.azure_devops_email or current_user.email
                task_id = create_work_item(title, description, assignee, due_date)
                response = f"Task '{title}' created with ID {task_id}."

            elif action == "update_time":
                title = params.get("task_title", "").lower()
                time_spent = params.get("time_spent")
                time_remaining = params.get("time_remaining")
                matched_task = next((t for t in tasks if title in t["fields"].get("System.Title", "").lower()), None)
                if matched_task:
                    task_id = int(matched_task["id"])
                    update_time_fields(task_id, time_spent, time_remaining)
                    response = f"Updated '{title}' with time spent = {time_spent}, remaining = {time_remaining}."
                else:
                    response = f"Task '{title}' not found."

            elif action == "update_assignment":
                task_id = int(params.get("task_id"))
                assignee = params.get("assignee")
                update_task_assignment(task_id, assignee)
                response = f"Task {task_id} assigned to {assignee}."
            
            elif action == "delete_task":
                title = params.get("task_title", "").lower()
                matched_task = next((t for t in tasks if title in t["fields"].get("System.Title", "").lower()), None)
                if matched_task:
                    task_id = int(matched_task["id"])
                    delete_work_item(task_id)
                    response = f"Task '{title}' has been deleted."
                else:
                    response = f"Task '{title}' not found."

            elif action == "list_all_tasks":
                response = "All work items:<br>" + format_tasks(tasks)

            elif action == "show_my_tasks":
                email = (current_user.azure_devops_email or current_user.email).lower()
                my_tasks = [
                    t for t in tasks
                    if email in str(t["fields"].get("System.AssignedTo", "")).lower()
                ]
                response = "Your tasks:<br>" + format_tasks(my_tasks) if my_tasks else "No tasks assigned to you."

            elif action in ["show_priority_tasks", "summarize_tasks"]:
                email = current_user.azure_devops_email
                filtered = analyze_high_priority_tasks(tasks, email if "my" in message else None)
                if filtered:
                    summary = []
                    for t in filtered:
                        title = t["fields"].get("System.Title", "No Title")
                        dr = t.get("days_remaining", "N/A")
                        status = (
                            f"{abs(dr)} days overdue" if dr < 0 else
                            "due today" if dr == 0 else
                            "due tomorrow" if dr == 1 else
                            f"due in {dr} days"
                        )
                        summary.append(f"{title} ({status})")
                    response = f"{len(filtered)} high-priority tasks: " + ", ".join(summary)
                else:
                    response = "No high-priority tasks."

            elif action == "show_pending_tasks":
                pending_tasks = [
                    t for t in tasks
                    if t["fields"].get("System.State", "").lower() not in ["closed", "done", "removed", "resolved"]
                ]
                if pending_tasks:
                    response = "Pending tasks:<br>" + format_tasks(pending_tasks)
                else:
                    response = "No pending tasks found."
            
            elif action == "show_completed_tasks":
                completed_tasks = [
                     t for t in tasks
                    if t["fields"].get("System.State", "").lower() in ["done", "removed"]
             ]
                if completed_tasks:
                        response = "Completed tasks:<br>" + format_tasks(completed_tasks)
                else:
                        response = "No completed tasks found."



            elif action == "update_status":
                title = params.get("task_title", "").lower()
                status = params.get("status", "")
                matched_task = next((t for t in tasks if title in t["fields"].get("System.Title", "").lower()), None)
                if matched_task:
                    task_id = int(matched_task["id"])
                    update_task_status(task_id, status)
                    response = f"Task '{title}' status updated to {status}."
                else:
                    response = f"Task '{title}' not found."

            else:
                response = "Sorry, I didn’t understand that. Please rephrase."

        except Exception as e:
            error_message = str(e)
            gpt_prompt = f"""
            You're a helpful assistant. The following error occurred in an Azure DevOps integration while trying to update a task status:

            Error:
            "{error_message}"

            Please explain the issue in simple terms for a non-technical user and suggest what they could do next (if applicable).
            """

            response = get_response([{"role": "user", "content": gpt_prompt}])


        current_user.chat_history_list += [{"type": "bot", "text": response}]
        db.session.commit()
        return jsonify({"status": "success", "response": response, "history": current_user.chat_history_list})

    return render_template("index.html", history=current_user.chat_history_list)


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        inspector = inspect(db.engine)
        columns = [col['name'] for col in inspector.get_columns('user')]
        if 'chat_history' not in columns:
            with db.engine.connect() as connection:
                connection.execute('ALTER TABLE user ADD COLUMN chat_history TEXT')
                connection.execute("UPDATE user SET chat_history = '[]' WHERE chat_history IS NULL")
        app.run(debug=True)