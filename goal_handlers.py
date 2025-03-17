from datetime import datetime
import uuid
from telegram import Update
from telegram.ext import ContextTypes
from storage import save_goal, get_goals, update_goal_progress

async def add_goal_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Add a new goal with target date and description."""
    try:
        # Format: /addgoal <title> <target_date> <description>
        title = context.args[0]
        target_date = context.args[1]
        description = ' '.join(context.args[2:])

        if not description:
            await update.message.reply_text(
                "Please provide goal title, target date (MM/DD/YYYY), and description!"
            )
            return

        try:
            target_date = datetime.strptime(target_date, "%m/%d/%Y")
        except ValueError:
            await update.message.reply_text("Invalid date format! Use MM/DD/YYYY")
            return

        goal = {
            'id': str(uuid.uuid4()),
            'title': title,
            'description': description,
            'target_date': target_date.isoformat(),
            'created_at': datetime.now().isoformat(),
            'progress': 0,
            'user_id': update.effective_user.id
        }

        save_goal(goal)
        await update.message.reply_text(
            f"🎯 Goal added: {title}\n"
            f"Target date: {target_date.strftime('%Y-%m-%d')}\n"
            f"Progress: {generate_progress_bar(0)} 0%"
        )

    except IndexError:
        await update.message.reply_text(
            "Usage: /addgoal <title> <target_date> <description>\n"
            "Example: /addgoal 'Learn Python' 12/31/2025 Master Python programming"
        )

async def view_goals_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """View all goals and their progress."""
    goals = get_goals(update.effective_user.id)
    if not goals:
        await update.message.reply_text("No goals found!")
        return

    goals_text = "🎯 Your Goals:\n\n"
    for goal in goals:
        progress_bar = generate_progress_bar(goal['progress'])
        target_date = datetime.fromisoformat(goal['target_date']).strftime('%Y-%m-%d')
        goals_text += (
            f"📌 {goal['title']}\n"
            f"{goal['description']}\n"
            f"Target: {target_date}\n"
            f"Progress: {progress_bar} {goal['progress']}%\n"
            f"ID: {goal['id']}\n\n"
        )

    await update.message.reply_text(goals_text)

async def update_goal_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Update goal progress."""
    try:
        # Format: /updategoal <goal_id> <progress>
        goal_id = context.args[0]
        progress = int(context.args[1])

        if not (0 <= progress <= 100):
            await update.message.reply_text("Progress must be between 0 and 100!")
            return

        update_goal_progress(update.effective_user.id, goal_id, progress)
        await update.message.reply_text(
            f"✅ Goal progress updated to {progress}%\n"
            f"{generate_progress_bar(progress)}"
        )

    except (IndexError, ValueError):
        await update.message.reply_text(
            "Usage: /updategoal <goal_id> <progress>\n"
            "Example: /updategoal abc123 75"
        )

def generate_progress_bar(progress, length=10):
    """Generate a visual progress bar."""
    filled = int(progress / 100 * length)
    return '█' * filled + '▒' * (length - filled)