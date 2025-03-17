import os
import logging
import asyncio
import nest_asyncio
from telegram import Update
from telegram.ext import (
    Application, CommandHandler, ContextTypes, MessageHandler, 
    filters, CallbackQueryHandler
)

from handlers import (
    start_command, help_command, remind_command, add_task_command, todo_command,
    spend_command, note_command, view_notes_command, done_command,
    view_reminders_command, edit_task_command, delete_task_command,
    edit_reminder_command, delete_reminder_command
)
from goal_handlers import (
    add_goal_command, view_goals_command, update_goal_command
)
from extra_handlers import (
    weather_command, auto_message_command, timer_command,
    translate_command, news_command, birthday_command,
    email_check_command, password_command, calendar_command,
    custom_notification_command
)
from callback_handlers import handle_callback_query
from scheduler import setup_scheduler

# Apply nest_asyncio to handle nested event loops
nest_asyncio.apply()

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.DEBUG
)
logger = logging.getLogger(__name__)

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, context.error)
    if update and update.effective_message:
        await update.effective_message.reply_text(
            "Sorry, an error occurred while processing your command. Please try again."
        )

async def handle_dynamic_commands(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle dynamic edit/delete commands."""
    message_text = update.message.text
    if message_text.startswith('/edit_task_'):
        await edit_task_command(update, context)
    elif message_text.startswith('/delete_task_'):
        await delete_task_command(update, context)
    elif message_text.startswith('/edit_reminder_'):
        await edit_reminder_command(update, context)
    elif message_text.startswith('/delete_reminder_'):
        await delete_reminder_command(update, context)

async def setup_application():
    """Initialize and configure the application."""
    token = os.getenv("TELEGRAM_TOKEN")
    if not token:
        logger.error("No token provided!")
        return None

    # Create the Application
    application = Application.builder().token(token).build()
    logger.info("Application created successfully")

    # Add basic command handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("remind", remind_command))
    application.add_handler(CommandHandler("addtask", add_task_command))
    application.add_handler(CommandHandler("todo", todo_command))
    application.add_handler(CommandHandler("done", done_command))
    application.add_handler(CommandHandler("reminders", view_reminders_command))
    application.add_handler(CommandHandler("spend", spend_command))
    application.add_handler(CommandHandler("note", note_command))
    application.add_handler(CommandHandler("viewnotes", view_notes_command))

    # Add goal handlers
    application.add_handler(CommandHandler("addgoal", add_goal_command))
    application.add_handler(CommandHandler("goals", view_goals_command))
    application.add_handler(CommandHandler("updategoal", update_goal_command))

    # Add new feature handlers
    application.add_handler(CommandHandler("weather", weather_command))
    application.add_handler(CommandHandler("automessage", auto_message_command))
    application.add_handler(CommandHandler("timer", timer_command))
    application.add_handler(CommandHandler("translate", translate_command))
    application.add_handler(CommandHandler("news", news_command))
    application.add_handler(CommandHandler("birthday", birthday_command))
    application.add_handler(CommandHandler("email", email_check_command))
    application.add_handler(CommandHandler("password", password_command))
    application.add_handler(CommandHandler("calendar", calendar_command))
    application.add_handler(CommandHandler("notify", custom_notification_command))

    # Add handler for dynamic edit/delete commands
    application.add_handler(MessageHandler(
        filters.COMMAND & (
            filters.Regex('^/edit_task_') |
            filters.Regex('^/delete_task_') |
            filters.Regex('^/edit_reminder_') |
            filters.Regex('^/delete_reminder_')
        ),
        handle_dynamic_commands
    ))

    # Add callback query handler for inline buttons
    application.add_handler(CallbackQueryHandler(handle_callback_query))

    # Add error handler
    application.add_error_handler(error_handler)

    return application

async def run_bot():
    """Run the bot."""
    try:
        # Initialize application
        application = await setup_application()
        if not application:
            return

        # Initialize background tasks
        await setup_scheduler(application.bot)
        logger.info("Background tasks initialized")

        # Start polling
        logger.info("Starting bot polling...")
        await application.run_polling(allowed_updates=Update.ALL_TYPES)

    except Exception as e:
        logger.error(f"Bot crashed: {e}")

if __name__ == '__main__':
    asyncio.run(run_bot())