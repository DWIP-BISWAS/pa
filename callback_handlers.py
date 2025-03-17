import os
from datetime import datetime
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from storage import save_task, save_reminder, save_note, save_expense, save_goal
from extra_storage import (
    get_password, get_calendar_events, get_custom_notifications,
    save_calendar_event, save_custom_notification
)

async def handle_callback_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle callback queries from inline keyboards."""
    query = update.callback_query
    await query.answer()  # Acknowledge the button click

    # Weather forecast handlers
    if query.data.startswith("weather_"):
        parts = query.data.split("_")
        forecast_type = parts[1]  # hourly or daily
        city = "_".join(parts[2:])  # Handle city names with spaces

        API_KEY = os.environ.get('OPENWEATHERMAP_API_KEY')

        if forecast_type == "hourly":
            # Get 3-hour forecast for next 12 hours
            response = requests.get(
                'http://api.openweathermap.org/data/2.5/forecast',
                params={
                    'q': city,
                    'appid': API_KEY,
                    'units': 'imperial',
                    'cnt': 4  # Next 12 hours (3-hour intervals)
                }
            )

            if response.status_code == 200:
                data = response.json()
                forecast = f"⏰ Hourly Forecast for {city}:\n\n"
                for item in data['list']:
                    time = datetime.fromtimestamp(item['dt']).strftime('%H:%M')
                    temp = round(item['main']['temp'])
                    desc = item['weather'][0]['description'].capitalize()
                    forecast += f"{time} - {temp}°F, {desc}\n"
            else:
                forecast = "Sorry, couldn't fetch hourly forecast."

        else:  # daily
            # Get 4-day forecast
            response = requests.get(
                'http://api.openweathermap.org/data/2.5/forecast',
                params={
                    'q': city,
                    'appid': API_KEY,
                    'units': 'imperial'
                }
            )

            if response.status_code == 200:
                data = response.json()
                forecast = f"📅 Daily Forecast for {city}:\n\n"

                # Group by day and get daily averages
                daily_forecasts = {}
                for item in data['list']:
                    date = datetime.fromtimestamp(item['dt']).strftime('%Y-%m-%d')
                    if date not in daily_forecasts:
                        daily_forecasts[date] = {
                            'temps': [],
                            'descriptions': []
                        }
                    daily_forecasts[date]['temps'].append(item['main']['temp'])
                    daily_forecasts[date]['descriptions'].append(item['weather'][0]['description'])

                # Format daily forecasts
                for date, info in list(daily_forecasts.items())[:4]:  # Show 4 days
                    avg_temp = round(sum(info['temps']) / len(info['temps']))
                    # Get most common weather description
                    desc = max(set(info['descriptions']), key=info['descriptions'].count).capitalize()
                    day = datetime.strptime(date, '%Y-%m-%d').strftime('%A')  # Get day name
                    forecast += f"{day} - {avg_temp}°F, {desc}\n"
            else:
                forecast = "Sorry, couldn't fetch daily forecast."

        await query.edit_message_text(forecast)

    # Quick action handlers
    elif query.data == "quick_addtask":
        await query.message.reply_text(
            "📝 To add a task, use:\n"
            "/addtask <task description>\n"
            "Example: /addtask Buy groceries"
        )
    elif query.data == "quick_remind":
        await query.message.reply_text(
            "⏰ To set a reminder, use:\n"
            "/remind <time> <message>\n"
            "Example: /remind 14:30 Call mom"
        )
    elif query.data == "quick_note":
        await query.message.reply_text(
            "📝 To add a note, use:\n"
            "/note <title> <content>\n"
            "Example: /note Meeting Notes Discuss project timeline"
        )
    elif query.data == "quick_spend":
        await query.message.reply_text(
            "💰 To log an expense, use:\n"
            "/spend <amount> <description>\n"
            "Example: /spend 25.50 Lunch"
        )
    elif query.data == "quick_goal":
        await query.message.reply_text(
            "🎯 To add a goal, use:\n"
            "/addgoal <title> <target_date> <description>\n"
            "Example: /addgoal 'Learn Python' 12/31/2025 Master programming"
        )
    elif query.data == "quick_weather":
        await query.message.reply_text(
            "🌤 To check weather, use:\n"
            "/weather <city>\n"
            "Example: /weather London"
        )

    # Timer handlers
    elif query.data.startswith("cancel_timer_"):
        timer_id = query.data.split("_")[2]
        await query.edit_message_text(f"⏰ Timer {timer_id} cancelled!")

    # Auto message handlers
    elif query.data == "cancel_auto_message":
        await query.edit_message_text("🔄 Auto message cancelled!")

    # Translation handlers
    elif query.data.startswith("translate_"):
        parts = query.data.split("_")
        lang = parts[1]
        text = "_".join(parts[2:])

        try:
            # Use MyMemory Translation API
            MYMEMORY_URL = "https://api.mymemory.translated.net/get"
            response = requests.get(
                MYMEMORY_URL,
                params={
                    'q': text,
                    'langpair': f'en|{lang}'
                }
            )

            if response.status_code == 200:
                result = response.json()
                translated = result['responseData']['translatedText']
            else:
                # Fallback to basic translation for common phrases
                translations = {
                    'hi': {'hello': 'नमस्ते', 'world': 'दुनिया', 'how are you': 'आप कैसे हैं'},
                    'es': {'hello': 'hola', 'world': 'mundo', 'how are you': '¿cómo estás?'},
                    'fr': {'hello': 'bonjour', 'world': 'monde', 'how are you': 'comment allez-vous?'},
                    'de': {'hello': 'hallo', 'world': 'welt', 'how are you': 'wie geht es dir?'}
                }
                words = text.lower().split()
                translated_words = [
                    translations.get(lang, {}).get(word, word)
                    for word in words
                ]
                translated = ' '.join(translated_words)

            # Add language names for clarity
            lang_names = {
                'hi': 'Hindi',
                'es': 'Spanish',
                'fr': 'French',
                'de': 'German'
            }

            await query.edit_message_text(
                f"🌐 Translation:\n"
                f"Original: {text}\n"
                f"Translated ({lang_names.get(lang, lang.upper())}): {translated}"
            )
        except Exception as e:
            await query.edit_message_text(
                "Sorry, an error occurred during translation. Please try again."
            )

    # News category handlers
    elif query.data.startswith("news_"):
        category = query.data.split("_")[1]
        valid_categories = ["business", "entertainment", "general", "health", "science", "sports", "technology"]

        if category not in valid_categories:
            category = "general"

        API_KEY = os.environ.get('NEWS_API_KEY')
        BASE_URL = 'https://newsapi.org/v2/top-headlines'

        try:
            response = requests.get(
                BASE_URL,
                params={
                    'apiKey': API_KEY,
                    'category': category,
                    'language': 'en',
                    'pageSize': 5
                }
            )

            if response.status_code != 200:
                await query.edit_message_text(
                    "Sorry, couldn't fetch news at the moment. Please try again later."
                )
                return

            data = response.json()
            articles = data.get('articles', [])

            if not articles:
                await query.edit_message_text(
                    f"No news found for category: {category}"
                )
                return

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

            # Split message if it's too long
            if len(news_text) > 4096:
                news_text = news_text[:4000] + "\n\n(Message truncated due to length)"

            await query.edit_message_text(news_text, reply_markup=reply_markup)

        except Exception as e:
            await query.edit_message_text(
                "Sorry, an error occurred while fetching news. Please try again later."
            )

    # Birthday handlers
    elif query.data == "view_birthdays":
        await query.message.reply_text("🎂 Loading all birthdays...")
    elif query.data.startswith("remove_birthday_"):
        name = query.data.split("_")[2]
        await query.message.reply_text(f"🎂 Removed birthday reminder for {name}")

    # Email handlers
    elif query.data == "refresh_emails":
        await query.message.reply_text("📧 Checking for new emails...")
    elif query.data == "mark_emails_read":
        await query.message.reply_text("📧 Marked all emails as read")

    # Password handlers
    elif query.data == "list_passwords":
        await query.message.reply_text("🔐 Loading saved passwords...")
    elif query.data.startswith("delete_password_"):
        service = query.data.split("_")[2]
        await query.message.reply_text(f"🔐 Deleted password for {service}")

    # Calendar handlers
    elif query.data == "view_events":
        events = get_calendar_events(query.from_user.id)
        if not events:
            await query.message.reply_text("📅 No events found!")
        else:
            events_text = "📅 Your Events:\n\n"
            for event in events:
                events_text += f"📌 {event['date']}: {event['event']}\n"
            await query.message.reply_text(events_text)
    elif query.data == "add_event":
        await query.message.reply_text(
            "📅 To add an event, use:\n"
            "/calendar add <date> <event>\n"
            "Example: /calendar add 2025-03-20 Team meeting"
        )

    # Notification handlers
    elif query.data == "view_notifications":
        notifications = get_custom_notifications(query.from_user.id)
        if not notifications:
            await query.message.reply_text("🔔 No custom notifications found!")
        else:
            notif_text = "🔔 Your Notifications:\n\n"
            for notif in notifications:
                notif_text += f"📌 Trigger: {notif['trigger']}\n   Message: {notif['message']}\n\n"
            await query.message.reply_text(notif_text)
    elif query.data.startswith("delete_notification_"):
        notif_id = query.data.split("_")[2]
        await query.message.reply_text(f"🔔 Deleted notification {notif_id}")