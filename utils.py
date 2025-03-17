from datetime import datetime, timedelta

def parse_time(time_str):
    """Parse time string into datetime object in IST."""
    today = datetime.now() + timedelta(hours=5, minutes=30)  # Convert to IST
    try:
        # Try parsing as HH:MM
        time = datetime.strptime(time_str, "%H:%M")
        # Set to today's date
        result = datetime.combine(today.date(), time.time())
        # If the time has already passed today, set it for tomorrow
        if result < today:
            result += timedelta(days=1)
        return result
    except ValueError:
        try:
            # Try parsing as MM/DD/YYYY HH:MM
            return datetime.strptime(time_str, "%m/%d/%Y %H:%M") + timedelta(hours=5, minutes=30)
        except ValueError:
            return None

def format_task_list(tasks):
    """Format task list for display with IST timestamps."""
    if not tasks:
        return "No tasks found!"

    formatted = "📝 Your Tasks:\n\n"
    for i, task in enumerate(tasks, 1):
        status = "✅" if task['completed'] else "⬜️"
        # Convert timestamp to IST
        created_time = datetime.fromisoformat(task['created_at']) + timedelta(hours=5, minutes=30)
        formatted += f"{i}. {status} {task['task']}\n"
        formatted += f"   Created: {created_time.strftime('%Y-%m-%d %I:%M %p')} IST\n"
        formatted += f"   /edit_task_{i} | /delete_task_{i}\n\n"

    return formatted

def format_reminder_list(reminders):
    """Format reminder list for display with IST timestamps."""
    if not reminders:
        return "No reminders found!"

    formatted = "⏰ Your Reminders:\n\n"
    for i, reminder in enumerate(reminders, 1):
        # Convert timestamp to IST
        reminder_time = datetime.fromisoformat(reminder['time']) + timedelta(hours=5, minutes=30)
        formatted += f"{i}. {reminder_time.strftime('%Y-%m-%d %I:%M %p')} IST - {reminder['message']}\n"
        formatted += f"   /edit_reminder_{i} | /delete_reminder_{i}\n\n"

    return formatted

def to_ist(utc_time):
    """Convert UTC datetime to IST."""
    if isinstance(utc_time, str):
        utc_time = datetime.fromisoformat(utc_time)
    return utc_time + timedelta(hours=5, minutes=30)

def from_ist(ist_time):
    """Convert IST datetime to UTC for storage."""
    if isinstance(ist_time, str):
        ist_time = datetime.fromisoformat(ist_time)
    return ist_time - timedelta(hours=5, minutes=30)