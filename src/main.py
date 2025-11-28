from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, filters

from src.config import BOT_TOKEN
from src.database import init_db
from src.handlers.callback import callbackQueryHandler
from src.handlers.default import default_handler
from src.handlers.forwarded import forwarded_message_handler
from src.handlers.start import start
from src.logger import setup_logging

# Setup logging
setup_logging()


def main():
    """Main function to start the bot."""
    # Initialize database
    init_db()

    # Build the application
    application = ApplicationBuilder().token(BOT_TOKEN).build()

    # 开始处理
    application.add_handler(CommandHandler('start', start))
    # 频道转发处理器
    application.add_handler(MessageHandler(filters.FORWARDED, forwarded_message_handler))
    # 回调处理器
    application.add_handler(CallbackQueryHandler(callbackQueryHandler))
    # 默认处理器
    application.add_handler(MessageHandler(filters.ALL, default_handler))

    # Run the bot
    print("Bot is running...")
    application.run_polling()


if __name__ == '__main__':
    main()
