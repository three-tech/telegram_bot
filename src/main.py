import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters
from src.config import BOT_TOKEN
from src.database import init_db
from src.logger import setup_logging
from src.handlers.start import start
from src.handlers.message import message_handler

# Setup logging
setup_logging()

def main():
    """Main function to start the bot."""
    # Initialize database
    init_db()
    
    # Build the application
    application = ApplicationBuilder().token(BOT_TOKEN).build()
    
    # Add handlers
    start_handler = CommandHandler('start', start)
    echo_handler = MessageHandler(filters.TEXT | filters.PHOTO | filters.VIDEO & (~filters.COMMAND), message_handler)
    
    application.add_handler(start_handler)
    application.add_handler(echo_handler)
    
    # Run the bot
    print("Bot is running...")
    application.run_polling()

if __name__ == '__main__':
    main()
