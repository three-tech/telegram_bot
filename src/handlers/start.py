from telegram import Update
from telegram.ext import ContextTypes

from src.database import isAdminUser


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for the /start command."""
    user_id = update.effective_user.id
    
    # 检查用户是否为管理员
    if not isAdminUser(user_id):
        # 非管理员用户不做任何响应
        return
    
    # 管理员用户返回指令列表
    commands_text = """🤖 机器人指令列表:

/start - 显示此指令列表
/forward - 查看转发频道列表并执行转发

⚠️ 仅管理员可使用此机器人功能"""
    
    await context.bot.send_message(chat_id=update.effective_chat.id, text=commands_text)
