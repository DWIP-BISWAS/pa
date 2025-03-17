import asyncio
from datetime import datetime
from extra_storage import (
    get_auto_messages, get_active_timers,
    get_upcoming_birthdays, get_calendar_events
)
from utils import to_ist, from_ist

class BackgroundTasks:
    def __init__(self, bot):
        self.bot = bot
        self.tasks = []
        self.running = False

    async def check_timers(self):
        """Check for expired timers and send notifications."""
        while self.running:
            try:
                now = datetime.now()
                now_ist = to_ist(now)
                # For timers, we'll check all users since they're time-sensitive
                all_timers = get_active_timers(None)  # None to get all timers
                for timer in all_timers:
                    end_time = datetime.fromisoformat(timer['end_time'])
                    end_time_ist = to_ist(end_time)
                    if end_time <= now:
                        await self.bot.send_message(
                            chat_id=timer['user_id'],
                            text=f"⏰ Timer finished!\n"
                                 f"Duration: {timer['duration']} minutes\n"
                                 f"Time: {end_time_ist.strftime('%I:%M %p')} IST"
                        )
            except Exception as e:
                print(f"Error in check_timers: {e}")
            await asyncio.sleep(60)  # Check every minute

    async def send_auto_messages(self):
        """Send scheduled auto messages."""
        while self.running:
            try:
                current_time = to_ist(datetime.now()).strftime("%H:%M")
                # For auto messages, check all users
                all_messages = get_auto_messages(None)  # None to get all messages
                for msg in all_messages:
                    if msg['time'] == current_time and msg['active']:
                        await self.bot.send_message(
                            chat_id=msg['user_id'],
                            text=f"🔄 Auto Message:\n{msg['message']}\n"
                                 f"Time: {current_time} IST"
                        )
            except Exception as e:
                print(f"Error in send_auto_messages: {e}")
            await asyncio.sleep(60)  # Check every minute

    async def check_birthdays(self):
        """Check for upcoming birthdays and send notifications."""
        while self.running:
            try:
                today = to_ist(datetime.now())
                # For birthdays, check all users
                all_birthdays = get_upcoming_birthdays(None)  # None to get all birthdays
                for birthday in all_birthdays:
                    bday_date = datetime.strptime(birthday['date'], "%m/%d")
                    bday_date = bday_date.replace(year=today.year)
                    days_until = (bday_date - today.date()).days

                    if days_until in [7, 3, 1, 0]:  # Notify 7 days, 3 days, 1 day before and on the day
                        time_str = today.strftime("%I:%M %p")
                        await self.bot.send_message(
                            chat_id=birthday['user_id'],
                            text=f"🎂 Birthday Reminder! ({time_str} IST)\n"
                                 f"{birthday['name']}'s birthday "
                                 f"{'is today' if days_until == 0 else f'is in {days_until} days'}!"
                        )
            except Exception as e:
                print(f"Error in check_birthdays: {e}")
            await asyncio.sleep(3600)  # Check every hour

    async def check_calendar_events(self):
        """Check for upcoming calendar events and send notifications."""
        while self.running:
            try:
                today = to_ist(datetime.now())
                # For calendar events, check all users
                all_events = get_calendar_events(None)  # None to get all events
                for event in all_events:
                    event_date = datetime.strptime(event['date'], "%Y-%m-%d").date()
                    days_until = (event_date - today.date()).days

                    if days_until in [7, 1, 0]:  # Notify 7 days, 1 day before and on the day
                        time_str = today.strftime("%I:%M %p")
                        await self.bot.send_message(
                            chat_id=event['user_id'],
                            text=f"📅 Calendar Reminder! ({time_str} IST)\n"
                                 f"Event: {event['event']}\n"
                                 f"{'Today!' if days_until == 0 else f'In {days_until} days'}"
                        )
            except Exception as e:
                print(f"Error in check_calendar_events: {e}")
            await asyncio.sleep(3600)  # Check every hour

    async def start(self):
        """Start all background tasks."""
        self.running = True
        self.tasks = [
            asyncio.create_task(self.check_timers()),
            asyncio.create_task(self.send_auto_messages()),
            asyncio.create_task(self.check_birthdays()),
            asyncio.create_task(self.check_calendar_events())
        ]
        print("Background tasks started successfully")

    async def stop(self):
        """Stop all background tasks."""
        self.running = False
        for task in self.tasks:
            task.cancel()
        await asyncio.gather(*self.tasks, return_exceptions=True)
        self.tasks = []
        print("Background tasks stopped successfully")

background_tasks = None

async def setup_scheduler(bot):
    """Set up all background tasks."""
    global background_tasks
    try:
        background_tasks = BackgroundTasks(bot)
        await background_tasks.start()
        print("Scheduler setup completed successfully")
    except Exception as e:
        print(f"Error setting up scheduler: {e}")

async def shutdown_scheduler():
    """Shutdown all background tasks."""
    global background_tasks
    try:
        if background_tasks:
            await background_tasks.stop()
            print("Scheduler shutdown completed successfully")
    except Exception as e:
        print(f"Error shutting down scheduler: {e}")