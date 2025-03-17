from datetime import datetime
import json
import os
from storage import DATA_DIR, ensure_data_dir, load_json, save_json
from encryption import password_encryption

def save_auto_message(message_data):
    """Save an auto message configuration."""
    messages = load_json('auto_messages.json')
    messages.append(message_data)
    save_json(messages, 'auto_messages.json')

def get_auto_messages(user_id):
    """Get auto messages for a specific user."""
    messages = load_json('auto_messages.json')
    return [msg for msg in messages if msg['user_id'] == user_id and msg['active']]

def save_birthday(birthday_data):
    """Save a birthday reminder."""
    birthdays = load_json('birthdays.json')
    birthdays.append(birthday_data)
    save_json(birthdays, 'birthdays.json')

def get_birthdays(user_id):
    """Get birthdays for a specific user."""
    birthdays = load_json('birthdays.json')
    return [b for b in birthdays if b['user_id'] == user_id]

def get_upcoming_birthdays(user_id):
    """Get upcoming birthdays for a user."""
    birthdays = get_birthdays(user_id)
    today = datetime.now()
    upcoming = []

    for birthday in birthdays:
        bday = datetime.strptime(birthday['date'], "%m/%d")
        bday = bday.replace(year=today.year)
        if bday < today:
            bday = bday.replace(year=today.year + 1)

        # Add to upcoming if within next 30 days
        if (bday - today).days <= 30:
            upcoming.append(birthday)

    return upcoming

def save_timer(timer_data):
    """Save a timer."""
    timers = load_json('timers.json')
    timers.append(timer_data)
    save_json(timers, 'timers.json')

def get_active_timers(user_id):
    """Get active timers for a user."""
    timers = load_json('timers.json')
    now = datetime.now()
    return [
        t for t in timers 
        if t['user_id'] == user_id and 
        datetime.fromisoformat(t['end_time']) > now
    ]

def save_calendar_event(event_data):
    """Save a calendar event."""
    events = load_json('calendar_events.json')
    events.append(event_data)
    save_json(events, 'calendar_events.json')

def get_calendar_events(user_id):
    """Get calendar events for a user."""
    events = load_json('calendar_events.json')
    return [e for e in events if e['user_id'] == user_id]

def save_password(password_data):
    """Save an encrypted password."""
    passwords = load_json('passwords.json')
    # Encrypt the password before saving
    encrypted_password = password_encryption.encrypt(password_data['password'])
    password_data['password'] = encrypted_password
    passwords.append(password_data)
    save_json(passwords, 'passwords.json')

def get_password(user_id, service):
    """Get a decrypted password for a service."""
    passwords = load_json('passwords.json')
    password = next(
        (p for p in passwords if p['user_id'] == user_id and p['service'] == service),
        None
    )
    if password:
        # Decrypt the password before returning
        decrypted = password_encryption.decrypt(password['password'])
        if decrypted:
            password['password'] = decrypted
            return password
    return None

def save_custom_notification(notification_data):
    """Save a custom notification configuration."""
    notifications = load_json('custom_notifications.json')
    notifications.append(notification_data)
    save_json(notifications, 'custom_notifications.json')

def get_custom_notifications(user_id):
    """Get custom notifications for a user."""
    notifications = load_json('custom_notifications.json')
    return [n for n in notifications if n['user_id'] == user_id]