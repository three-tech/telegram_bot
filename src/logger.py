import logging
import os

def setup_logging():
    """Configures the global logging settings."""
    # Ensure logs directory exists
    if not os.path.exists('logs'):
        os.makedirs('logs')

    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO,
        handlers=[
            logging.FileHandler("../logs/telegram_bot.log"),
            logging.StreamHandler()
        ]
    )
    
    # Suppress httpx logs
    logging.getLogger("httpx").setLevel(logging.WARNING)
