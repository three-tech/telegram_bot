import json
import logging

from telegram import Update
from telegram.ext import ContextTypes


async def default_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    jsonMessage = json.dumps(message.to_dict(), indent=2, ensure_ascii=False)
    logging.info(f"默认消息处理器: {jsonMessage}")
