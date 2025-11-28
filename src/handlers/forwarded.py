import json
import logging
from typing import Dict, Optional, Tuple

from telegram import Message, Update
from telegram.ext import ContextTypes

from src.database import save_message, save_message_group, getChannelTag, isAdminUser


def extractForwardInfo(message: Message) -> Tuple[bool, Optional[int], Optional[int]]:
    """
    提取消息的转发信息
    
    Args:
        message: Telegram消息对象
        
    Returns:
        (是否为频道转发, 转发来源chat_id, 转发来源message_id)
    """
    if message.forward_origin is None:
        return False, None, None

    if message.forward_origin.type != 'channel':
        logging.info(f"检测到非频道转发: {message.forward_origin.type}")
        return False, None, None

    forwardChatId = message.forward_origin.chat.id
    forwardMessageId = message.forward_origin.message_id
    logging.info(f"检测到频道转发 - chat: {message.forward_origin.chat.title}, message_id: {forwardMessageId}")

    return True, forwardChatId, forwardMessageId


def extractCaption(message: Message) -> Optional[str]:
    """
    提取消息的标题或文本内容
    
    Args:
        message: Telegram消息对象
        
    Returns:
        标题文本或None
    """
    caption = message.caption if message.caption else message.text
    if caption:
        logging.info(f"标题: {caption}")
    return caption


def extractPhotoMetadata(photo) -> Dict[str, any]:
    """
    提取照片元数据
    
    Args:
        photo: Telegram照片对象
        
    Returns:
        包含照片元数据的字典
    """
    return {
        'fileId': photo.file_id,
        'fileUniqueId': photo.file_unique_id,
        'fileSize': photo.file_size,
        'width': photo.width,
        'height': photo.height
    }


def extractVideoMetadata(video) -> Dict[str, any]:
    """
    提取视频元数据
    
    Args:
        video: Telegram视频对象
        
    Returns:
        包含视频元数据的字典
    """
    metadata = {
        'fileId': video.file_id,
        'fileUniqueId': video.file_unique_id,
        'fileName': video.file_name,
        'mimeType': video.mime_type,
        'fileSize': video.file_size,
        'width': video.width,
        'height': video.height,
        'duration': video.duration,
        'thumbnailFileId': video.thumbnail.file_id if video.thumbnail else None
    }

    logging.info(
        f"视频 - 分辨率: {video.width}x{video.height}, "
        f"时长: {video.duration}s, 大小: {video.file_size}"
    )

    return metadata


def determineMessageType(message: Message) -> Tuple[str, Dict[str, any]]:
    """
    确定消息类型并提取对应的元数据
    
    Args:
        message: Telegram消息对象
        
    Returns:
        (消息类型, 元数据字典)
    """
    if message.text and not message.photo and not message.video:
        logging.info(f"文本消息: {message.text}")
        return 'text', {}

    if message.photo:
        highestResPhoto = message.photo[-1]
        return 'photo', extractPhotoMetadata(highestResPhoto)

    if message.video:
        return 'video', extractVideoMetadata(message.video)

    return 'text', {}


def saveMediaGroupMessage(
        chatId: int,
        userId: int,
        userName: str,
        messageId: int,
        forwardChatId: int,
        forwardMessageId: int,
        caption: Optional[str],
        mediaGroupId: str,
        messageType: str,
        metadata: Dict[str, any],
        tag: Optional[str] = None
) -> int:
    """
    保存媒体组消息
    
    Args:
        chatId: 聊天ID
        userId: 用户ID
        userName: 用户名
        messageId: 消息ID
        forwardChatId: 转发来源chat_id
        forwardMessageId: 转发来源message_id
        caption: 标题
        mediaGroupId: 媒体组ID
        messageType: 消息类型
        metadata: 媒体元数据
        
    Returns:
        数据库消息ID
    """
    dbMessageId = save_message(
        chat_id=chatId,
        from_user_id=userId,
        from_user_name=userName,
        message_id=messageId,
        message_type='media_group',
        is_forwarded=True,
        forward_from_channel=True,
        forward_from_chat_id=forwardChatId,
        forward_from_message_id=forwardMessageId,
        caption=caption,
        media_group_id=mediaGroupId,
        file_id=None,
        file_unique_id=None,
        file_name=None,
        mime_type=None,
        file_size=None,
        width=None,
        height=None,
        duration=None,
        thumbnail_file_id=None,
        tag=tag
    )

    save_message_group(
        media_group_id=mediaGroupId,
        media_type=messageType,
        file_id=metadata.get('fileId'),
        file_unique_id=metadata.get('fileUniqueId'),
        file_name=metadata.get('fileName'),
        mime_type=metadata.get('mimeType'),
        file_size=metadata.get('fileSize'),
        width=metadata.get('width'),
        height=metadata.get('height'),
        duration=metadata.get('duration'),
        thumbnail_file_id=metadata.get('thumbnailFileId')
    )

    logging.info(f"已保存媒体组项 - 组ID: {mediaGroupId}, 类型: {messageType}, DB消息ID: {dbMessageId}")
    return dbMessageId


def saveSingleMessage(
        chatId: int,
        userId: int,
        userName: str,
        messageId: int,
        forwardChatId: int,
        forwardMessageId: int,
        caption: Optional[str],
        messageType: str,
        metadata: Dict[str, any],
        tag: Optional[str] = None
) -> int:
    """
    保存单条消息
    
    Args:
        chatId: 聊天ID
        userId: 用户ID
        userName: 用户名
        messageId: 消息ID
        forwardChatId: 转发来源chat_id
        forwardMessageId: 转发来源message_id
        caption: 标题
        messageType: 消息类型
        metadata: 媒体元数据
        
    Returns:
        数据库消息ID
    """
    dbMessageId = save_message(
        chat_id=chatId,
        from_user_id=userId,
        from_user_name=userName,
        message_id=messageId,
        message_type=messageType,
        is_forwarded=True,
        forward_from_channel=True,
        forward_from_chat_id=forwardChatId,
        forward_from_message_id=forwardMessageId,
        caption=caption,
        media_group_id=None,
        file_id=metadata.get('fileId'),
        file_unique_id=metadata.get('fileUniqueId'),
        file_name=metadata.get('fileName'),
        mime_type=metadata.get('mimeType'),
        file_size=metadata.get('fileSize'),
        width=metadata.get('width'),
        height=metadata.get('height'),
        duration=metadata.get('duration'),
        thumbnail_file_id=metadata.get('thumbnailFileId'),
        tag=tag
    )

    logging.info(f"已保存单条转发 {messageType} - 数据库ID: {dbMessageId}")
    return dbMessageId


async def forwarded_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    处理频道转发消息的主处理器
    
    Args:
        update: Telegram更新对象
        context: Telegram上下文对象
    """
    user = update.effective_user
    message = update.message

    jsonMessage = json.dumps(message.to_dict(), indent=2, ensure_ascii=False)
    # logging.info(f"收到消息: {jsonMessage}")

    # 步骤1: 验证是否为频道转发
    isChannelForward, forwardChatId, forwardMessageId = extractForwardInfo(message)
    if not isChannelForward:
        logging.info(
            f"忽略来自 {user.first_name} ({user.id}) 的非频道消息"
        )
        return

    # 步骤2: 验证是否为管理员
    if not isAdminUser(user.id):
        logging.info(
            f"忽略非管理员 {user.first_name} ({user.id}) 转发的消息"
        )
        return

    # 步骤3: 检查channel_tag
    channelTag = getChannelTag(forwardChatId)

    if not channelTag:
        # channel不存在于channel_tag表中,使用按钮提示用户
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup

        channelTitle = message.forward_origin.chat.title if message.forward_origin.chat.title else "未知频道"
        channelUsername = message.forward_origin.chat.username if message.forward_origin.chat.username else ""

        # 将频道信息存储在context.user_data中,避免callback_data过长
        if 'pending_channels' not in context.user_data:
            context.user_data['pending_channels'] = {}

        context.user_data['pending_channels'][str(forwardChatId)] = {
            'title': channelTitle,
            'username': channelUsername
        }

        keyboard = [
            [
                InlineKeyboardButton("是", callback_data=f"create_tag:{forwardChatId}"),
                InlineKeyboardButton("否", callback_data=f"skip_tag:{forwardChatId}")
            ]
        ]
        replyMarkup = InlineKeyboardMarkup(keyboard)

        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"检测到新频道: {channelTitle}\n是否需要为该频道创建标签?",
            reply_markup=replyMarkup
        )
        logging.info(f"频道 {channelTitle} (ID: {forwardChatId}) 不存在于channel_tag表中,已发送按钮提示")
        return

    tag = channelTag.get('tag')
    logging.info(f"频道 {forwardChatId} 的标签: {tag}")

    # 步骤4: 提取消息内容
    caption = extractCaption(message)
    messageType, metadata = determineMessageType(message)

    # 步骤5: 保存消息
    if message.media_group_id:
        dbMessageId = saveMediaGroupMessage(
            chatId=update.effective_chat.id,
            userId=user.id,
            userName=user.username or user.first_name,
            messageId=message.message_id,
            forwardChatId=forwardChatId,
            forwardMessageId=forwardMessageId,
            caption=caption,
            mediaGroupId=message.media_group_id,
            messageType=messageType,
            metadata=metadata,
            tag=tag
        )
    else:
        dbMessageId = saveSingleMessage(
            chatId=update.effective_chat.id,
            userId=user.id,
            userName=user.username or user.first_name,
            messageId=message.message_id,
            forwardChatId=forwardChatId,
            forwardMessageId=forwardMessageId,
            caption=caption,
            messageType=messageType,
            metadata=metadata,
            tag=tag
        )
