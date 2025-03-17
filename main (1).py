
import os
import logging
import asyncio
import json
import base64
from datetime import datetime
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, ContextTypes, MessageHandler, 
    filters, CallbackQueryHandler
)

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Storage Helper Functions
def load_json(filename):
    try:
        os.makedirs('data', exist_ok=True)
        filepath = f'data/{filename}.json'
        if not os.path.exists(filepath):
            return []
        with open(filepath, 'r') as f:
            return json.load(f)
    except:
        return []

def save_json(data, filename):
    os.makedirs('data', exist_ok=True)
    with open(f'data/{filename}.json', 'w') as f:
        json.dump(data, f, indent=2)

# Encryption Helper
class PasswordEncryption:
    def __init__(self):
        self.key = self._get_or_create_key()
        self.fernet = Fernet(self.key)

    def _get_or_create_key(self):
        key = os.getenv('ENCRYPTION_KEY')
        if not key:
            salt = os.urandom(16)
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
            )
            key = base64.urlsafe_b64encode(kdf.derive(os.urandom(32)))
        else:
            key = key.encode()
        return key

    def encrypt(self, text):
        return self.fernet.encrypt(text.encode()).decode()

    def decrypt(self, encrypted_text):
        try:
            return self.fernet.decrypt(encrypted_text.encode()).decode()
        except:
            return None

# Command Handlers
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
        "/updategoal - Update goal progress"
    )
    await update.message.reply_text(welcome_message)

async def add_task_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = ' '.join(context.args)
    if not text:
        await update.message.reply_text("Please provide a task description!")
        return
    
    tasks = load_json('tasks')
    tasks.append({
        'user_id': user_id,
        'task': text,
        'completed': False,
        'created_at': datetime.now().isoformat()
    })
    save_json(tasks, 'tasks')
    await update.message.reply_text("✅ Task added successfully!")

async def todo_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    tasks = load_json('tasks')
    user_tasks = [t for t in tasks if t['user_id'] == user_id and not t['completed']]
    
    if not user_tasks:
        await update.message.reply_text("No pending tasks!")
        return
    
    response = "📋 Your To-Do List:\n\n"
    for i, task in enumerate(user_tasks, 1):
        response += f"{i}. {task['task']}\n"
    
    await update.message.reply_text(response)

# Error Handler
async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.warning('Update "%s" caused error "%s"', update, context.error)
    if update and update.effective_message:
        await update.effective_message.reply_text(
            "Sorry, an error occurred. Please try again."
        )

# Main Functions
async def setup_application():
    token = os.getenv("TELEGRAM_TOKEN")
    if not token:
        logger.error("No telegram token provided!")
        return None

    application = Application.builder().token(token).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("addtask", add_task_command))
    application.add_handler(CommandHandler("todo", todo_command))
    application.add_error_handler(error_handler)
    
    return application

async def main():
    try:
        application = await setup_application()
        if not application:
            return

        logger.info("Starting bot...")
        await application.run_polling(allowed_updates=Update.ALL_TYPES)

    except Exception as e:
        logger.error(f"Bot crashed: {e}")

if __name__ == '__main__':
    asyncio.run(main())
