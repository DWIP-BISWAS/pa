import os
import logging
import asyncio
import json
import base64
import requests
import random
import string
from datetime import datetime, timedelta
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (Application, CommandHandler, ContextTypes,
                         MessageHandler, filters, CallbackQueryHandler)

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO)
logger = logging.getLogger(__name__)

# Required Environment Variables - Load from Railway
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
ENCRYPTION_KEY = os.getenv('ENCRYPTION_KEY')

# API Keys
OPENWEATHER_API_KEY = os.getenv('OPENWEATHER_API_KEY')
NEWS_API_KEY = os.getenv('NEWS_API_KEY')
ALPHA_VANTAGE_API_KEY = os.getenv('ALPHA_VANTAGE_API_KEY')
TMDB_API_KEY = os.getenv('TMDB_API_KEY')
RAWG_API_KEY = os.getenv('RAWG_API_KEY')
GIPHY_API_KEY = os.getenv('GIPHY_API_KEY')
WOLFRAM_ALPHA_KEY = os.getenv('WOLFRAM_ALPHA_KEY')
UNSPLASH_API_KEY = os.getenv('UNSPLASH_API_KEY')
SPOONACULAR_API_KEY = os.getenv('SPOONACULAR_API_KEY')
EDAMAM_APP_ID = os.getenv('EDAMAM_APP_ID')
EDAMAM_APP_KEY = os.getenv('EDAMAM_APP_KEY')
IPSTACK_API_KEY = os.getenv('IPSTACK_API_KEY')
VIRUSTOTAL_API_KEY = os.getenv('VIRUSTOTAL_API_KEY')

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

# Password Encryption
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

password_encryption = PasswordEncryption()

# Command Handlers
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_message = (
        "👋 Welcome to Your All-in-One Assistant Bot!\n\n"
        "Here's what I can help you with:\n\n"
        "📋 Task Management:\n"
        "/addtask - Add a new task\n"
        "/todo - View your to-do list\n"
        "/done - Mark a task as completed\n\n"
        "🔐 Password Management:\n"
        "/addpass - Store a new password\n"
        "/getpass - Retrieve a password\n"
        "/listpass - List stored services\n"
        "/genpass - Generate secure password\n\n"
        "📰 Information Services:\n"
        "/weather - Get weather info\n"
        "/news - Get latest news\n"
        "/crypto - Get crypto price\n"
        "/quote - Random quote\n"
        "/joke - Random joke\n"
        "/fact - Random fact\n\n"
        "🎬 Entertainment:\n"
        "/movie - Get movie information\n"
        "/game - Get game information\n"
        "/image - Get random/specific image\n\n"
        "📝 Notes & Reminders:\n"
        "/note - Save a note\n"
        "/notes - List all notes\n"
        "/remind - Set a reminder\n\n"
        "Type /help for more commands!")

    keyboard = [
        [
            InlineKeyboardButton("📋 Add Task", callback_data="quick_addtask"),
            InlineKeyboardButton("⏰ Set Reminder", callback_data="quick_remind")
        ],
        [
            InlineKeyboardButton("📝 Add Note", callback_data="quick_note"),
            InlineKeyboardButton("🌤 Weather", callback_data="quick_weather")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(welcome_message, reply_markup=reply_markup)

# Error Handler
async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.warning('Update "%s" caused error "%s"', update, context.error)
    if update and update.effective_message:
        await update.effective_message.reply_text(
            "❌ Sorry, an error occurred. Please try again.")

# Main Application Setup
async def setup_application():
    if not TELEGRAM_TOKEN:
        logger.error("No telegram token provided!")
        return None

    application = Application.builder().token(TELEGRAM_TOKEN).build()

    # Add command handlers
    application.add_handler(CommandHandler("start", start_command))
    # Add all other command handlers here


    # Add error handler
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