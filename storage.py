import json
import os
from datetime import datetime

DATA_DIR = "data"

def ensure_data_dir():
    """Ensure data directory exists."""
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)

def load_json(filename):
    """Load data from JSON file."""
    ensure_data_dir()
    filepath = os.path.join(DATA_DIR, filename)
    if not os.path.exists(filepath):
        return []
    with open(filepath, 'r') as f:
        return json.load(f)

def save_json(data, filename):
    """Save data to JSON file."""
    ensure_data_dir()
    filepath = os.path.join(DATA_DIR, filename)
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)

def save_reminder(reminder):
    """Save a reminder to reminders.json."""
    reminders = load_json('reminders.json')
    reminders.append(reminder)
    save_json(reminders, 'reminders.json')

def update_reminder(user_id, reminder_index, new_time=None, new_message=None):
    """Update a reminder's time or message."""
    reminders = load_json('reminders.json')
    user_reminders = [r for r in reminders if r['user_id'] == user_id]

    if 0 <= reminder_index < len(user_reminders):
        target_time = user_reminders[reminder_index]['time']
        for reminder in reminders:
            if reminder['user_id'] == user_id and reminder['time'] == target_time:
                if new_time:
                    reminder['time'] = new_time
                if new_message:
                    reminder['message'] = new_message
                break
        save_json(reminders, 'reminders.json')
        return True
    return False

def delete_reminder(user_id, reminder_index):
    """Delete a reminder."""
    reminders = load_json('reminders.json')
    user_reminders = [r for r in reminders if r['user_id'] == user_id]

    if 0 <= reminder_index < len(user_reminders):
        target_time = user_reminders[reminder_index]['time']
        reminders = [r for r in reminders if not (r['user_id'] == user_id and r['time'] == target_time)]
        save_json(reminders, 'reminders.json')
        return True
    return False

def get_reminders(user_id):
    """Get reminders for a specific user."""
    reminders = load_json('reminders.json')
    return [r for r in reminders if r['user_id'] == user_id]

def get_active_reminders(user_id):
    """Get active reminders for a user."""
    now = datetime.now()
    reminders = get_reminders(user_id)
    return [r for r in reminders if datetime.fromisoformat(r['time']) > now]

def save_task(task):
    """Save a task to tasks.json."""
    tasks = load_json('tasks.json')
    tasks.append(task)
    save_json(tasks, 'tasks.json')

def update_task(user_id, task_index, new_task=None):
    """Update a task's content."""
    tasks = load_json('tasks.json')
    user_tasks = [t for t in tasks if t['user_id'] == user_id]

    if 0 <= task_index < len(user_tasks):
        task_id = user_tasks[task_index]['created_at']
        for task in tasks:
            if task['user_id'] == user_id and task['created_at'] == task_id:
                if new_task:
                    task['task'] = new_task
                break
        save_json(tasks, 'tasks.json')
        return True
    return False

def delete_task(user_id, task_index):
    """Delete a task."""
    tasks = load_json('tasks.json')
    user_tasks = [t for t in tasks if t['user_id'] == user_id]

    if 0 <= task_index < len(user_tasks):
        task_id = user_tasks[task_index]['created_at']
        tasks = [t for t in tasks if not (t['user_id'] == user_id and t['created_at'] == task_id)]
        save_json(tasks, 'tasks.json')
        return True
    return False

def get_tasks(user_id):
    """Get tasks for a specific user."""
    tasks = load_json('tasks.json')
    return [task for task in tasks if task['user_id'] == user_id]

def update_task_status(user_id, task_index, completed):
    """Update task completion status."""
    tasks = load_json('tasks.json')
    user_tasks = [t for t in tasks if t['user_id'] == user_id]
    if 0 <= task_index < len(user_tasks):
        task_id = user_tasks[task_index]['created_at']
        for task in tasks:
            if task['user_id'] == user_id and task['created_at'] == task_id:
                task['completed'] = completed
                break
    save_json(tasks, 'tasks.json')

def save_goal(goal):
    """Save a goal to goals.json."""
    goals = load_json('goals.json')
    goals.append(goal)
    save_json(goals, 'goals.json')

def get_goals(user_id):
    """Get goals for a specific user."""
    goals = load_json('goals.json')
    return [goal for goal in goals if goal['user_id'] == user_id]

def update_goal_progress(user_id, goal_id, progress):
    """Update goal progress."""
    goals = load_json('goals.json')
    for goal in goals:
        if goal['user_id'] == user_id and goal['id'] == goal_id:
            goal['progress'] = min(100, max(0, progress))
            break
    save_json(goals, 'goals.json')

def save_expense(expense):
    """Save an expense to expenses.json."""
    expenses = load_json('expenses.json')
    expenses.append(expense)
    save_json(expenses, 'expenses.json')

def save_note(note):
    """Save a note to notes.json."""
    notes = load_json('notes.json')
    notes.append(note)
    save_json(notes, 'notes.json')

def get_notes(user_id):
    """Get notes for a specific user."""
    notes = load_json('notes.json')
    return [note for note in notes if note['user_id'] == user_id]