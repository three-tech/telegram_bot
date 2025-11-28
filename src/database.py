import sqlite3

from src.config import DB_NAME


def get_db_connection():
    """Establishes a connection to the SQLite database."""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Initializes the database with necessary tables."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Create telegram_bot_message_group table for media items in a group
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

    # Create telegram_bot_message table with forward fields and detailed media info
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
                 width=None, height=None, duration=None, thumbnail_file_id=None):
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
            file_size, width, height, duration, thumbnail_file_id
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        chat_id, from_user_id, from_user_name, message_id,
        message_type, is_forwarded, forward_from_channel,
        forward_from_chat_id, forward_from_message_id, caption,
        media_group_id, file_id, file_unique_id, file_name, mime_type,
        file_size, width, height, duration, thumbnail_file_id
    ))
    db_message_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return db_message_id
