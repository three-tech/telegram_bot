import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, CallbackQueryHandler, filters
from src.config import BOT_TOKEN
from src.database import init_db
from src.logger import setup_logging
from src.handlers.start import start
from src.handlers.forwarded import forwarded_message_handler
from src.handlers.callback import callbackQueryHandler

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
    # 转发处理器
    forwarded_handler = MessageHandler(filters.FORWARDED, forwarded_message_handler)
    # 回调处理器
    callback_handler = CallbackQueryHandler(callbackQueryHandler)
    
    application.add_handler(start_handler)
    application.add_handler(forwarded_handler)
    application.add_handler(callback_handler)
    
    # Run the bot
    print("Bot is running...")
    application.run_polling()

if __name__ == '__main__':
    main()
