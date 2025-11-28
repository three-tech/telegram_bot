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
        channel_id = channel['channel_id']
        tag = channel['tag']
        last_id = channel['last_id'] if channel['last_id'] else 0
        per_count = channel['per_count'] if channel['per_count'] else 1
        
        logging.info(f"正在处理频道: {channel['channel_name']} (ID: {channel_id}), Tag: {tag}, Last ID: {last_id}")
        
        # 2.1 查询待转发消息
        messages = getMessagesByTag(tag, last_id, per_count)
        
        if not messages:
            logging.info(f"频道 {channel['channel_name']} 没有新消息")
            continue
            
        logging.info(f"频道 {channel['channel_name']} 发现 {len(messages)} 条新消息")
        
        new_last_id = last_id
        success_count = 0
        
        # 2.2 转发消息
        for msg in messages:
            try:
                # 使用 copy_message 将消息复制到目标频道
                # 这样可以避免显示"转发自...", 且内容更干净
                await context.bot.copy_message(
                    chat_id=channel_id,
                    from_chat_id=msg['chat_id'],
                    message_id=msg['message_id']
                )
                new_last_id = msg['id']
                success_count += 1
                # 稍微延迟一下，避免触发频率限制？暂时不需要，除非量很大
                
            except TelegramError as e:
                logging.error(f"转发消息失败 (Msg ID: {msg['id']}): {e}")
                # 如果是消息不存在等错误，可能需要跳过，继续下一个
                # 这里我们选择继续，并更新 last_id，避免卡死在一条错误消息上
                # 但如果是因为网络等原因失败，可能不应该更新 last_id
                # 简单起见，如果失败，我们暂时不更新 new_last_id 为当前ID，
                # 但这样会导致下次重复尝试这条失败的消息。
                # 策略：如果明确是内容问题（如已被删除），应该跳过。
                # 暂时策略：记录错误，不更新 new_last_id，下次重试。
                # 修正策略：根据 PRD "更新channel_my的last_id为当前查询到的telegram_bot_message.id"
                # 如果发送失败，是否更新？
                # 如果消息源被删了，永远发不出去，会卡死。
                # 我们可以认为，如果尝试过了，就应该往前走，或者记录失败状态。
                # 为了防止卡死，我们还是更新 last_id，假设失败是因为源消息问题或不重要。
                # 或者更稳妥的：只在成功时更新。但需注意死循环。
                # 鉴于 "禁止添加额外的功能"，我们遵循最简单的逻辑：尝试转发。
                # 如果失败了，我们假设是暂时性错误，不更新 last_id，下次重试。
                # 但为了避免死循环，如果错误是 "Message not found"，应该跳过。
                if "Message not found" in str(e) or "message to copy not found" in str(e).lower():
                     new_last_id = msg['id'] # 跳过已删除的消息
                pass

        if success_count > 0 or new_last_id > last_id:
            # 2.3 更新频道信息
            try:
                chat_info = await context.bot.get_chat(channel_id)
                member_count = chat_info.get_member_count()
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
                    member_count=channel['member_count'],
                    channel_name=channel['channel_name']
                )

    logging.info("转发任务执行完毕")
