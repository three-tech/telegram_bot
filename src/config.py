import os

# Get the project root directory (parent of src)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

BOT_TOKEN = "8346883674:AAGCt5ECGqc0gATtySU5L7qfLkB72COTRxs"
DB_NAME = os.path.join(BASE_DIR, "telegram_bot.db")
