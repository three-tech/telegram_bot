import logging

from telegram import Update
from telegram.ext import ContextTypes

from src.database import saveChannelTag, getDistinctTags


async def callbackQueryHandler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    处理按钮回调的处理器
    
    Args:
        update: Telegram更新对象
        context: Telegram上下文对象
    """
    query = update.callback_query
    await query.answer()

    callbackData = query.data
    logging.info(f"收到回调数据: {callbackData}")

    if callbackData.startswith("create_tag:"):
        await handleCreateTag(query, callbackData, context)
    elif callbackData.startswith("skip_tag:"):
        await handleSkipTag(query, callbackData)
    elif callbackData.startswith("set_tag:"):
        await handleSetTag(query, callbackData, context)
    elif callbackData.startswith("new_tag:"):
        await handleNewTag(query, callbackData, context)


async def handleCreateTag(query, callbackData: str, context: ContextTypes.DEFAULT_TYPE):
    """
    处理创建channel_tag的回调,展示tag选择按钮
    
    Args:
        query: CallbackQuery对象
        callbackData: 回调数据字符串,格式: create_tag:chatId
        context: Telegram上下文对象
    """
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup

    parts = callbackData.split(":", 1)
    if len(parts) < 2:
        await query.edit_message_text(text="数据格式错误")
        return

    _, chatId = parts
    chatId = int(chatId)

    # 从context.user_data中获取频道信息
    channelInfo = context.user_data.get('pending_channels', {}).get(str(chatId))
    if not channelInfo:
        await query.edit_message_text(text="频道信息已过期,请重新转发消息")
        return

    channelTitle = channelInfo['title']
    channelUsername = channelInfo['username']

    # 获取所有已存在的tag
    existingTags = getDistinctTags()

    # 构建按钮列表
    keyboard = []
    for tag in existingTags:
        keyboard.append([
            InlineKeyboardButton(tag, callback_data=f"set_tag:{chatId}:{tag}")
        ])

    replyMarkup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(
        text=f"请为频道 {channelTitle} 选择标签:",
        reply_markup=replyMarkup
    )
    logging.info(f"已展示tag选择列表,频道: {channelTitle}")


async def handleSkipTag(query, callbackData: str):
    """
    处理跳过创建channel_tag的回调
    
    Args:
        query: CallbackQuery对象
        callbackData: 回调数据字符串
    """
    parts = callbackData.split(":")
    if len(parts) < 2:
        await query.edit_message_text(text="数据格式错误")
        return

    _, chatId = parts

    await query.edit_message_text(text="已跳过,该频道的消息将不会被保存")
    logging.info(f"用户选择跳过频道 {chatId} 的标签创建")


async def handleSetTag(query, callbackData: str, context: ContextTypes.DEFAULT_TYPE):
    """
    处理设置tag的回调,保存channel_tag记录
    
    Args:
        query: CallbackQuery对象
        callbackData: 回调数据字符串,格式: set_tag:chatId:tag
        context: Telegram上下文对象
    """
    parts = callbackData.split(":", 2)
    if len(parts) < 3:
        await query.edit_message_text(text="数据格式错误")
        return

    _, chatId, tag = parts
    chatId = int(chatId)

    # 从context.user_data中获取频道信息
    channelInfo = context.user_data.get('pending_channels', {}).get(str(chatId))
    if not channelInfo:
        await query.edit_message_text(text="频道信息已过期,请重新转发消息")
        return

    channelTitle = channelInfo['title']
    channelUsername = channelInfo['username']

    try:
        channelTagId = saveChannelTag(
            chat_id=chatId,
            title=channelTitle,
            user_name=channelUsername,
            tag=tag
        )

        await query.edit_message_text(
            text=f"已为频道 {channelTitle} 创建标签记录\n标签: {tag}"
        )
        logging.info(f"已创建channel_tag记录 - ID: {channelTagId}, 频道: {channelTitle}, 标签: {tag}")

        # 清理user_data
        if str(chatId) in context.user_data.get('pending_channels', {}):
            del context.user_data['pending_channels'][str(chatId)]
    except Exception as e:
        logging.error(f"创建channel_tag失败: {e}")
        await query.edit_message_text(text=f"创建失败: {str(e)}")


async def handleNewTag(query, callbackData: str, context: ContextTypes.DEFAULT_TYPE):
    """
    处理新建tag的回调
    
    Args:
        query: CallbackQuery对象
        callbackData: 回调数据字符串,格式: new_tag:chatId
        context: Telegram上下文对象
    """
    parts = callbackData.split(":", 1)
    if len(parts) < 2:
        await query.edit_message_text(text="数据格式错误")
        return

    _, chatId = parts
    chatId = int(chatId)

    # 从context.user_data中获取频道信息
    channelInfo = context.user_data.get('pending_channels', {}).get(str(chatId))
    if not channelInfo:
        await query.edit_message_text(text="频道信息已过期,请重新转发消息")
        return

    channelTitle = channelInfo['title']

    await query.edit_message_text(
        text=f"请直接回复此消息,输入新的标签名称\n频道: {channelTitle}\n\n(注: 当前版本需要手动在数据库中添加新标签)"
    )
    logging.info(f"用户选择为频道 {channelTitle} 创建新标签")
