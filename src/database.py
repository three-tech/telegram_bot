import sqlite3

from src.config import DB_NAME


def get_db_connection():
    """Establishes a connection to the SQLite database."""
    conn = sqlite3.connect(DB_NAME)
    conn.execute("PRAGMA timezone = 'Asia/Shanghai'")
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Initializes the database with necessary tables."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # 创建telegram_bot_message_group表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS telegram_bot_message_group (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            media_group_id TEXT,
            media_type TEXT,
            file_id TEXT,
            file_unique_id TEXT,
            file_name TEXT,
            mime_type TEXT,
            file_size INTEGER,
            width INTEGER,
            height INTEGER,
            duration INTEGER,
            thumbnail_file_id TEXT,
            create_time DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # 创建我的频道表
    cursor.execute('''
            CREATE TABLE IF NOT EXISTS channel_my (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                channel_id INTEGER,
                channel_name TEXT,
                channel_type TEXT, -- supergroup
                tag TEXT,
                member_count INTEGER, -- 当前人数
                create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
                update_time DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
    # 创建用户表
    cursor.execute('''
                CREATE TABLE IF NOT EXISTS user (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    first_name TEXT,
                    last_name TEXT, -- supergroup
                    type TEXT, -- 管理员
                    create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
                    update_time DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')

    # 创建telegram_bot_message表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS telegram_bot_message (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id INTEGER,
            from_user_id INTEGER,
            from_user_name TEXT,
            message_id INTEGER,
            message_type TEXT,
            is_forwarded BOOLEAN DEFAULT 0,
            forward_from_channel BOOLEAN DEFAULT 0,
            forward_from_chat_id INTEGER,
            forward_from_message_id INTEGER,
            caption TEXT,
            media_group_id TEXT,
            file_id TEXT,
            file_unique_id TEXT,
            file_name TEXT,
            mime_type TEXT,
            file_size INTEGER,
            width INTEGER,
            height INTEGER,
            duration INTEGER,
            thumbnail_file_id TEXT,
            tag TEXT,
            create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
            update_time DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # 创建channel标签表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS channel_tag (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id, -- channelId
            title TEXT, -- channel标题
            user_name TEXT, -- channel的username
            tag TEXT,
            is_on TEXT,  -- 是否启用标签：'1' 表示启用，'0' 表示禁用
            create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
            update_time DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    conn.commit()
    conn.close()
    print(f"Database {DB_NAME} initialized.")


def save_message_group(media_group_id, media_type, file_id, file_unique_id=None, file_name=None,
                       mime_type=None, file_size=None, width=None, height=None, duration=None,
                       thumbnail_file_id=None):
    """Saves a media item to the message group table."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO telegram_bot_message_group (
            media_group_id, media_type, file_id, file_unique_id, file_name, mime_type,
            file_size, width, height, duration, thumbnail_file_id
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        media_group_id, media_type, file_id, file_unique_id, file_name, mime_type,
        file_size, width, height, duration, thumbnail_file_id
    ))
    conn.commit()
    conn.close()


def save_message(chat_id, from_user_id, from_user_name, message_id, message_type,
                 is_forwarded=False, forward_from_channel=False, forward_from_chat_id=None,
                 forward_from_message_id=None, caption=None, media_group_id=None, file_id=None,
                 file_unique_id=None, file_name=None, mime_type=None, file_size=None,
                 width=None, height=None, duration=None, thumbnail_file_id=None, tag=None):
    """Saves a message to the database. Idempotent for media_group_id."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # If media_group_id is present, check if it already exists
    if media_group_id:
        cursor.execute("SELECT id FROM telegram_bot_message WHERE media_group_id = ?", (media_group_id,))
        existing_row = cursor.fetchone()
        if existing_row:
            conn.close()
            return existing_row['id']

    cursor.execute('''
        INSERT INTO telegram_bot_message (
            chat_id, from_user_id, from_user_name, message_id, 
            message_type, is_forwarded, forward_from_channel,
            forward_from_chat_id, forward_from_message_id, caption,
            media_group_id, file_id, file_unique_id, file_name, mime_type,
            file_size, width, height, duration, thumbnail_file_id, tag
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        chat_id, from_user_id, from_user_name, message_id,
        message_type, is_forwarded, forward_from_channel,
        forward_from_chat_id, forward_from_message_id, caption,
        media_group_id, file_id, file_unique_id, file_name, mime_type,
        file_size, width, height, duration, thumbnail_file_id, tag
    ))
    db_message_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return db_message_id


def getChannelTag(chat_id):
    """
    根据chat_id查询channel_tag信息
    
    Args:
        chat_id: 频道的chat_id
        
    Returns:
        channel_tag记录的字典,如果不存在则返回None
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM channel_tag WHERE chat_id = ? AND is_on = '1'",
        (chat_id,)
    )
    row = cursor.fetchone()
    conn.close()

    if row:
        return dict(row)
    return None


def isAdminUser(user_id):
    """
    检查用户是否为管理员
    
    Args:
        user_id: 用户的user_id
        
    Returns:
        True表示是管理员,False表示不是管理员
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT type FROM user WHERE user_id = ?",
        (user_id,)
    )
    row = cursor.fetchone()
    conn.close()

    if row and row['type'] == '管理员':
        return True
    return False


def saveChannelTag(chat_id, title, user_name, tag):
    """
    保存channel_tag记录
    
    Args:
        chat_id: 频道的chat_id
        title: 频道标题
        user_name: 频道的username
        tag: 标签
        
    Returns:
        新插入记录的id
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO channel_tag (chat_id, title, user_name, tag, is_on)
        VALUES (?, ?, ?, ?, '1')
    ''', (chat_id, title, user_name, tag))
    channel_tag_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return channel_tag_id


def getDistinctTags():
    """
    获取所有不重复的tag值
    
    Returns:
        tag列表
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT tag FROM channel_tag WHERE tag IS NOT NULL AND tag != ''")
    rows = cursor.fetchall()
    conn.close()

    tags = [row['tag'] for row in rows]
    return tags
