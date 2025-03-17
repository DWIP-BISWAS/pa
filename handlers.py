from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from storage import (
    save_reminder, save_task, get_tasks, update_task_status,
    save_expense, save_note, get_notes, get_active_reminders,
    update_task, delete_task, update_reminder, delete_reminder
)
from utils import parse_time, format_task_list, format_reminder_list

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a message when the command /start or /help is issued."""
    welcome_message = (
        "👋 Welcome to your Personal Task Management Bot!\n\n"
        "Here's what I can help you with:\n\n"
        "📋 Task Management:\n"
        "/addtask - Add a new task\n"
        "/todo - View your to-do list\n"
        "/done - Mark a task as completed\n"
        "/remind - Set a reminder\n"
        "/reminders - View active reminders\n\n"
        "💰 Financial Management:\n"
        "/spend - Log an expense\n\n"
        "📝 Notes & Goals:\n"
        "/note - Add a note\n"
        "/viewnotes - View all notes\n"
        "/addgoal - Add a new goal\n"
        "/goals - View all goals\n"
        "/updategoal - Update goal progress\n\n"
        "⚡ Smart Features:\n"
        "/weather - Get weather information\n"
        "/automessage - Set automatic daily messages\n"
        "/timer - Set a countdown timer\n"
        "/translate - Translate text\n"
        "/news - Get latest news updates\n"
        "/birthday - Set birthday reminders\n"
        "/email - Check unread emails\n"
        "/password - Manage passwords\n"
        "/calendar - Manage calendar events\n"
        "/notify - Set custom notifications\n\n"
        "Type /help to see usage examples for each command!"
    )

    # Create quick action buttons
    keyboard = [
        [
            InlineKeyboardButton("📋 Add Task", callback_data="quick_addtask"),
            InlineKeyboardButton("⏰ Set Reminder", callback_data="quick_remind")
        ],
        [
            InlineKeyboardButton("📝 Add Note", callback_data="quick_note"),
            InlineKeyboardButton("💰 Log Expense", callback_data="quick_spend")
        ],
        [
            InlineKeyboardButton("🎯 Add Goal", callback_data="quick_goal"),
            InlineKeyboardButton("🌤 Weather", callback_data="quick_weather")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(welcome_message, reply_markup=reply_markup)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send help message with list of commands."""
    help_message = (
        "📚 Command Usage Guide:\n\n"
        "Task Management:\n"
        "/addtask <task> - Example: /addtask Buy groceries\n"
        "/todo - Shows your task list with edit/delete buttons\n"
        "/done <number> - Example: /done 1\n"
        "/remind <time> <message> - Example: /remind 14:30 Call mom\n"
        "/reminders - Shows active reminders with edit/delete buttons\n\n"
        "Financial Management:\n"
        "/spend <amount> <description> - Example: /spend 25.50 Lunch\n\n"
        "Notes & Goals:\n"
        "/note <title> <content> - Example: /note Meeting Notes Discuss project timeline\n"
        "/viewnotes - View all your saved notes\n"
        "/addgoal <title> <target_date> <description> - Example: /addgoal 'Learn Python' 12/31/2025 Master programming\n"
        "/goals - View your goals and progress\n"
        "/updategoal <goal_id> <progress> - Example: /updategoal abc123 75\n\n"
        "Smart Features:\n"
        "/weather <city> - Example: /weather London\n"
        "/automessage <time> <message> - Example: /automessage 09:00 Good morning!\n"
        "/timer <minutes> - Example: /timer 30\n"
        "/translate <lang> <text> - Example: /translate es Hello world\n"
        "/news [category] - Example: /news technology\n"
        "/birthday <name> <MM/DD> - Example: /birthday John 12/25\n"
        "/email - Check your unread emails\n"
        "/password store <service> <password> - Example: /password store gmail mypass123\n"
        "/password get <service> - Example: /password get gmail\n"
        "/calendar add <date> <event> - Example: /calendar add 2025-03-20 Team meeting\n"
        "/calendar list - View your calendar events\n"
        "/notify <trigger> <message> - Example: /notify daily Good morning!\n\n"
        "Need more help? Just type any command and I'll guide you!"
    )
    await update.message.reply_text(help_message)

async def remind_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Set a reminder."""
    try:
        time_str = context.args[0]
        message = ' '.join(context.args[1:])

        if not message:
            await update.message.reply_text("Please provide both time and message!")
            return

        reminder_time = parse_time(time_str)
        if not reminder_time:
            await update.message.reply_text(
                "Invalid time format!\n"
                "Use HH:MM for today or MM/DD/YYYY HH:MM for a specific date."
            )
            return

        save_reminder({
            'time': reminder_time.isoformat(),
            'message': message,
            'user_id': update.effective_user.id
        })

        await update.message.reply_text(
            f"⏰ Reminder set for {reminder_time.strftime('%Y-%m-%d %H:%M')}"
        )

    except (IndexError, ValueError):
        await update.message.reply_text(
            "Usage: /remind <time> <message>\n"
            "Example: /remind 14:30 Call mom\n"
            "Or: /remind 12/25/2025 10:00 Christmas party"
        )

async def view_reminders_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """View all active reminders."""
    reminders = get_active_reminders(update.effective_user.id)
    formatted_list = format_reminder_list(reminders)
    await update.message.reply_text(formatted_list)

async def edit_reminder_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Edit a reminder."""
    try:
        command_parts = update.message.text.split('_')
        if len(command_parts) != 3:
            raise ValueError("Invalid command format")

        reminder_index = int(command_parts[2]) - 1
        time_str = context.args[0]
        message = ' '.join(context.args[1:])

        reminder_time = parse_time(time_str)
        if not reminder_time:
            await update.message.reply_text("Invalid time format!")
            return

        if update_reminder(
            update.effective_user.id,
            reminder_index,
            reminder_time.isoformat(),
            message
        ):
            await update.message.reply_text("✅ Reminder updated!")
            await view_reminders_command(update, context)
        else:
            await update.message.reply_text("❌ Reminder not found!")

    except (IndexError, ValueError):
        await update.message.reply_text(
            "Usage: /edit_reminder_X <new_time> <new_message>\n"
            "Example: /edit_reminder_1 14:30 Updated reminder message"
        )

async def delete_reminder_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Delete a reminder."""
    try:
        command_parts = update.message.text.split('_')
        if len(command_parts) != 3:
            raise ValueError("Invalid command format")

        reminder_index = int(command_parts[2]) - 1
        if delete_reminder(update.effective_user.id, reminder_index):
            await update.message.reply_text("✅ Reminder deleted!")
            await view_reminders_command(update, context)
        else:
            await update.message.reply_text("❌ Reminder not found!")

    except (IndexError, ValueError):
        await update.message.reply_text("Invalid reminder number!")

async def add_task_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Add a new task."""
    try:
        task = ' '.join(context.args)
        if not task:
            await update.message.reply_text("Please provide a task!")
            return

        save_task({
            'task': task,
            'created_at': datetime.now().isoformat(),
            'completed': False,
            'user_id': update.effective_user.id
        })

        await update.message.reply_text(f"✅ Task added: {task}")

    except IndexError:
        await update.message.reply_text("Usage: /addtask <task description>")

async def todo_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show todo list."""
    tasks = get_tasks(update.effective_user.id)
    formatted_list = format_task_list(tasks)
    await update.message.reply_text(formatted_list)

async def done_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Mark a task as completed."""
    try:
        task_number = int(context.args[0]) - 1
        update_task_status(update.effective_user.id, task_number, True)
        await update.message.reply_text("✅ Task marked as completed!")

        # Show updated task list
        await todo_command(update, context)

    except (IndexError, ValueError):
        await update.message.reply_text("Usage: /done <task_number>")

async def edit_task_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Edit a task."""
    try:
        command_parts = update.message.text.split('_')
        if len(command_parts) != 3:
            raise ValueError("Invalid command format")

        task_index = int(command_parts[2]) - 1
        new_task = ' '.join(context.args)

        if update_task(update.effective_user.id, task_index, new_task):
            await update.message.reply_text("✅ Task updated!")
            await todo_command(update, context)
        else:
            await update.message.reply_text("❌ Task not found!")

    except (IndexError, ValueError):
        await update.message.reply_text(
            "Usage: /edit_task_X <new task description>\n"
            "Example: /edit_task_1 Updated task description"
        )

async def delete_task_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Delete a task."""
    try:
        command_parts = update.message.text.split('_')
        if len(command_parts) != 3:
            raise ValueError("Invalid command format")

        task_index = int(command_parts[2]) - 1
        if delete_task(update.effective_user.id, task_index):
            await update.message.reply_text("✅ Task deleted!")
            await todo_command(update, context)
        else:
            await update.message.reply_text("❌ Task not found!")

    except (IndexError, ValueError):
        await update.message.reply_text("Invalid task number!")

async def spend_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Log an expense."""
    try:
        amount = float(context.args[0])
        description = ' '.join(context.args[1:])

        if not description:
            await update.message.reply_text("Please provide both amount and description!")
            return

        save_expense({
            'amount': amount,
            'description': description,
            'date': datetime.now().isoformat(),
            'user_id': update.effective_user.id
        })

        await update.message.reply_text(f"💰 Expense logged: ${amount:.2f} - {description}")

    except (IndexError, ValueError):
        await update.message.reply_text("Usage: /spend <amount> <description>")

async def note_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Save a note."""
    try:
        title = context.args[0]
        content = ' '.join(context.args[1:])

        if not content:
            await update.message.reply_text("Please provide both title and content!")
            return

        save_note({
            'title': title,
            'content': content,
            'created_at': datetime.now().isoformat(),
            'user_id': update.effective_user.id
        })

        await update.message.reply_text(f"📝 Note saved: {title}")

    except IndexError:
        await update.message.reply_text("Usage: /note <title> <content>")

async def view_notes_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """View all notes."""
    notes = get_notes(update.effective_user.id)
    if not notes:
        await update.message.reply_text("No notes found!")
        return

    notes_text = "📝 Your Notes:\n\n"
    for note in notes:
        notes_text += f"📌 {note['title']}\n{note['content']}\n\n"

    await update.message.reply_text(notes_text)