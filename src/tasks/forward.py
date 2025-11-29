import logging
from telegram.ext import ContextTypes
from telegram.error import TelegramError
from src.database import getAllMyChannels, getMessagesByTag, updateMyChannel


async def execute_forwarding_task(context: ContextTypes.DEFAULT_TYPE):
    """
    执行转发任务：将消息转发到我的频道
    """
    logging.info("开始执行转发任务")

    # 1. 获取所有我的频道配置
    my_channels = getAllMyChannels()

    for channel in my_channels:
        await process_channel_forwarding(context, channel)

    logging.info("转发任务执行完毕")


async def process_channel_forwarding(context: ContextTypes.DEFAULT_TYPE, channel: dict):
    """
    处理单个频道的消息转发

    Args:
        context: Telegram上下文
        channel: 频道配置信息
    """
    try:
        channel_id = channel['channel_id']
        tag = channel['tag']
        last_id = channel['last_id'] if channel['last_id'] else 0
        per_count = channel['per_count'] if channel['per_count'] else 1

        logging.info(f"正在处理频道: {channel['channel_name']} (ID: {channel_id}), Tag: {tag}, Last ID: {last_id}")

        # 查询待转发消息
        messages = getMessagesByTag(tag, last_id, per_count)

        if not messages:
            logging.info(f"频道 {channel['channel_name']} 没有新消息")
            return

        logging.info(f"频道 {channel['channel_name']} 发现 {len(messages)} 条新消息")

        # 转发消息并获取最新的消息ID
        new_last_id = await forward_messages(context, channel_id, messages)

        # 更新频道信息
        if new_last_id > last_id:
            await update_channel_info(context, channel, new_last_id)

    except Exception as e:
        logging.error(f"处理频道 {channel.get('channel_name', 'Unknown')} 时发生错误: {e}")


async def forward_messages(context: ContextTypes.DEFAULT_TYPE, channel_id: str, messages: list) -> int:
    """
    转发消息列表，使用本地保存的消息数据重新构建发送

    Args:
        context: Telegram上下文
        channel_id: 目标频道ID
        messages: 待转发的消息列表

    Returns:
        最新成功转发的消息ID
    """
    new_last_id = 0
    success_count = 0

    for msg in messages:
        try:
            await send_message_from_data(context, channel_id, msg)
            new_last_id = msg['id']
            success_count += 1

        except TelegramError as e:
            logging.error(f"发送消息失败 (Msg ID: {msg['id']}): {e}")
            # 处理特定错误类型
            error_message = str(e).lower()
            if "message not found" in error_message or "message to copy not found" in error_message:
                # 消息已被删除，跳过此消息
                logging.info(f"消息 {msg['id']} 已被删除，跳过处理")
                new_last_id = msg['id']
            # 对于其他错误，保留当前 last_id 不更新，以便下次重试

        except Exception as e:
            logging.error(f"发送消息时发生未知错误 (Msg ID: {msg['id']}): {e}")
            # 保留当前 last_id 不更新，以便下次重试

    logging.info(f"成功发送 {success_count} 条消息")
    return new_last_id


async def send_message_from_data(context: ContextTypes.DEFAULT_TYPE, channel_id: str, msg: dict):
    """
    根据保存的消息数据重新构建并发送消息

    Args:
        context: Telegram上下文
        channel_id: 目标频道ID
        msg: 消息数据
    """
    caption = msg.get('caption')
    
    if msg.get('media_group_id') and msg.get('group_media'):
        # 处理媒体组消息
        await send_media_group(context, channel_id, msg)
    elif msg.get('file_id'):
        # 处理单个媒体消息
        await send_single_media(context, channel_id, msg)
    elif caption:
        # 处理纯文本消息
        await context.bot.send_message(chat_id=channel_id, text=caption)
    else:
        logging.warning(f"消息 {msg['id']} 没有可发送的内容")


async def send_media_group(context: ContextTypes.DEFAULT_TYPE, channel_id: str, msg: dict):
    """
    发送媒体组消息
    """
    from telegram import InputMediaPhoto, InputMediaVideo, InputMediaAudio, InputMediaDocument
    
    group_media = msg.get('group_media', [])
    if not group_media:
        return
    
    # 构建媒体组
    media_group = []
    
    for media in group_media:
        media_type = media.get('media_type')
        file_id = media.get('file_id')
        
        if not file_id:
            continue
            
        caption = msg.get('caption') if media == group_media[0] else None
        
        if media_type == 'photo':
            media_group.append(InputMediaPhoto(media=file_id, caption=caption))
        elif media_type == 'video':
            media_group.append(InputMediaVideo(media=file_id, caption=caption))
        elif media_type == 'audio':
            media_group.append(InputMediaAudio(media=file_id, caption=caption))
        elif media_type == 'document':
            media_group.append(InputMediaDocument(media=file_id, caption=caption))
    
    if media_group:
        await context.bot.send_media_group(chat_id=channel_id, media=media_group)


async def send_single_media(context: ContextTypes.DEFAULT_TYPE, channel_id: str, msg: dict):
    """
    发送单个媒体消息
    """
    media_type = msg.get('message_type')
    file_id = msg.get('file_id')
    caption = msg.get('caption')
    
    if not file_id:
        return
    
    if media_type == 'photo':
        await context.bot.send_photo(chat_id=channel_id, photo=file_id, caption=caption)
    elif media_type == 'video':
        await context.bot.send_video(chat_id=channel_id, video=file_id, caption=caption)
    elif media_type == 'audio':
        await context.bot.send_audio(chat_id=channel_id, audio=file_id, caption=caption)
    elif media_type == 'document':
        await context.bot.send_document(chat_id=channel_id, document=file_id, caption=caption)
    elif media_type == 'animation':
        await context.bot.send_animation(chat_id=channel_id, animation=file_id, caption=caption)
    elif media_type == 'voice':
        await context.bot.send_voice(chat_id=channel_id, voice=file_id, caption=caption)
    elif media_type == 'video_note':
        await context.bot.send_video_note(chat_id=channel_id, video_note=file_id)
    elif caption:
        # 如果没有媒体文件但有文本，发送文本消息
        await context.bot.send_message(chat_id=channel_id, text=caption)
    else:
        logging.warning(f"未知的媒体类型: {media_type}")


async def update_channel_info(context: ContextTypes.DEFAULT_TYPE, channel: dict, new_last_id: int):
    """
    更新频道信息

    Args:
        context: Telegram上下文
        channel: 频道配置信息
        new_last_id: 新的最后处理消息ID
    """
    channel_id = channel['channel_id']

    try:
        chat_info = await context.bot.get_chat(channel_id)
        member_count = await chat_info.get_member_count()
        channel_title = chat_info.title

        updateMyChannel(
            channel_id=channel_id,
            last_id=new_last_id,
            member_count=member_count,
            channel_name=channel_title
        )
        logging.info(f"频道 {channel_title} 更新完成: Last ID {new_last_id}, 成员数 {member_count}")

    except Exception as e:
        logging.error(f"更新频道信息失败: {e}")
        # 即使获取频道信息失败，也应该保存 last_id，否则会重复发送
        # 但 updateMyChannel 需要 member_count 等参数
        # 使用旧值或默认值
        updateMyChannel(
            channel_id=channel_id,
            last_id=new_last_id,
            member_count=channel.get('member_count', 0),
            channel_name=channel.get('channel_name', 'Unknown Channel')
        )
