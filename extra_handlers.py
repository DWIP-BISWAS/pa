from datetime import datetime, timedelta
import uuid
import json
import os
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from storage import save_reminder
from extra_storage import (
    save_auto_message, get_auto_messages, save_birthday, get_upcoming_birthdays,
    save_timer, get_active_timers, save_calendar_event, get_calendar_events,
    save_password, get_password, save_custom_notification, get_custom_notifications
)
from encryption import password_encryption
from utils import to_ist, from_ist

async def weather_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Get weather information for a location."""
    try:
        city = ' '.join(context.args)
        if not city:
            await update.message.reply_text("Please provide a city name!\nUsage: /weather <city>")
            return

        API_KEY = os.environ.get('OPENWEATHERMAP_API_KEY')
        BASE_URL = 'http://api.openweathermap.org/data/2.5/weather'

        # Make API request with metric units
        response = requests.get(
            BASE_URL,
            params={
                'q': city,
                'appid': API_KEY,
                'units': 'metric'  # Use Celsius
            }
        )

        if response.status_code != 200:
            await update.message.reply_text(
                "Sorry, couldn't fetch weather data. Please check the city name and try again."
            )
            return

        data = response.json()

        # Convert UTC to IST (UTC+5:30)
        current_time = datetime.fromtimestamp(data['dt']) + timedelta(hours=5, minutes=30)

        weather_data = {
            'temp': round(data['main']['temp']),
            'feels_like': round(data['main']['feels_like']),
            'condition': data['weather'][0]['main'],
            'description': data['weather'][0]['description'].capitalize(),
            'humidity': data['main']['humidity'],
            'wind': round(data['wind']['speed'] * 3.6),  # Convert m/s to km/h
            'pressure': data['main']['pressure'],
            'time': current_time.strftime('%I:%M %p')  # 12-hour format
        }

        # Create inline keyboard for hourly/daily forecast
        keyboard = [
            [
                InlineKeyboardButton(
                    "Hourly Forecast",
                    callback_data=f"weather_hourly_{city}"
                ),
                InlineKeyboardButton(
                    "Daily Forecast",
                    callback_data=f"weather_daily_{city}"
                )
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            f"🌤 Weather in {city} at {weather_data['time']} (IST):\n"
            f"Temperature: {weather_data['temp']}°C\n"
            f"Feels like: {weather_data['feels_like']}°C\n"
            f"Condition: {weather_data['description']}\n"
            f"Humidity: {weather_data['humidity']}%\n"
            f"Wind Speed: {weather_data['wind']} km/h\n"
            f"Pressure: {weather_data['pressure']} hPa",
            reply_markup=reply_markup
        )

    except Exception as e:
        await update.message.reply_text(
            "An error occurred while fetching weather data. Please try again later."
        )

async def auto_message_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Set up automatic messages."""
    try:
        time = context.args[0]
        message = ' '.join(context.args[1:])

        if not message:
            await update.message.reply_text(
                "Please provide time and message!\n"
                "Usage: /automessage HH:MM Your message here"
            )
            return

        # Parse the time in IST
        message_time = datetime.strptime(time, "%H:%M").time()
        today = to_ist(datetime.now()).date()
        message_datetime = datetime.combine(today, message_time)

        # If time has passed today, schedule for tomorrow
        if message_datetime <= to_ist(datetime.now()):
            message_datetime = datetime.combine(today + timedelta(days=1), message_time)

        # Save auto message configuration (time stored in IST)
        save_auto_message({
            'id': str(uuid.uuid4()),
            'time': message_datetime.strftime("%H:%M"),
            'message': message,
            'user_id': update.effective_user.id,
            'active': True
        })

        # Also create a reminder for the first occurrence (convert to UTC for storage)
        save_reminder({
            'time': from_ist(message_datetime).isoformat(),
            'message': f"🔄 Auto Message: {message}",
            'user_id': update.effective_user.id
        })

        keyboard = [[
            InlineKeyboardButton("Cancel Auto Message", callback_data="cancel_auto_message")
        ]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            f"⏰ Auto message set for {time} IST\n"
            f"Message: {message}\n"
            "It will be sent daily at this time.",
            reply_markup=reply_markup
        )

    except ValueError:
        await update.message.reply_text(
            "Usage: /automessage HH:MM Your message here\n"
            "Time must be in 24-hour format (e.g., 14:30)"
        )
    except IndexError:
        await update.message.reply_text(
            "Usage: /automessage HH:MM Your message here"
        )

async def timer_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Set a timer."""
    try:
        minutes = int(context.args[0])
        if minutes <= 0:
            await update.message.reply_text("Please provide a positive number of minutes!")
            return

        # Create timer end time in IST
        timer_end = to_ist(datetime.now() + timedelta(minutes=minutes))

        # Save timer data (convert back to UTC for storage)
        timer_id = str(uuid.uuid4())
        save_timer({
            'id': timer_id,
            'end_time': from_ist(timer_end).isoformat(),
            'duration': minutes,
            'user_id': update.effective_user.id
        })

        # Create a reminder for when timer ends
        save_reminder({
            'time': from_ist(timer_end).isoformat(),
            'message': "⏰ Timer finished!",
            'user_id': update.effective_user.id
        })

        # Create cancel button
        keyboard = [[
            InlineKeyboardButton("Cancel Timer", callback_data=f"cancel_timer_{timer_id}")
        ]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            f"⏲ Timer set for {minutes} minutes!\n"
            f"Will notify you at: {timer_end.strftime('%I:%M %p')} IST",
            reply_markup=reply_markup
        )

    except (IndexError, ValueError):
        await update.message.reply_text("Usage: /timer <minutes>")

async def translate_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Translate text to a specified language."""
    try:
        target_lang = context.args[0].lower()
        text = ' '.join(context.args[1:])

        if not text:
            await update.message.reply_text(
                "Please provide target language and text!\n"
                "Usage: /translate <lang> <text>\n"
                "Example: /translate hi Hello, how are you?"
            )
            return

        # Use MyMemory Translation API
        MYMEMORY_URL = "https://api.mymemory.translated.net/get"
        response = requests.get(
            MYMEMORY_URL,
            params={
                'q': text,
                'langpair': f'en|{target_lang}'
            }
        )

        if response.status_code == 200:
            result = response.json()
            translated_text = result['responseData']['translatedText']

            # Create language selection buttons
            keyboard = [
                [InlineKeyboardButton(f"Translate to {lang.upper()}", callback_data=f"translate_{lang}_{text}")
                 for lang in ['hi', 'es', 'fr', 'de']]  # Added Hindi (hi)
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            # Add language names for clarity
            lang_names = {
                'hi': 'Hindi',
                'es': 'Spanish',
                'fr': 'French',
                'de': 'German'
            }

            await update.message.reply_text(
                f"🌐 Translation:\n"
                f"Original: {text}\n"
                f"Translated to {lang_names.get(target_lang, target_lang.upper())}: {translated_text}",
                reply_markup=reply_markup
            )
        else:
            await update.message.reply_text(
                "Sorry, translation service is currently unavailable. Please try again later."
            )

    except IndexError:
        await update.message.reply_text(
            "Usage: /translate <lang> <text>\n"
            "Example: /translate hi Hello, how are you?\n\n"
            "Supported languages:\n"
            "hi - Hindi\n"
            "es - Spanish\n"
            "fr - French\n"
            "de - German"
        )
    except Exception as e:
        await update.message.reply_text(
            "Sorry, an error occurred during translation. Please try again later."
        )

async def news_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Get latest news."""
    try:
        category = context.args[0].lower() if context.args else "general"
        valid_categories = ["business", "entertainment", "general", "health", "science", "sports", "technology"]

        if category not in valid_categories:
            category = "general"

        API_KEY = os.environ.get('NEWS_API_KEY')
        BASE_URL = 'https://newsapi.org/v2/top-headlines'

        # Make API request with country parameter
        response = requests.get(
            BASE_URL,
            params={
                'apiKey': API_KEY,
                'category': category,
                'country': 'us',  # Added country parameter
                'language': 'en',
                'pageSize': 5  # Get 5 articles
            }
        )

        if response.status_code != 200:
            # Fallback to simulated news if API fails
            simulated_news = {
                "general": [
                    {"title": "Daily Update", "description": "Latest events and updates from around the world"},
                    {"title": "Community News", "description": "Local developments and announcements"}
                ],
                "technology": [
                    {"title": "Tech Innovation", "description": "Latest technological breakthroughs and updates"},
                    {"title": "Digital Trends", "description": "Current trends in the digital world"}
                ]
            }

            articles = simulated_news.get(category, simulated_news["general"])
            news_text = f"📰 Latest {category.title()} News (Offline Mode):\n\n"
            for article in articles:
                news_text += f"📌 {article['title']}\n{article['description']}\n\n"
        else:
            data = response.json()
            articles = data.get('articles', [])

            if not articles:
                await update.message.reply_text(
                    f"No news found for category: {category}"
                )
                return

            news_text = f"📰 Latest {category.title()} News:\n\n"
            for article in articles:
                title = article.get('title', 'No title')
                desc = article.get('description', 'No description available')
                source = article.get('source', {}).get('name', 'Unknown source')
                url = article.get('url', '')

                news_text += (
                    f"📌 {title}\n"
                    f"Source: {source}\n"
                    f"{desc}\n"
                    f"Read more: {url}\n\n"
                )

        # Create category selection buttons
        keyboard = []
        for i in range(0, len(valid_categories), 3):
            row = [
                InlineKeyboardButton(
                    cat.title(),
                    callback_data=f"news_{cat}"
                ) for cat in valid_categories[i:i+3]
            ]
            keyboard.append(row)
        reply_markup = InlineKeyboardMarkup(keyboard)

        # Split message if it's too long
        if len(news_text) > 4096:
            news_text = news_text[:4000] + "\n\n(Message truncated due to length)"

        await update.message.reply_text(news_text, reply_markup=reply_markup)

    except Exception as e:
        await update.message.reply_text(
            "Usage: /news [category]\n"
            "Available categories: business, entertainment, general, health, science, sports, technology"
        )

async def birthday_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Set a birthday reminder."""
    try:
        name = context.args[0]
        date = context.args[1]

        # Validate date format
        try:
            birthday_date = datetime.strptime(date, "%m/%d")
        except ValueError:
            await update.message.reply_text(
                "Invalid date format!\n"
                "Please use MM/DD format (e.g., 12/25)"
            )
            return

        save_birthday({
            'name': name,
            'date': date,
            'user_id': update.effective_user.id
        })

        # Get upcoming birthdays
        upcoming = get_upcoming_birthdays(update.effective_user.id)

        # Create response message with IST time
        current_time = to_ist(datetime.now())
        response = f"🎂 Birthday reminder set for {name} on {date} ({current_time.strftime('%I:%M %p')} IST)"

        if upcoming:
            response += "\n\n📅 Upcoming birthdays:\n"
            for bday in upcoming:
                bday_date = datetime.strptime(bday['date'], "%m/%d")
                bday_this_year = bday_date.replace(year=current_time.year)
                if bday_this_year < current_time:
                    bday_this_year = bday_date.replace(year=current_time.year + 1)
                days_until = (bday_this_year - current_time.date()).days

                response += f"🎈 {bday['name']} - {bday['date']} (in {days_until} days)\n"

        # Add buttons for managing birthdays
        keyboard = [
            [InlineKeyboardButton("View All Birthdays", callback_data="view_birthdays")],
            [InlineKeyboardButton("Remove Birthday", callback_data=f"remove_birthday_{name}")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(response, reply_markup=reply_markup)

    except IndexError:
        await update.message.reply_text(
            "Usage: /birthday <name> <MM/DD>\n"
            "Example: /birthday John 12/25"
        )

async def email_check_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Check unread emails."""
    # Simulated email data
    emails = [
        {"subject": "Important Update", "from": "team@example.com", "time": "10:30 AM"},
        {"subject": "Meeting Tomorrow", "from": "manager@example.com", "time": "11:15 AM"},
        {"subject": "Project Status", "from": "client@example.com", "time": "12:45 PM"}
    ]

    # Create email management buttons
    keyboard = [
        [InlineKeyboardButton("Check New Emails", callback_data="refresh_emails")],
        [InlineKeyboardButton("Mark All Read", callback_data="mark_emails_read")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    email_text = "📧 Your Recent Emails:\n\n"
    for email in emails:
        email_text += (
            f"📩 From: {email['from']}\n"
            f"Subject: {email['subject']}\n"
            f"Time: {email['time']}\n\n"
        )

    await update.message.reply_text(email_text, reply_markup=reply_markup)

async def password_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Store and manage passwords securely."""
    try:
        if not context.args:
            raise IndexError

        action = context.args[0].lower()
        if action == "store":
            if len(context.args) < 3:
                raise IndexError

            service = context.args[1]
            password = ' '.join(context.args[2:])  # Allow spaces in passwords

            # Save encrypted password with IST timestamp
            save_password({
                'service': service,
                'password': password,  # encryption is handled in save_password
                'user_id': update.effective_user.id,
                'created_at': to_ist(datetime.now()).isoformat()
            })

            keyboard = [[
                InlineKeyboardButton("View Stored Passwords", callback_data="list_passwords")
            ]]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await update.message.reply_text(
                f"🔐 Password securely encrypted and stored for {service}",
                reply_markup=reply_markup
            )

        elif action == "get":
            if len(context.args) < 2:
                raise IndexError

            service = context.args[1]
            password_data = get_password(update.effective_user.id, service)

            if password_data and password_data.get('password'):
                # Send initial message
                await update.message.reply_text(
                    f"🔐 Password for {service}:\n"
                    "I'll send it in a separate message that will be deleted in 30 seconds for security."
                )

                # Send password in separate message that will be deleted
                keyboard = [[
                    InlineKeyboardButton("Delete Password", callback_data=f"delete_password_{service}")
                ]]
                reply_markup = InlineKeyboardMarkup(keyboard)

                message = await update.message.reply_text(
                    f"🔑 Password: {password_data['password']}\n"
                    "(This message will be deleted in 30 seconds for security)",
                    reply_markup=reply_markup
                )

                # Schedule message deletion after 30 seconds
                async def delete_message(context: ContextTypes.DEFAULT_TYPE):
                    try:
                        await message.delete()
                    except Exception:
                        pass  # Message might already be deleted

                context.job_queue.run_once(
                    delete_message,
                    30,
                    data=None,
                    name=f"delete_pwd_msg_{update.effective_user.id}_{service}"
                )
            else:
                await update.message.reply_text(
                    f"❌ No password found for {service} or error decrypting password."
                )

        else:
            raise IndexError

    except IndexError:
        await update.message.reply_text(
            "Usage:\n"
            "/password store <service> <password> - Store a password\n"
            "/password get <service> - Retrieve a password\n\n"
            "Example:\n"
            "/password store gmail mySecurePass123\n"
            "/password get gmail"
        )
    except Exception as e:
        await update.message.reply_text(
            "❌ An error occurred while processing your request.\n"
            "Please try again or contact support if the issue persists."
        )

async def calendar_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Manage calendar events."""
    try:
        action = context.args[0].lower()
        if action == "add":
            date = context.args[1]
            event = ' '.join(context.args[2:])

            # Add event with IST timestamp
            save_calendar_event({
                'date': date,
                'event': event,
                'user_id': update.effective_user.id,
                'created_at': to_ist(datetime.now()).isoformat()
            })

            keyboard = [[
                InlineKeyboardButton("View All Events", callback_data="view_events"),
                InlineKeyboardButton("Add Another Event", callback_data="add_event")
            ]]
            reply_markup = InlineKeyboardMarkup(keyboard)

            current_time = to_ist(datetime.now())
            await update.message.reply_text(
                f"📅 Event added at {current_time.strftime('%I:%M %p')} IST:\n"
                f"Date: {date}\n"
                f"Event: {event}",
                reply_markup=reply_markup
            )

        elif action == "list":
            events = get_calendar_events(update.effective_user.id)
            if not events:
                keyboard = [[
                    InlineKeyboardButton("Add Event", callback_data="add_event")
                ]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await update.message.reply_text(
                    "No events found!",
                    reply_markup=reply_markup
                )
                return

            events_text = "📅 Your Upcoming Events:\n\n"
            current_time = to_ist(datetime.now())
            for i, event in enumerate(events, 1):
                # Convert event date to datetime for comparison
                event_date = datetime.strptime(event['date'], "%Y-%m-%d")
                days_until = (event_date.date() - current_time.date()).days
                events_text += (
                    f"{i}. 📌 {event['date']}: {event['event']}\n"
                    f"   {'Today!' if days_until == 0 else f'In {days_until} days'}\n"
                )

            keyboard = [
                [InlineKeyboardButton("Add Event", callback_data="add_event")],
                [InlineKeyboardButton("Delete Event", callback_data="delete_event")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await update.message.reply_text(events_text, reply_markup=reply_markup)
        else:
            raise IndexError
    except IndexError:
        await update.message.reply_text(
            "Usage:\n"
            "/calendar add <date> <event> - Add an event\n"
            "/calendar list - List upcoming events\n\n"
            "Date format: YYYY-MM-DD\n"
            "Example: /calendar add 2025-12-25 Christmas Celebration"
        )

async def custom_notification_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Set custom notifications."""
    try:
        trigger = context.args[0]
        message = ' '.join(context.args[1:])
        if not message:
            raise IndexError

        notification_id = str(uuid.uuid4())
        save_custom_notification({
            'id': notification_id,
            'trigger': trigger,
            'message': message,
            'user_id': update.effective_user.id,
            'created_at': datetime.now().isoformat(),
        })

        keyboard = [
            [InlineKeyboardButton("View All Notifications", callback_data="view_notifications")],
            [InlineKeyboardButton("Delete Notification", callback_data=f"delete_notification_{notification_id}")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            f"🔔 Custom notification set!\n"
            f"Trigger: {trigger}\n"
            f"Message: {message}\n\n"
            f"You will be notified when the trigger condition is met.",
            reply_markup=reply_markup
        )
    except IndexError:
        await update.message.reply_text(
            "Usage: /notify <trigger> <message>\n"
            "Example: /notify daily Good morning!"
        )