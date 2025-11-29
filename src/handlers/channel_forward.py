import logging

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from src.database import getAllMyChannels
from src.tasks.forward import process_channel_forwarding


async def handle_forward_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    处理转发指令，展示频道列表和转发按钮
    
    Args:
        update: Telegram更新对象
        context: Telegram上下文对象
    """
    logging.info("收到转发指令请求")
    
    try:
        # 获取所有频道配置
        channels = getAllMyChannels()
        
        if not channels:
            await update.message.reply_text("暂无可用的转发频道")
            logging.info("没有找到可用的转发频道")
            return
        
        # 构建频道列表和按钮
        message_text = "📋 转发频道列表:\n\n"
        keyboard = []
        
        for channel in channels:
            # 格式化频道信息：channel_name channel_tag member_count per_count
            channel_name = channel.get('channel_name', '未知频道')
            channel_tag = channel.get('tag', '无标签')
            member_count = channel.get('member_count', 0)
            per_count = channel.get('per_count', 0)
            
            message_text += f"{channel_name} {channel_tag} {member_count} {per_count}\n"
            
            # 为每个频道添加转发按钮
            keyboard.append([
                InlineKeyboardButton(
                    f"转发 {channel_name}",
                    callback_data=f"forward_channel:{channel['channel_id']}"
                )
            ])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            text=message_text,
            reply_markup=reply_markup
        )
        
        logging.info(f"已展示 {len(channels)} 个频道的转发列表")
        
    except Exception as e:
        error_message = f"获取转发频道列表失败: {str(e)}"
        await update.message.reply_text(error_message)
        logging.error(error_message)


async def handle_forward_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    处理转发按钮的回调事件
    
    Args:
        update: Telegram更新对象
        context: Telegram上下文对象
    """
    query = update.callback_query
    await query.answer()
    
    callback_data = query.data
    logging.info(f"收到转发回调: {callback_data}")
    
    try:
        # 解析回调数据: forward_channel:channel_id
        parts = callback_data.split(":", 1)
        if len(parts) < 2:
            await query.edit_message_text(text="数据格式错误")
            return
        
        _, channel_id = parts
        channel_id = int(channel_id)
        
        # 获取所有频道信息找到对应的频道
        channels = getAllMyChannels()
        target_channel = None
        
        for channel in channels:
            if channel['channel_id'] == channel_id:
                target_channel = channel
                break
        
        if not target_channel:
            await query.edit_message_text(text="未找到指定的频道配置")
            logging.warning(f"未找到频道ID {channel_id} 的配置")
            return
        
        # 开始处理单个频道转发
        processing_text = f"正在转发到 {target_channel['channel_name']}..."
        await query.edit_message_text(text=processing_text)
        logging.info(f"开始转发频道 {target_channel['channel_name']} ")
        
        # 执行转发任务
        await process_channel_forwarding(context, target_channel)
        
        # 转发完成，更新消息
        success_text = f"✅ 已完成转发到 {target_channel['channel_name']}"
        await query.edit_message_text(text=success_text)
        logging.info(f"完成转发频道 {target_channel['channel_name']}")
        
    except Exception as e:
        error_message = f"转发过程中发生错误: {str(e)}"
        
        # 特殊处理消息未修改错误
        if "not modified" in str(e).lower():
            logging.info(f"转发消息内容未变化，忽略编辑错误: {callback_data}")
            return
        
        await query.edit_message_text(text=error_message)
        logging.error(error_message)