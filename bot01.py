#bot_merged  — bot1 base + bot2 dump-channel fix + bot2 3-mode sequence sorting
import asyncio
import sys

# Fix for Python 3.10+ and Pyrogram
if sys.version_info >= (3, 10):
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        asyncio.set_event_loop(asyncio.new_event_loop())

import os
import re
import sys
import time
import json
import math
import asyncio
import logging
import datetime
import shutil
import subprocess
import heapq
from pyrogram.errors import BadRequest
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Deque, Set
from collections import deque
from dotenv import load_dotenv
from PIL import Image
import motor.motor_asyncio
from pyrogram import Client, filters, __version__, idle
from pyrogram.types import (
    Message, InlineKeyboardButton, InlineKeyboardMarkup,
    CallbackQuery, ChatPermissions
)
from pyrogram.errors import FloodWait, UserNotParticipant, BadRequest

# ── NEW: import Pyrogram v2 enums so type/status comparisons work ──────────
try:
    from pyrogram.enums import ChatType, ChatMemberStatus
    _PYROGRAM_ENUMS = True
except ImportError:
    ChatType = None
    ChatMemberStatus = None
    _PYROGRAM_ENUMS = False

# ==================== LIBTORRENT IMPORT ====================
try:
    import libtorrent as lt
    LIBTORRENT_AVAILABLE = True
    print("✅ libtorrent loaded successfully")
except ImportError:
    LIBTORRENT_AVAILABLE = False
    print("⚠️ libtorrent not available — torrent features disabled. Install with: pip install libtorrent --break-system-packages")

# Load environment variables
load_dotenv()

# ==================== CONFIGURATION ====================
class Config:
    API_ID = int(os.getenv("API_ID", ""))
    API_HASH = os.getenv("API_HASH", "")
    BOT_TOKEN = os.getenv("BOT_TOKEN", "")
    ADMIN = [int(admin) for admin in os.getenv("ADMIN", "").split(",")]
    DB_URL = os.getenv("DB_URL", " ")
    DB_NAME = os.getenv("DB_NAME", "")
    LOG_CHANNEL = int(os.getenv("LOG_CHANNEL", ""))
    START_PIC = os.getenv("START_PIC", "")
    WEBHOOK = os.getenv("WEBHOOK", "").lower() == "true"
    PORT = int(os.getenv("PORT", ""))
    BOT_UPTIME = time.time()
    TIMEOUT_SECONDS = 0
    RESTRICT_CHAT_PERMISSIONS = False
    ALLOWED_GROUPS = set()
    MAX_FILE_SIZE = 2 * 1024 * 1024 * 1024
    ACTIVE_MODE = os.getenv("ACTIVE_MODE", "false").lower() == "true"

class Txt:
    START_TXT = """<b>ʜᴇʏ! {}  

» ɪ ᴀᴍ ᴀᴅᴠᴀɴᴄᴇᴅ ʀᴇɴᴀᴍᴇ ʙᴏᴛ! ᴡʜɪᴄʜ ᴄᴀɴ ᴀᴜᴛᴏʀᴇɴᴀᴍᴇ ʏᴏᴜʀ ғɪʟᴇs ᴡɪᴛʜ ᴄᴜsᴛᴏᴍ ᴄᴀᴘᴛɪᴏɴ ᴀɴᴅ ᴛʜᴜᴍʙɴᴀɪʟ ᴀɴᴅ ᴀʟsᴏ sᴇǫᴜᴇɴᴄᴇ ᴛʜᴇᴍ ᴘᴇʀғᴇᴄᴛʟʏ</b>"""

    HELP_TXT = """<b>📚 Available Commands:</b>

<b>⚙️ Setup Commands (Private Chat Only):</b>
• /autorename [format] - Set auto rename format
• /set_caption [caption] - Set custom caption
• /clear_caption - Reset caption to default (full renamed filename with extension)
• /settitle [title] - Set metadata title
• /setauthor [author] - Set metadata author
• /setartist [artist] - Set metadata artist
• /setaudio [audio] - Set audio metadata
• /setsubtitle [subtitle] - Set subtitle metadata
• /setvideo [video] - Set video metadata
• /setallmeta [text] - Set ALL metadata fields to same value
• /set_thumbnail - Set thumbnail from replied photo
• /view_thumbnail - View your thumbnail
• /delete_thumbnail - Delete thumbnail
• /delete_metadata - Delete metadata settings
• /mediatype - Choose output media type (Document/Video/Audio) – now with buttons!

<b>🌊 Torrent Download Commands (Private Chat Only):</b>
• /start_torrent - Enable torrent download mode
• /stop_torrent - Disable torrent download mode
• After enabling, send a magnet link or upload a .torrent file
• Only video and audio files are downloaded from the torrent
• Files are renamed with your format template and sent to dump channel (if set)

<b>🎬 Encode / Compress Commands:</b>
• /encode_all - Toggle encode mode ON/OFF. When ON, each video file is encoded to 480p, 720p and 1080p.
• /compress - Enter compress mode (encodes to 480p, 720p, 1080p) and auto‑rename with {quality} set to actual quality.
• /compress_480p - Compress only to 480p.
• /compress_720p - Compress only to 720p.
• /compress_1080p - Compress only to 1080p.
• /compress_off - Exit compress mode.

<b>📊 View Commands:</b>
• /view_caption - View your caption
• /view_thumb - View your thumbnail
• /showmetadata - Show metadata settings
• /queue_stats - Check processing queue status
• /queue - Check your position in queue
• /failed_queue - View your files pending manual rename

<b>🗂 Dump Channel Commands:</b>
• /add_dump [channel_id] - Add dump channel (by ID or forward a message)
• /send_dump - Select & enable a dump channel (files go only there)
• /dissable_dump - Disable dump mode (files go to private chat)
• /view_dump - Show current dump settings
• /delete_dump [channel_id] - Remove a dump channel
• /list_dump_channels - List all dump channels

<b>⚡ Control Commands:</b>
• /metadata - Open metadata settings interface
• /stop_renaming - Pause renaming queue (Admin)
• /start_renaming - Resume renaming queue (Admin)
• /admin_priority_on - Enable admin priority (Admin)
• /admin_priority_off - Disable admin priority (Admin)
• /clear_queue_user [user_id] - Clear your queued files (Admins can specify a user ID)
• /skip_failed - Skip current manual rename request

<b>🔄 Sequence Sorting (Private Chat Only):</b>
• /ssequence - Start sequence mode (files are saved, NOT processed)
• /esequence - End sequence mode and choose sort mode (3 modes)
• /sequence_mode [1|2|3] - Set default sort mode
  Mode 1: Season → Quality → Episode
  Mode 2: Season → Episode → Quality
  Mode 3: Quality → Season → Episode

<b>👑 Admin Commands:</b>
• /stats - Bot statistics
• /clear_queue - Clear entire processing queue
• /restart - Restart bot
• /broadcast - Broadcast message
• /add_group [group_id] - Add group to allowed list
• /remove_group [group_id] - Remove group from allowed list
• /list_groups - List all allowed groups

<b>📖 Guide:</b>
1. First use setup commands in private chat with bot
2. Send any file in group or private chat to auto rename
3. Check queue status with /queue_stats
4. Customize with metadata commands
5. If a file can't extract season/episode/quality, it goes to failed queue
6. After all files done, bot asks you to manually provide the filename

<b>📝 Variables for Format:</b>
• {filename} - Original filename
• {season} - Season number
• {episode} - Episode number
• {quality} - Video quality (auto-set when compress/encode mode is on)
• {filesize} - File size
• {duration} - Duration

<b>Example:</b>
<code>/autorename {filename} [S{season}E{episode}] - {quality}</code>"""

# ==================== TORRENT CONSTANTS ====================
TORRENT_VIDEO_EXTS = {'.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv', '.webm', '.m4v', '.ts', '.3gp', '.m2ts', '.mts', '.divx', '.ogv'}
TORRENT_AUDIO_EXTS = {'.mp3', '.flac', '.aac', '.wav', '.ogg', '.m4a', '.opus', '.wma', '.ac3', '.dts', '.alac', '.ape', '.mka'}

# ==================== SEQUENCE SORTING STORAGE ====================
sequence_sessions = {}  # user_id -> {'active': bool, 'files': [message, ...]}

# ==================== ENCODE MODE STORAGE (old) ====================
encode_sessions: Dict[int, bool] = {}

# ==================== COMPRESS MODE STORAGE (new) ====================
compress_sessions: Dict[int, Optional[str]] = {}

# ==================== TORRENT MODE STORAGE ====================
torrent_mode_sessions: Dict[int, bool] = {}

# ==================== MANUAL RENAME STATE ====================
failed_rename_queue: Dict[int, List[dict]] = {}
manual_rename_waiting: Dict[int, dict] = {}

# ==================== ADD DUMP CHANNEL STATE ====================
add_dump_waiting = {}   # user_id -> True when waiting for forwarded message

# ==================== GLOBAL RENAMING PAUSE ====================
renaming_paused = False

# ==================== SEQUENCE UTILITIES (3 modes from bot2) ====================
_QUALITY_LABELS = {4: '4K', 3: '2K', 2: '1080p', 1: '720p', 0: '480p'}

def quality_label(q: int) -> str:
    return _QUALITY_LABELS.get(q, 'HD')

def get_msg_fname(msg: Message) -> str:
    if msg.document: return msg.document.file_name or 'file'
    if msg.video:    return msg.video.file_name    or 'video.mp4'
    if msg.audio:    return msg.audio.file_name    or 'audio.mp3'
    return 'file'

def sort_key_for_mode(msg: Message, mode: int):
    """Return sort key tuple depending on chosen sequence mode."""
    fname = get_msg_fname(msg)
    season, quality, episode = extract_file_info(fname)
    if   mode == 1: return (season, quality, episode)   # Season > Quality > Episode
    elif mode == 2: return (season, episode, quality)   # Season > Episode > Quality
    else:           return (quality, season, episode)   # Quality > Season > Episode

def generate_sort_summary(sorted_files: list, mode: int) -> str:
    """Build a human-readable sorted-file summary for the chosen mode."""
    if not sorted_files:
        return "No files."
    lines: List[str] = []
    if mode == 1:
        lines.append("🔀 **Sorted: Season › Quality › Episode**\n")
        last_s = last_q = None
        for msg in sorted_files:
            s, q, e = extract_file_info(get_msg_fname(msg))
            if s != last_s or q != last_q:
                lines.append(f"\n**S{s:02d} {quality_label(q)}:**")
            lines.append(f"  Ep{e:02d} - `{get_msg_fname(msg)[:40]}`")
            last_s, last_q = s, q
    elif mode == 2:
        lines.append("🔀 **Sorted: Season › Episode › Quality**\n")
        last_s = last_e = None
        for msg in sorted_files:
            s, q, e = extract_file_info(get_msg_fname(msg))
            if s != last_s or e != last_e:
                lines.append(f"\n**S{s:02d} Ep{e:02d}:**")
            lines.append(f"  {quality_label(q)} - `{get_msg_fname(msg)[:40]}`")
            last_s, last_e = s, e
    else:
        lines.append("🔀 **Sorted: Quality › Season › Episode**\n")
        last_q = last_s = None
        for msg in sorted_files:
            s, q, e = extract_file_info(get_msg_fname(msg))
            if q != last_q or s != last_s:
                lines.append(f"\n**{quality_label(q)} - S{s:02d}:**")
            lines.append(f"  Ep{e:02d} - `{get_msg_fname(msg)[:40]}`")
            last_q, last_s = q, s
    return "\n".join(lines)

def _get_failed_queue(user_id: int) -> List[dict]:
    if user_id not in failed_rename_queue:
        failed_rename_queue[user_id] = []
    return failed_rename_queue[user_id]

def _add_to_failed_queue(user_id: int, failed_item: dict):
    _get_failed_queue(user_id).append(failed_item)

def _has_pending_queue_tasks(user_id: int) -> bool:
    queue_info = processing_queue.get_queue_info()
    for task in queue_info['waiting_list']:
        if task['user_id'] == user_id:
            return True
    if queue_info['is_processing'] and queue_info['current']:
        if queue_info['current']['user_id'] == user_id:
            return True
    return False

async def _trigger_manual_rename_if_ready(user_id: int):
    if user_id in manual_rename_waiting:
        return
    failed = _get_failed_queue(user_id)
    if not failed:
        return
    if _has_pending_queue_tasks(user_id):
        return
    await _prompt_next_manual_rename(user_id)

async def _prompt_next_manual_rename(user_id: int):
    failed = _get_failed_queue(user_id)
    if not failed:
        return
    item = failed[0]
    manual_rename_waiting[user_id] = {'failed_item': item, 'awaiting': True}
    original_name = item.get('original_file_name', 'Unknown')
    remaining = len(failed)
    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("⏭️ Skip This File", callback_data=f"skip_manual_{user_id}")],
        [InlineKeyboardButton("❌ Cancel All Manual Renames", callback_data=f"cancel_manual_{user_id}")]
    ])
    try:
        await app.send_message(
            chat_id=user_id,
            text=(
                f"Select The Output File Type File Name :- `{original_name}`\n\n"
                f"Please Enter New Filename...\n\n"
                f"Old File Name :- `{original_name}`"
            ),
            reply_markup=buttons
        )
    except Exception as e:
        print(f"Error prompting manual rename for user {user_id}: {e}")

# ==================== ENHANCED QUEUE SYSTEM ====================
class PriorityQueue:
    def __init__(self):
        self.queue = []
        self.task_counter = 0
        self.current_task = None
        self.current_task_id = None
        self.is_processing = False
        self.paused_tasks = []
        self.admin_priority_mode = False
        self.lock = asyncio.Lock()
        self.completed_tasks = 0
        self.failed_tasks = 0
        self.task_start_time = None
        self.admin_mode_active = False
        self.timeout_seconds = Config.TIMEOUT_SECONDS
        self.task_retry_count = {}
        self.max_retries = 2
        self.user_tasks = {}
        self.task_map = {}

    def add_to_queue(self, message: Message, user_id: int, encode_mode: bool = False, compress_quality: Optional[str] = None):
        task_id = f"{user_id}_{int(time.time())}_{self.task_counter}"
        priority = 0 if user_id in Config.ADMIN else 1
        queue_position = len(self.queue) + 1
        queue_item = {
            'task_id': task_id,
            'message_id': message.id,
            'chat_id': message.chat.id,
            'user_id': user_id,
            'file_name': '',
            'file_size': 0,
            'media_type': '',
            'added_time': time.time(),
            'status': 'waiting',
            'priority': priority,
            'is_admin': user_id in Config.ADMIN,
            'retry_count': 0,
            'queue_position': queue_position,
            'completed': False,
            'success': False,
            'cancelled': False,
            'manual_filename': None,
            'encode_mode': encode_mode,
            'compress_quality': compress_quality
        }
        if message.document:
            queue_item['file_name'] = message.document.file_name or "file"
            queue_item['file_size'] = message.document.file_size
            queue_item['media_type'] = 'document'
        elif message.video:
            queue_item['file_name'] = message.video.file_name or "video.mp4"
            queue_item['file_size'] = message.video.file_size
            queue_item['media_type'] = 'video'
        elif message.audio:
            queue_item['file_name'] = message.audio.file_name or "audio.mp3"
            queue_item['file_size'] = message.audio.file_size
            queue_item['media_type'] = 'audio'
        heapq.heappush(self.queue, (priority, time.time(), self.task_counter, queue_item))
        self.task_counter += 1
        self.task_map[task_id] = queue_item
        if user_id not in self.user_tasks:
            self.user_tasks[user_id] = []
        self.user_tasks[user_id].append(task_id)
        return queue_position, task_id, queue_item

    def add_manual_task_to_queue(self, message: Message, user_id: int, manual_filename: str):
        task_id = f"{user_id}_manual_{int(time.time())}_{self.task_counter}"
        priority = 0 if user_id in Config.ADMIN else 1
        queue_position = len(self.queue) + 1
        queue_item = {
            'task_id': task_id,
            'message_id': message.id,
            'chat_id': message.chat.id,
            'user_id': user_id,
            'file_name': '',
            'file_size': 0,
            'media_type': '',
            'added_time': time.time(),
            'status': 'waiting',
            'priority': priority,
            'is_admin': user_id in Config.ADMIN,
            'retry_count': 0,
            'queue_position': queue_position,
            'completed': False,
            'success': False,
            'cancelled': False,
            'manual_filename': manual_filename,
            'encode_mode': False,
            'compress_quality': None,
        }
        if message.document:
            queue_item['file_name'] = message.document.file_name or "file"
            queue_item['file_size'] = message.document.file_size
            queue_item['media_type'] = 'document'
        elif message.video:
            queue_item['file_name'] = message.video.file_name or "video.mp4"
            queue_item['file_size'] = message.video.file_size
            queue_item['media_type'] = 'video'
        elif message.audio:
            queue_item['file_name'] = message.audio.file_name or "audio.mp3"
            queue_item['file_size'] = message.audio.file_size
            queue_item['media_type'] = 'audio'
        heapq.heappush(self.queue, (priority, time.time(), self.task_counter, queue_item))
        self.task_counter += 1
        self.task_map[task_id] = queue_item
        if user_id not in self.user_tasks:
            self.user_tasks[user_id] = []
        self.user_tasks[user_id].append(task_id)
        return queue_position, task_id, queue_item

    def get_next_task(self):
        while self.queue:
            priority, timestamp, counter, task = heapq.heappop(self.queue)
            if task.get('cancelled', False):
                uid = task['user_id']
                tid = task['task_id']
                if uid in self.user_tasks and tid in self.user_tasks[uid]:
                    self.user_tasks[uid].remove(tid)
                    if not self.user_tasks[uid]:
                        del self.user_tasks[uid]
                if tid in self.task_map:
                    del self.task_map[tid]
                continue
            return task
        return None

    def get_queue_length(self):
        return len([item for item in self.queue if not item[3].get('cancelled', False)])

    def clear_queue(self):
        self.queue.clear()
        self.user_tasks.clear()
        self.task_map.clear()

    async def clear_user_queue(self, user_id: int) -> Tuple[int, bool]:
        async with self.lock:
            removed_count = 0
            has_current = False
            if self.is_processing and self.current_task and self.current_task['user_id'] == user_id:
                has_current = True
            if user_id in self.user_tasks:
                for task_id in list(self.user_tasks[user_id]):
                    task = self.task_map.get(task_id)
                    if task and task_id != self.current_task_id:
                        if not task.get('cancelled', False):
                            task['cancelled'] = True
                            removed_count += 1
                if has_current:
                    self.user_tasks[user_id] = [self.current_task_id]
                else:
                    del self.user_tasks[user_id]
            return removed_count, has_current

    def get_queue_info(self):
        waiting_tasks = [item for item in self.queue if not item[3].get('cancelled', False)]
        total_waiting = len(waiting_tasks)
        sorted_queue = sorted(waiting_tasks, key=lambda x: (x[0], x[1]))
        info = {
            'total': total_waiting,
            'current': self.current_task,
            'is_processing': self.is_processing,
            'completed': self.completed_tasks,
            'failed': self.failed_tasks,
            'paused': len(self.paused_tasks),
            'admin_priority': self.admin_priority_mode,
            'admin_mode': self.admin_mode_active,
            'waiting_list': [],
            'admin_waiting': 0,
            'user_waiting': 0,
            'user_stats': {}
        }
        admin_count = 0
        for i, (priority, timestamp, counter, item) in enumerate(sorted_queue):
            info['waiting_list'].append({
                'position': i + 1,
                'task_id': item['task_id'],
                'file_name': item['file_name'][:50] if item['file_name'] else 'Unknown',
                'user_id': item['user_id'],
                'is_admin': item.get('is_admin', False),
                'priority': 'High' if priority == 0 else 'Normal',
                'added_time': item.get('added_time', 0),
                'waiting_time': time.time() - item['added_time']
            })
            if item.get('is_admin', False):
                admin_count += 1
        info['admin_waiting'] = admin_count
        info['user_waiting'] = total_waiting - admin_count
        user_stats = {}
        for _, _, _, item in waiting_tasks:
            uid = item['user_id']
            user_stats[uid] = user_stats.get(uid, 0) + 1
        info['user_stats'] = user_stats
        return info

    def check_timeout(self):
        if self.is_processing and self.task_start_time:
            elapsed = time.time() - self.task_start_time
            return elapsed > self.timeout_seconds
        return False

    def mark_task_completed(self, task_id, success=True):
        if self.current_task and self.current_task['task_id'] == task_id:
            self.current_task['completed'] = True
            self.current_task['success'] = success
            self.current_task['completed_time'] = time.time()

processing_queue = PriorityQueue()

# ==================== DATABASE ====================
class Database:
    def __init__(self):
        self.client = motor.motor_asyncio.AsyncIOMotorClient(Config.DB_URL)
        self.db = self.client[Config.DB_NAME]
        self.col = self.db.users
        self.groups_col = self.db.groups

    async def init_db(self):
        try:
            groups = await self.groups_col.find({}).to_list(length=None)
            Config.ALLOWED_GROUPS = {group['_id'] for group in groups}
            print(f"Loaded {len(Config.ALLOWED_GROUPS)} allowed groups")
        except Exception as e:
            print(f"Error loading groups: {e}")
            Config.ALLOWED_GROUPS = set()

    def new_user(self, user_id):
        return {
            "_id": int(user_id),
            "join_date": datetime.now().isoformat(),
            "file_id": None,
            "caption": None,
            "metadata": True,
            "title": "Encoded by @AnimeMultiDub",
            "author": "@AnimeMultiDub",
            "artist": "@AnimeMultiDub",
            "audio": "By @AnimeMultiDub",
            "subtitle": "By @AnimeMultiDub",
            "video": "Encoded By @AnimeMultiDub",
            "format_template": None,
            "media_type": "document",
            "ban_status": {
                "is_banned": False,
                "ban_duration": 0,
                "banned_on": datetime.max.isoformat(),
                "ban_reason": ''
            },
            "dump_channels": [],
            "dump_enabled": False,
            "active_dump_channel": None,
            "sequence_mode": 1,
        }

    async def add_user(self, user_id):
        try:
            await self.col.update_one(
                {"_id": int(user_id)},
                {"$setOnInsert": self.new_user(user_id)},
                upsert=True
            )
        except Exception as e:
            print(f"add_user error (ignored): {e}")

    async def is_user_exist(self, user_id):
        user = await self.col.find_one({"_id": int(user_id)})
        return bool(user)

    async def total_users_count(self):
        return await self.col.count_documents({})

    async def get_all_users(self):
        return self.col.find({})

    async def delete_user(self, user_id):
        await self.col.delete_many({"_id": int(user_id)})

    async def set_thumbnail(self, user_id, file_id):
        await self.col.update_one({"_id": int(user_id)}, {"$set": {"file_id": file_id}})

    async def get_thumbnail(self, user_id):
        user = await self.col.find_one({"_id": int(user_id)})
        return user.get("file_id", None) if user else None

    async def set_caption(self, user_id, caption):
        await self.col.update_one({"_id": int(user_id)}, {"$set": {"caption": caption}})

    async def get_caption(self, user_id):
        user = await self.col.find_one({"_id": int(user_id)})
        return user.get("caption", None) if user else None

    async def set_format_template(self, user_id, format_template):
        await self.col.update_one({"_id": int(user_id)}, {"$set": {"format_template": format_template}})

    async def get_format_template(self, user_id):
        user = await self.col.find_one({"_id": int(user_id)})
        return user.get("format_template", None) if user else None

    async def set_media_preference(self, user_id, media_type):
        await self.col.update_one({"_id": int(user_id)}, {"$set": {"media_type": media_type}})

    async def get_media_preference(self, user_id):
        user = await self.col.find_one({"_id": int(user_id)})
        return user.get("media_type", "document") if user else "document"

    async def get_metadata(self, user_id):
        user = await self.col.find_one({"_id": int(user_id)})
        return user.get("metadata", True) if user else True

    async def set_metadata(self, user_id, metadata):
        await self.col.update_one({"_id": int(user_id)}, {"$set": {"metadata": metadata}})

    async def get_title(self, user_id):
        user = await self.col.find_one({"_id": int(user_id)})
        return user.get("title", "Encoded by @AnimeMultiDub") if user else "Encoded by @AnimeMultiDub"

    async def set_title(self, user_id, title):
        await self.col.update_one({"_id": int(user_id)}, {"$set": {"title": title}})

    async def get_author(self, user_id):
        user = await self.col.find_one({"_id": int(user_id)})
        return user.get("author", "@AnimeMultiDub") if user else "@AnimeMultiDub"

    async def set_author(self, user_id, author):
        await self.col.update_one({"_id": int(user_id)}, {"$set": {"author": author}})

    async def get_artist(self, user_id):
        user = await self.col.find_one({"_id": int(user_id)})
        return user.get("artist", "@AnimeMultiDub") if user else "@AnimeMultiDub"

    async def set_artist(self, user_id, artist):
        await self.col.update_one({"_id": int(user_id)}, {"$set": {"artist": artist}})

    async def get_audio(self, user_id):
        user = await self.col.find_one({"_id": int(user_id)})
        return user.get("audio", "By @AnimeMultiDub") if user else "By @AnimeMultiDub"

    async def set_audio(self, user_id, audio):
        await self.col.update_one({"_id": int(user_id)}, {"$set": {"audio": audio}})

    async def get_subtitle(self, user_id):
        user = await self.col.find_one({"_id": int(user_id)})
        return user.get("subtitle", "By @AnimeMultiDub") if user else "By @AnimeMultiDub"

    async def set_subtitle(self, user_id, subtitle):
        await self.col.update_one({"_id": int(user_id)}, {"$set": {"subtitle": subtitle}})

    async def get_video(self, user_id):
        user = await self.col.find_one({"_id": int(user_id)})
        return user.get("video", "Encoded By @AnimeMultiDub") if user else "Encoded By @AnimeMultiDub"

    async def set_video(self, user_id, video):
        await self.col.update_one({"_id": int(user_id)}, {"$set": {"video": video}})

    # ---------- Sequence Mode ----------
    async def get_sequence_mode(self, user_id):
        user = await self.col.find_one({"_id": int(user_id)})
        return user.get("sequence_mode", 1) if user else 1

    async def set_sequence_mode(self, user_id, mode: int):
        await self.col.update_one({"_id": int(user_id)}, {"$set": {"sequence_mode": mode}})

    # ---------- Dump Channel Methods ----------
    async def get_dump_channels(self, user_id):
        user = await self.col.find_one({"_id": int(user_id)})
        if not user:
            return []
        channels = user.get("dump_channels", [])
        clean_channels = []
        for c in channels:
            if isinstance(c, int):
                clean_channels.append(c)
            elif isinstance(c, dict):
                ch_id = c.get('channel_id') or c.get('id') or c.get('_id')
                if ch_id is not None:
                    clean_channels.append(int(ch_id))
        return clean_channels

    async def add_dump_channel(self, user_id, channel_id):
        await self.col.update_one(
            {"_id": int(user_id)},
            {"$addToSet": {"dump_channels": int(channel_id)}}
        )

    async def remove_dump_channel(self, user_id, channel_id):
        await self.col.update_one(
            {"_id": int(user_id)},
            {"$pull": {"dump_channels": int(channel_id)}}
        )

    async def get_dump_enabled(self, user_id):
        user = await self.col.find_one({"_id": int(user_id)})
        return user.get("dump_enabled", False) if user else False

    async def set_dump_enabled(self, user_id, enabled: bool):
        await self.col.update_one({"_id": int(user_id)}, {"$set": {"dump_enabled": enabled}})

    async def get_active_dump_channel(self, user_id):
        user = await self.col.find_one({"_id": int(user_id)})
        return user.get("active_dump_channel", None) if user else None

    async def set_active_dump_channel(self, user_id, channel_id):
        await self.col.update_one(
            {"_id": int(user_id)},
            {"$set": {"active_dump_channel": int(channel_id) if channel_id else None}}
        )
    # -------------------------------------------

    async def add_group(self, group_id):
        group = {
            "_id": int(group_id),
            "added_date": datetime.now().isoformat(),
            "added_by": "admin"
        }
        await self.groups_col.update_one({"_id": int(group_id)}, {"$set": group}, upsert=True)
        Config.ALLOWED_GROUPS.add(int(group_id))

    async def remove_group(self, group_id):
        await self.groups_col.delete_one({"_id": int(group_id)})
        Config.ALLOWED_GROUPS.discard(int(group_id))

    async def is_group_allowed(self, group_id):
        return int(group_id) in Config.ALLOWED_GROUPS

    async def get_all_groups(self):
        groups = await self.groups_col.find({}).to_list(length=None)
        return groups

db = Database()

# ==================== UTILITY FUNCTIONS ====================
def humanbytes(size):
    if not size:
        return "0 B"
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size < 1024.0:
            return f"{size:.2f} {unit}"
        size /= 1024.0
    return f"{size:.2f} PB"

def TimeFormatter(milliseconds: int) -> str:
    seconds, milliseconds = divmod(int(milliseconds), 1000)
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    days, hours = divmod(hours, 24)
    tmp = ((str(days) + "ᴅ, ") if days else "") + \
          ((str(hours) + "ʜ, ") if hours else "") + \
          ((str(minutes) + "ᴍ, ") if minutes else "") + \
          ((str(seconds) + "ꜱ, ") if seconds else "")
    return tmp[:-2] or "0 s"

async def progress_for_pyrogram(current, total, ud_type, message, start):
    now = time.time()
    diff = now - start
    if round(diff % 10.00) == 0 or current == total:
        percentage = current * 100 / total
        speed = current / diff if diff > 0 else 0
        elapsed_time = round(diff) * 1000
        time_to_completion = round((total - current) / speed) * 1000 if speed > 0 else 0
        estimated_total_time = elapsed_time + time_to_completion
        elapsed_time = TimeFormatter(milliseconds=elapsed_time)
        estimated_total_time = TimeFormatter(milliseconds=time_to_completion)
        progress = "{0}{1}".format(
            ''.join(["█" for _ in range(math.floor(percentage / 5))]),
            ''.join(["░" for _ in range(20 - math.floor(percentage / 5))])
        )
        tmp = f"""\n
<b>» Size</b> : {humanbytes(current)} | {humanbytes(total)}
<b>» Done</b> : {round(percentage, 2)}%
<b>» Speed</b> : {humanbytes(speed)}/s
<b>» ETA</b> : {estimated_total_time if estimated_total_time else "0 s"} """
        try:
            if message and hasattr(message, 'edit'):
                await message.edit(text=f"{ud_type}\n\n{progress}{tmp}")
        except:
            pass

async def safe_send_message(chat_id, text, reply_to_message_id=None, retry_count=3):
    for attempt in range(retry_count):
        try:
            return await app.send_message(
                chat_id=chat_id,
                text=text,
                reply_to_message_id=reply_to_message_id
            )
        except FloodWait as e:
            if attempt < retry_count - 1:
                await asyncio.sleep(e.value)
                continue
            else:
                raise
        except Exception as e:
            print(f"Error sending message: {e}")
            if attempt < retry_count - 1:
                await asyncio.sleep(2)
                continue
            else:
                raise

async def cleanup_files(*paths):
    for path in paths:
        try:
            if path and os.path.exists(path):
                if os.path.isfile(path):
                    os.remove(path)
                elif os.path.isdir(path):
                    shutil.rmtree(path)
        except Exception as e:
            print(f"Error removing {path}: {e}")

async def process_thumbnail(thumb_path):
    if not thumb_path or not os.path.exists(thumb_path):
        return None
    try:
        with Image.open(thumb_path) as img:
            if img.mode != 'RGB':
                img = img.convert('RGB')
            img.thumbnail((320, 320))
            img.save(thumb_path, "JPEG", quality=85)
        return thumb_path
    except Exception as e:
        print(f"Thumbnail processing error: {e}")
        await cleanup_files(thumb_path)
        return None

async def add_metadata_correct(input_path, output_path, user_id):
    ffmpeg_path = None
    for path in ['ffmpeg', '/usr/bin/ffmpeg', '/usr/local/bin/ffmpeg', '/bin/ffmpeg']:
        if shutil.which(path):
            ffmpeg_path = path
            break
    if not ffmpeg_path:
        raise RuntimeError("FFmpeg not found.")
    title = await db.get_title(user_id)
    artist = await db.get_artist(user_id)
    author = await db.get_author(user_id)
    video_title = await db.get_video(user_id)
    audio_title = await db.get_audio(user_id)
    subtitle_title = await db.get_subtitle(user_id)
    def escape_metadata(text):
        return text.replace('"', '\\"').replace("'", "\\'")
    cmd = [
        ffmpeg_path,
        '-i', input_path,
        '-map', '0',
        '-c:v', 'copy',
        '-c:a', 'copy',
        '-c:s', 'copy',
        '-metadata', f'title={escape_metadata(title)}',
        '-metadata', f'artist={escape_metadata(artist)}',
        '-metadata', f'author={escape_metadata(author)}',
        '-metadata:s:v', f'title={escape_metadata(video_title)}',
        '-metadata:s:a', f'title={escape_metadata(audio_title)}',
        '-metadata:s:s', f'title={escape_metadata(subtitle_title)}',
        '-y',
        output_path
    ]
    try:
        process = await asyncio.wait_for(
            asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            ),
            timeout=180
        )
        stdout, stderr = await process.communicate()
        if process.returncode != 0:
            alt_cmd = [
                ffmpeg_path, '-i', input_path,
                '-map', '0',
                '-c', 'copy',
                '-metadata', f'title={escape_metadata(title)}',
                '-metadata', f'artist={escape_metadata(artist)}',
                '-metadata', f'author={escape_metadata(author)}',
                '-y', output_path
            ]
            process2 = await asyncio.wait_for(
                asyncio.create_subprocess_exec(
                    *alt_cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                ),
                timeout=180
            )
            await process2.communicate()
            if process2.returncode != 0:
                shutil.copy2(input_path, output_path)
                return output_path
    except asyncio.TimeoutError:
        shutil.copy2(input_path, output_path)
        return output_path
    if not os.path.exists(output_path) or os.path.getsize(output_path) == 0:
        shutil.copy2(input_path, output_path)
    return output_path

# ==================== HELPER: PICK OUTPUT EXTENSION FOR ENCODING ====================
def _pick_encode_ext(original_ext: str) -> str:
    ext = original_ext.lower()
    if ext in ('.mkv', '.mp4'):
        return ext
    return '.mkv'

# ==================== VIDEO ENCODING (PRESERVES ALL STREAMS) ====================
ENCODE_QUALITIES = [
    (480,  "480p"),
    (720,  "720p"),
    (1080, "1080p"),
]

async def encode_video(input_path: str, output_path: str, height: int,
                       status_msg=None, quality_label_str: str = "") -> bool:
    ffmpeg_path = None
    for path in ['ffmpeg', '/usr/bin/ffmpeg', '/usr/local/bin/ffmpeg', '/bin/ffmpeg']:
        if shutil.which(path):
            ffmpeg_path = path
            break
    if not ffmpeg_path:
        print("FFmpeg not found — cannot encode.")
        return False

    out_ext = os.path.splitext(output_path)[1].lower()

    if status_msg:
        try:
            await status_msg.edit_text(
                f"🎬 **Encoding {quality_label_str}...**\n"
                f"This may take a while depending on file size.\n"
                f"Preserving all audio and subtitle tracks."
            )
        except:
            pass

    def _build_cmd(sub_codec: str, include_subs: bool) -> list:
        cmd = [
            ffmpeg_path,
            '-i', input_path,
            '-map', '0',
            '-c:v', 'libx264',
            '-vf', f'scale=-2:{height}',
            '-crf', '23',
            '-preset', 'fast',
            '-c:a', 'copy',
            '-map_metadata', '0',
            '-map_chapters', '0',
        ]
        if include_subs:
            cmd += ['-c:s', sub_codec]
        else:
            cmd += ['-sn']
        cmd += ['-y', output_path]
        return cmd

    if out_ext == '.mkv':
        primary_cmd = _build_cmd('copy', include_subs=True)
        fallback_cmd = None
    else:
        primary_cmd = _build_cmd('mov_text', include_subs=True)
        fallback_cmd = _build_cmd('copy', include_subs=False)

    async def _run(cmd):
        proc = await asyncio.wait_for(
            asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            ),
            timeout=3600
        )
        stdout, stderr = await proc.communicate()
        return proc.returncode, stderr.decode(errors='ignore')

    try:
        ret, err = await _run(primary_cmd)
        if ret != 0:
            print(f"FFmpeg encode primary cmd failed ({quality_label_str}): {err[-500:]}")
            if fallback_cmd is not None:
                print(f"Retrying without subtitles ({quality_label_str})...")
                ret2, err2 = await _run(fallback_cmd)
                if ret2 != 0:
                    print(f"FFmpeg encode fallback also failed ({quality_label_str}): {err2[-300:]}")
                    return False
                print(f"⚠️ Subtitles dropped for {quality_label_str} (image-based subs not supported in MP4)")
            else:
                fallback_nosub = _build_cmd('copy', include_subs=False)
                ret3, err3 = await _run(fallback_nosub)
                if ret3 != 0:
                    print(f"FFmpeg encode MKV fallback failed ({quality_label_str}): {err3[-300:]}")
                    return False

        return os.path.exists(output_path) and os.path.getsize(output_path) > 0

    except asyncio.TimeoutError:
        print(f"FFmpeg encode timed out ({quality_label_str})")
        return False
    except Exception as e:
        print(f"FFmpeg encode exception ({quality_label_str}): {e}")
        return False

# ==================== FILE INFO EXTRACTION HELPERS ====================
def extract_file_info(file_name: str):
    season = 0
    episode = 0
    quality = 0
    season_patterns = [
        r'\[S(\d+)\]', r'Season\s*(\d+)', r'Saison\s*(\d+)',
        r'S(\d+)[\s\.\-_]', r'S(\d+)$', r'S(\d+)',
    ]
    for pat in season_patterns:
        m = re.search(pat, file_name, re.IGNORECASE)
        if m:
            season = int(m.group(1))
            break
    ep_patterns = [
        r'\[E(?:P)?(\d+)\]', r'Episode\s*(\d+)', r'E(?:P)?(\d+)',
        r'Ep(\d+)', r'\bE(?:P)?(\d+)\b',
    ]
    for pat in ep_patterns:
        m = re.search(pat, file_name, re.IGNORECASE)
        if m:
            episode = int(m.group(1))
            break
    quality_map = {
        '4k': 4, '2160p': 4, 'uhd': 4,
        '2k': 3, '1440p': 3, 'qhd': 3,
        '1080p': 2, 'fhd': 2, 'full hd': 2,
        '720p': 1, 'hd': 1,
        '480p': 0, 'sd': 0, '360p': 0,
    }
    fname_lower = file_name.lower()
    for key in sorted(quality_map, key=lambda k: len(k), reverse=True):
        if key in fname_lower:
            quality = quality_map[key]
            break
    return season, quality, episode

def check_template_needs_variables(format_template: str) -> set:
    needed = set()
    for var in ['{season}', '{episode}', '{quality}']:
        if var in format_template:
            needed.add(var)
    return needed

def check_extraction_failed(format_template: str, season: int, episode: int, quality_str: str) -> list:
    failed = []
    needed = check_template_needs_variables(format_template)
    if '{season}' in needed and season == 0:
        failed.append('{season}')
    if '{episode}' in needed and episode == 0:
        failed.append('{episode}')
    return failed

def sort_key_from_message(msg: Message):
    """Legacy single-mode sort key (Season > Quality > Episode) kept for compatibility."""
    fname = get_msg_fname(msg)
    season, quality, episode = extract_file_info(fname)
    return (season, quality, episode)

# ==================== DUMP CHANNEL HELPER FUNCTIONS (from bot2) ====================

def _is_channel_type(chat_type) -> bool:
    """Enum-safe check: works with Pyrogram v1 (strings) and v2 (ChatType enum)."""
    if chat_type is None:
        return False
    if _PYROGRAM_ENUMS and ChatType is not None:
        try:
            return chat_type in (ChatType.CHANNEL, ChatType.SUPERGROUP)
        except Exception:
            pass
    type_str = str(chat_type).upper()
    return 'CHANNEL' in type_str or 'SUPERGROUP' in type_str

def _is_admin_status(member_status) -> bool:
    """Enum-safe check for admin/owner status."""
    if member_status is None:
        return False
    if _PYROGRAM_ENUMS and ChatMemberStatus is not None:
        try:
            return member_status in (
                ChatMemberStatus.ADMINISTRATOR,
                ChatMemberStatus.OWNER,
            )
        except Exception:
            pass
    status_str = str(member_status).upper()
    return any(s in status_str for s in ('ADMINISTRATOR', 'OWNER', 'CREATOR'))

def _normalize_channel_id(raw: int) -> int:
    """Convert a bare channel ID to the -100xxx format if needed."""
    s = str(abs(raw))
    if str(raw).startswith('-100'):
        return raw
    if str(raw).startswith('-'):
        return raw
    return int(f"-100{s}")

def _extract_fwd_channel(message: Message):
    """
    Try every known way Pyrogram exposes a forwarded channel.
    Returns (channel_id, chat_obj) or (None, None).
    """
    # 1) forward_from_chat (most common, Pyrogram v1/v2)
    fwd = getattr(message, 'forward_from_chat', None)
    if fwd and _is_channel_type(getattr(fwd, 'type', None)):
        return fwd.id, fwd

    # 2) forward_origin → MessageOriginChannel (Pyrogram ≥ 2.x)
    origin = getattr(message, 'forward_origin', None)
    if origin:
        chat = getattr(origin, 'chat', None)
        if chat and _is_channel_type(getattr(chat, 'type', None)):
            return chat.id, chat

    # 3) sender_chat (sometimes set on forwarded channel posts)
    sc = getattr(message, 'sender_chat', None)
    if sc and _is_channel_type(getattr(sc, 'type', None)):
        return sc.id, sc

    # 4) Raw fwd_from fallback for channels that hide identity
    for raw_attr in ('_raw', 'raw', '_message'):
        raw = getattr(message, raw_attr, None)
        if raw is None:
            continue
        fwd_raw = getattr(raw, 'fwd_from', None)
        if not fwd_raw:
            continue
        from_id_obj = getattr(fwd_raw, 'from_id', None)
        if from_id_obj is None:
            continue
        channel_id_raw = getattr(from_id_obj, 'channel_id', None)
        if channel_id_raw:
            return _normalize_channel_id(channel_id_raw), None

    return None, None

async def _do_add_dump_channel(user_id: int, channel_id: int, client, reply_msg):
    """
    Validate and persist a dump channel.
    Uses enum-safe helpers to work with both Pyrogram v1 and v2.
    """
    try:
        chat = await client.get_chat(channel_id)
    except Exception as e:
        await reply_msg.reply_text(
            f"❌ Cannot access channel `{channel_id}`.\n"
            f"Make sure the bot is an **admin** there.\nError: `{e}`")
        return

    if not _is_channel_type(getattr(chat, 'type', None)):
        await reply_msg.reply_text(
            "❌ That does not appear to be a channel or supergroup.\n"
            f"Detected type: `{chat.type}`")
        return

    try:
        me  = await client.get_me()
        mbr = await client.get_chat_member(channel_id, me.id)

        is_admin_member = _is_admin_status(getattr(mbr, 'status', None))
        can_post = True
        if hasattr(mbr, 'privileges') and mbr.privileges is not None:
            can_post = getattr(mbr.privileges, 'can_post_messages', False)
        elif hasattr(mbr, 'can_post_messages'):
            can_post = getattr(mbr, 'can_post_messages', True)

        if not is_admin_member and not can_post:
            await reply_msg.reply_text(
                "❌ Bot is not an admin (or lacks **Post Messages** permission) in that channel.")
            return
    except Exception as e:
        print(f"Could not verify bot membership in {channel_id}: {e} — continuing anyway")

    current = await db.get_dump_channels(user_id)
    if channel_id in current:
        await reply_msg.reply_text("⚠️ That channel is already in your dump list.")
        add_dump_waiting.pop(user_id, None)
        return

    await db.add_dump_channel(user_id, channel_id)
    add_dump_waiting.pop(user_id, None)

    chat_title = getattr(chat, 'title', str(channel_id)) or str(channel_id)
    await reply_msg.reply_text(
        f"✅ **Dump channel added!**\n"
        f"Channel: `{channel_id}` ({chat_title})\n\n"
        "Use /send_dump to select it for sending renamed files.\n"
        "Use /list_dump_channels to see all.")

# ==================== QUEUE WORKER ====================
async def queue_worker():
    print("👷 Queue Worker: Started")
    while True:
        if renaming_paused:
            await asyncio.sleep(2)
            continue
        try:
            if processing_queue.get_queue_length() == 0:
                await asyncio.sleep(2)
                continue
            if processing_queue.is_processing:
                if processing_queue.check_timeout():
                    print(f"⚠️ Task timeout detected: {processing_queue.current_task_id}")
                    processing_queue.is_processing = False
                    processing_queue.current_task = None
                    processing_queue.current_task_id = None
                    processing_queue.task_start_time = None
                    processing_queue.failed_tasks += 1
                await asyncio.sleep(1)
                continue
            async with processing_queue.lock:
                processing_queue.is_processing = True
                task = processing_queue.get_next_task()
                if not task:
                    processing_queue.is_processing = False
                    await asyncio.sleep(2)
                    continue
                processing_queue.current_task = task
                processing_queue.current_task_id = task['task_id']
                processing_queue.task_start_time = time.time()
                task['status'] = 'processing'
                task['start_time'] = time.time()
                print(f"Processing task: {task['task_id']} - Admin: {task.get('is_admin')}")
                task_user_id = task['user_id']
                try:
                    message = await app.get_messages(
                        chat_id=task['chat_id'],
                        message_ids=task['message_id']
                    )
                    if not message:
                        print(f"Message not found: {task['message_id']}")
                        processing_queue.completed_tasks += 1
                        processing_queue.failed_tasks += 1
                        processing_queue.is_processing = False
                        processing_queue.current_task = None
                        processing_queue.current_task_id = None
                        asyncio.create_task(_trigger_manual_rename_if_ready(task_user_id))
                        continue
                    try:
                        await process_queue_file(message, task['user_id'], task)
                        processing_queue.completed_tasks += 1
                        processing_queue.mark_task_completed(task['task_id'], success=True)
                        print(f"✅ Task completed successfully: {task['task_id']}")
                    except asyncio.TimeoutError:
                        print(f"⏰ Task {task['task_id']} timed out")
                        processing_queue.failed_tasks += 1
                        processing_queue.mark_task_completed(task['task_id'], success=False)
                    except Exception as e:
                        print(f"❌ Error in task processing: {str(e)[:100]}")
                        processing_queue.failed_tasks += 1
                        processing_queue.mark_task_completed(task['task_id'], success=False)
                except Exception as e:
                    print(f"❌ Error getting message: {e}")
                    processing_queue.failed_tasks += 1
                    processing_queue.mark_task_completed(task['task_id'], success=False)
                finally:
                    processing_queue.is_processing = False
                    processing_queue.current_task = None
                    processing_queue.current_task_id = None
                    processing_queue.task_start_time = None
                    await asyncio.sleep(1)
                    asyncio.create_task(_trigger_manual_rename_if_ready(task_user_id))
        except Exception as e:
            print(f"⚠️ Queue worker error: {e}")
            await asyncio.sleep(5)

# ==================== SEND HELPER ====================
async def _send_file(target_chat_id, output_path, send_as, final_filename, caption,
                     thumb_path, duration, message, status_msg, upload_start, user_id,
                     dump_enabled, active_dump_channel):
    """Upload a single file and mirror to dump channels if needed."""
    sent_msg = None
    if send_as == "document":
        sent_msg = await app.send_document(
            chat_id=target_chat_id,
            document=output_path,
            caption=caption[:1024] if caption else None,
            thumb=thumb_path,
            file_name=final_filename,
            progress=progress_for_pyrogram,
            progress_args=("📤 Uploading...", status_msg if status_msg else message, upload_start),
            reply_to_message_id=message.id if message and target_chat_id == message.chat.id else None
        )
    elif send_as == "video":
        try:
            sent_msg = await app.send_video(
                chat_id=target_chat_id,
                video=output_path,
                caption=caption[:1024] if caption else None,
                thumb=thumb_path,
                duration=duration,
                file_name=final_filename,
                progress=progress_for_pyrogram,
                progress_args=("📤 Uploading...", status_msg if status_msg else message, upload_start),
                reply_to_message_id=message.id if message and target_chat_id == message.chat.id else None
            )
        except Exception as upload_error:
            print(f"Video upload failed, falling back to document: {upload_error}")
            sent_msg = await app.send_document(
                chat_id=target_chat_id,
                document=output_path,
                caption=caption[:1024] if caption else None,
                thumb=thumb_path,
                file_name=final_filename,
                progress=progress_for_pyrogram,
                progress_args=("📤 Uploading (fallback)...", status_msg if status_msg else message, upload_start),
                reply_to_message_id=message.id if message and target_chat_id == message.chat.id else None
            )
    elif send_as == "audio":
        sent_msg = await app.send_audio(
            chat_id=target_chat_id,
            audio=output_path,
            caption=caption[:1024] if caption else None,
            thumb=thumb_path,
            duration=duration,
            file_name=final_filename,
            progress=progress_for_pyrogram,
            progress_args=("📤 Uploading...", status_msg if status_msg else message, upload_start),
            reply_to_message_id=message.id if message and target_chat_id == message.chat.id else None
        )
    else:
        sent_msg = await app.send_document(
            chat_id=target_chat_id,
            document=output_path,
            caption=caption[:1024] if caption else None,
            thumb=thumb_path,
            file_name=final_filename,
            progress=progress_for_pyrogram,
            progress_args=("📤 Uploading...", status_msg if status_msg else message, upload_start),
            reply_to_message_id=message.id if message and target_chat_id == message.chat.id else None
        )

    if sent_msg and not (dump_enabled and active_dump_channel):
        if message and message.chat.type != "private" and message.chat.id != user_id:
            try:
                await sent_msg.copy(user_id)
            except Exception as e:
                print(f"Failed to send copy to user {user_id}: {e}")
        dump_channels = await db.get_dump_channels(user_id)
        for channel_id in dump_channels:
            try:
                await sent_msg.copy(channel_id)
            except BadRequest as e:
                if "PEER_ID_INVALID" in str(e):
                    await db.remove_dump_channel(user_id, channel_id)
                    print(f"Removed invalid dump channel {channel_id}")
                else:
                    print(f"Failed to send to dump channel {channel_id}: {e}")
            except Exception as e:
                print(f"Failed to send to dump channel {channel_id}: {e}")

    return sent_msg

# ==================== TORRENT PROCESSING FUNCTIONS ====================

async def process_torrent_file(file_path: str, user_id: int, status_msg=None):
    file_name = os.path.basename(file_path)
    base_name = os.path.splitext(file_name)[0]
    original_ext = os.path.splitext(file_name)[1]
    file_size = os.path.getsize(file_path)

    ext_lower = original_ext.lower()
    if ext_lower in TORRENT_VIDEO_EXTS:
        media_type = "video"
        duration = 0
    elif ext_lower in TORRENT_AUDIO_EXTS:
        media_type = "audio"
        duration = 0
    else:
        print(f"Skipping non-media torrent file: {file_name}")
        return

    season_int, _, episode_int = extract_file_info(file_name)
    season = f"{season_int:02d}" if season_int else 'None'
    episode = f"{episode_int:02d}" if episode_int else 'None'

    quality = "HD"
    fname_lower = file_name.lower()
    if '4k' in fname_lower or '2160p' in fname_lower:
        quality = "4K"
    elif '2k' in fname_lower or '1440p' in fname_lower:
        quality = "2K"
    elif '1080p' in fname_lower:
        quality = "1080p"
    elif '720p' in fname_lower:
        quality = "720p"
    elif '480p' in fname_lower:
        quality = "480p"

    format_template = await db.get_format_template(user_id)
    if format_template:
        new_filename = format_template
        replacements = {
            '{filename}': base_name,
            '{season}': season,
            '{episode}': episode,
            '{quality}': quality,
            '{filesize}': humanbytes(file_size),
            '{duration}': '00:00:00',
        }
        for k, v in replacements.items():
            new_filename = new_filename.replace(k, v)
    else:
        new_filename = base_name

    new_filename = re.sub(r'[<>:"/\\|?*]', '', new_filename).strip()

    media_pref = await db.get_media_preference(user_id)
    if media_pref == "video":
        send_as = "video"
        display_ext = original_ext
    elif media_pref == "audio":
        send_as = "audio"
        display_ext = original_ext if media_type == "audio" else ".mp3"
    else:
        send_as = "document"
        display_ext = original_ext

    final_filename = new_filename + display_ext

    output_path = file_path
    metadata_enabled = await db.get_metadata(user_id)
    if metadata_enabled:
        try:
            meta_path = f"temp/{user_id}_torrent_meta_{int(time.time())}{original_ext}"
            output_path = await add_metadata_correct(file_path, meta_path, user_id)
        except Exception as e:
            print(f"Torrent metadata error: {e}")
            output_path = file_path

    thumb_path = None
    user_thumb = await db.get_thumbnail(user_id)
    if user_thumb:
        try:
            thumb_path = f"temp/{user_id}_torrent_thumb_{int(time.time())}.jpg"
            await app.download_media(user_thumb, file_name=thumb_path)
            thumb_path = await process_thumbnail(thumb_path)
        except:
            thumb_path = None

    caption_template = await db.get_caption(user_id)
    if caption_template is None:
        caption = final_filename
    else:
        caption = caption_template \
            .replace("{filename}", os.path.splitext(final_filename)[0]) \
            .replace("{filesize}", humanbytes(file_size)) \
            .replace("{duration}", '00:00:00') \
            .replace("{season}", season) \
            .replace("{episode}", episode) \
            .replace("{quality}", quality)

    dump_enabled = await db.get_dump_enabled(user_id)
    active_dump_channel = await db.get_active_dump_channel(user_id) if dump_enabled else None
    if dump_enabled and active_dump_channel:
        target_chat_id = active_dump_channel
    else:
        target_chat_id = user_id

    if status_msg:
        try:
            await status_msg.edit_text(
                f"📤 **Uploading:** `{final_filename[:60]}`\n"
                f"Size: `{humanbytes(file_size)}`"
            )
        except:
            pass

    upload_start = time.time()
    try:
        sent_msg = None
        if send_as == "document":
            sent_msg = await app.send_document(
                chat_id=target_chat_id,
                document=output_path,
                caption=caption[:1024] if caption else None,
                thumb=thumb_path,
                file_name=final_filename,
                progress=progress_for_pyrogram,
                progress_args=("📤 Uploading...", status_msg, upload_start),
            )
        elif send_as == "video":
            try:
                sent_msg = await app.send_video(
                    chat_id=target_chat_id,
                    video=output_path,
                    caption=caption[:1024] if caption else None,
                    thumb=thumb_path,
                    duration=0,
                    file_name=final_filename,
                    progress=progress_for_pyrogram,
                    progress_args=("📤 Uploading...", status_msg, upload_start),
                )
            except Exception as ve:
                print(f"Video upload failed, fallback to document: {ve}")
                sent_msg = await app.send_document(
                    chat_id=target_chat_id,
                    document=output_path,
                    caption=caption[:1024] if caption else None,
                    thumb=thumb_path,
                    file_name=final_filename,
                )
        elif send_as == "audio":
            sent_msg = await app.send_audio(
                chat_id=target_chat_id,
                audio=output_path,
                caption=caption[:1024] if caption else None,
                thumb=thumb_path,
                duration=0,
                file_name=final_filename,
                progress=progress_for_pyrogram,
                progress_args=("📤 Uploading...", status_msg, upload_start),
            )

        if sent_msg and not (dump_enabled and active_dump_channel):
            dump_channels = await db.get_dump_channels(user_id)
            for channel_id in dump_channels:
                try:
                    await sent_msg.copy(channel_id)
                except BadRequest as be:
                    if "PEER_ID_INVALID" in str(be):
                        await db.remove_dump_channel(user_id, channel_id)
                except Exception as ce:
                    print(f"Failed to copy to dump channel {channel_id}: {ce}")

    finally:
        if output_path != file_path:
            await cleanup_files(output_path)
        if thumb_path:
            await cleanup_files(thumb_path)


async def download_torrent_and_process(user_id: int, source: str, status_msg,
                                        is_torrent_file: bool = False):
    if not LIBTORRENT_AVAILABLE:
        try:
            await status_msg.edit_text(
                "❌ **libtorrent is not installed on this server.**\n\n"
                "Ask the admin to install it:\n"
                "`pip install libtorrent --break-system-packages`"
            )
        except:
            pass
        return

    download_dir = f"downloads/torrent_{user_id}_{int(time.time())}"
    os.makedirs(download_dir, exist_ok=True)
    loop = asyncio.get_event_loop()

    def _create_session_and_handle():
        ses = lt.session()
        ses.listen_on(6881, 6891)
        sp = ses.get_settings()
        sp['active_downloads'] = 3
        sp['active_limit'] = 5
        ses.apply_settings(sp)

        if is_torrent_file:
            info = lt.torrent_info(source)
            handle = ses.add_torrent({'ti': info, 'save_path': download_dir})
        else:
            params = lt.parse_magnet_uri(source)
            params.save_path = download_dir
            handle = ses.add_torrent(params)
        return ses, handle

    try:
        ses, handle = await loop.run_in_executor(None, _create_session_and_handle)
    except Exception as e:
        try:
            await status_msg.edit_text(f"❌ **Failed to add torrent:**\n`{str(e)[:200]}`")
        except:
            pass
        await cleanup_files(download_dir)
        return

    if not is_torrent_file:
        try:
            await status_msg.edit_text(
                "🔍 **Fetching torrent metadata…**\n"
                "_(This may take up to 60 seconds for magnet links)_"
            )
        except:
            pass
        timeout_meta = 120
        start_meta = time.time()
        while True:
            has_meta = await loop.run_in_executor(None, handle.has_metadata)
            if has_meta:
                break
            if time.time() - start_meta > timeout_meta:
                try:
                    await status_msg.edit_text(
                        "❌ **Timeout: Could not fetch torrent metadata.**\n"
                        "Try a different magnet link or check your internet connection."
                    )
                except:
                    pass
                await loop.run_in_executor(None, lambda: ses.remove_torrent(handle))
                await cleanup_files(download_dir)
                return
            await asyncio.sleep(3)

    def _get_torrent_info():
        ti = handle.get_torrent_info()
        fs = ti.files()
        num = fs.num_files()
        result = []
        for i in range(num):
            result.append((i, fs.file_path(i), fs.file_size(i)))
        return ti.name(), ti.total_size(), num, result

    torrent_name, total_size, num_files, file_list = await loop.run_in_executor(
        None, _get_torrent_info
    )

    media_indices = []
    for idx, fpath, fsize in file_list:
        ext = os.path.splitext(fpath)[1].lower()
        if ext in TORRENT_VIDEO_EXTS or ext in TORRENT_AUDIO_EXTS:
            media_indices.append((idx, fpath, fsize))

    if not media_indices:
        try:
            await status_msg.edit_text(
                "❌ **No video or audio files found in this torrent.**\n\n"
                "Supported video: mp4, mkv, avi, mov, wmv, flv, webm, m4v, ts, 3gp, m2ts\n"
                "Supported audio: mp3, flac, aac, wav, ogg, m4a, opus, wma, ac3, dts"
            )
        except:
            pass
        await loop.run_in_executor(None, lambda: ses.remove_torrent(handle))
        await cleanup_files(download_dir)
        return

    def _set_priorities():
        prios = [0] * num_files
        for idx, _, _ in media_indices:
            prios[idx] = 4
        handle.prioritize_files(prios)

    await loop.run_in_executor(None, _set_priorities)

    media_total_size = sum(s for _, _, s in media_indices)
    try:
        await status_msg.edit_text(
            f"📥 **Downloading Torrent**\n\n"
            f"📛 `{torrent_name[:60]}`\n"
            f"🎬 Media files: `{len(media_indices)}`\n"
            f"💾 Total media size: `{humanbytes(media_total_size)}`\n\n"
            f"⏳ Please wait…"
        )
    except:
        pass

    STATE_NAMES = [
        'queued', 'checking', 'downloading metadata',
        'downloading', 'finished', 'seeding',
        'allocating', 'checking fastresume'
    ]
    last_update = 0.0

    while True:
        def _status():
            return handle.status()

        s = await loop.run_in_executor(None, _status)

        if s.state in (
            getattr(lt.torrent_status, 'seeding', 5),
            getattr(lt.torrent_status, 'finished', 4),
        ) or s.progress >= 1.0:
            break

        now = time.time()
        if now - last_update >= 12:
            state_label = STATE_NAMES[s.state] if s.state < len(STATE_NAMES) else 'unknown'
            pct = s.progress * 100
            bar = '█' * int(pct / 5) + '░' * (20 - int(pct / 5))
            try:
                await status_msg.edit_text(
                    f"📥 **Downloading Torrent**\n\n"
                    f"📛 `{torrent_name[:50]}`\n"
                    f"`{bar}` **{pct:.1f}%**\n\n"
                    f"⚡ Speed: `{humanbytes(s.download_rate)}/s`\n"
                    f"📡 Peers: `{s.num_peers}`\n"
                    f"📊 State: `{state_label}`\n"
                    f"💾 Downloaded: `{humanbytes(s.total_done)}` / `{humanbytes(media_total_size)}`"
                )
            except:
                pass
            last_update = now

        await asyncio.sleep(4)

    downloaded_paths = []
    for idx, rel_path, _ in media_indices:
        full_path = os.path.join(download_dir, rel_path)
        if os.path.exists(full_path) and os.path.getsize(full_path) > 0:
            downloaded_paths.append(full_path)

    await loop.run_in_executor(None, lambda: ses.remove_torrent(handle))

    if not downloaded_paths:
        try:
            await status_msg.edit_text(
                "❌ **Download finished but no media files were found on disk.**\n"
                "They may have been filtered or failed to download."
            )
        except:
            pass
        await cleanup_files(download_dir)
        return

    try:
        await status_msg.edit_text(
            f"✅ **Download Complete!**\n\n"
            f"📛 `{torrent_name[:50]}`\n"
            f"🎬 Files ready: `{len(downloaded_paths)}`\n\n"
            f"📤 Starting upload…"
        )
    except:
        pass

    total = len(downloaded_paths)
    for i, fpath in enumerate(downloaded_paths, 1):
        fname = os.path.basename(fpath)
        fsize = os.path.getsize(fpath)
        file_status = None
        try:
            file_status = await app.send_message(
                user_id,
                f"📤 **[{i}/{total}] Uploading:**\n`{fname[:60]}`\nSize: `{humanbytes(fsize)}`"
            )
        except:
            file_status = status_msg

        try:
            await process_torrent_file(fpath, user_id, file_status)
            try:
                await file_status.delete()
            except:
                pass
        except Exception as e:
            try:
                await file_status.edit_text(
                    f"❌ **Upload failed for [{i}/{total}]:**\n"
                    f"`{fname[:50]}`\n"
                    f"Error: `{str(e)[:150]}`"
                )
            except:
                pass

    try:
        await status_msg.edit_text(
            f"🎉 **Torrent processing complete!**\n\n"
            f"📛 `{torrent_name[:50]}`\n"
            f"✅ Files uploaded: `{len(downloaded_paths)}`\n\n"
            f"_All files have been renamed and sent._"
        )
    except:
        try:
            await app.send_message(
                user_id,
                f"🎉 **Torrent complete!** `{torrent_name[:50]}` — "
                f"`{len(downloaded_paths)}` file(s) uploaded."
            )
        except:
            pass

    await cleanup_files(download_dir)
    if is_torrent_file and os.path.exists(source):
        await cleanup_files(source)


# ==================== CORE PROCESSING FUNCTION ====================
async def process_queue_file(message, user_id, task_info):
    format_template = await db.get_format_template(user_id)
    if not format_template:
        try:
            await safe_send_message(
                chat_id=user_id,
                text="❌ Please set a rename format first in private chat!\n"
                     "Use: `/autorename Your Format Here`\n\n"
                     "**Example:** `/autorename {filename} [S{season}E{episode}]`",
            )
        except:
            pass
        return

    if message.document:
        file_id = message.document.file_id
        file_name = message.document.file_name or "file"
        file_size = message.document.file_size
        media_type = "document"
        duration = 0
    elif message.video:
        file_id = message.video.file_id
        file_name = message.video.file_name or "video.mp4"
        file_size = message.video.file_size
        media_type = "video"
        duration = message.video.duration
    elif message.audio:
        file_id = message.audio.file_id
        file_name = message.audio.file_name or "audio.mp3"
        file_size = message.audio.file_size
        media_type = "audio"
        duration = message.audio.duration
    else:
        return

    if file_size and file_size > Config.MAX_FILE_SIZE:
        try:
            await message.reply_text(
                f"❌ **File Too Large**\n\n"
                f"File `{file_name}` is {humanbytes(file_size)} which exceeds "
                f"the maximum limit of {humanbytes(Config.MAX_FILE_SIZE)}."
            )
        except:
            pass
        return

    base_name = os.path.splitext(file_name)[0]
    original_ext = os.path.splitext(file_name)[1] or ('.mp4' if media_type == 'video' else '.mp3')

    season_int, _, episode_int = extract_file_info(file_name)
    season = f"{season_int:02d}" if season_int else 'None'
    episode = f"{episode_int:02d}" if episode_int else 'None'

    quality = "HD"
    try:
        if '4k' in file_name.lower() or '2160p' in file_name.lower():
            quality = "4K"
        elif '2k' in file_name.lower() or '1440p' in file_name.lower():
            quality = "2K"
        elif '1080p' in file_name.lower():
            quality = "1080p"
        elif '720p' in file_name.lower():
            quality = "720p"
        elif '480p' in file_name.lower():
            quality = "480p"
    except:
        pass

    manual_filename = task_info.get('manual_filename')
    encode_mode = task_info.get('encode_mode', False)
    compress_quality = task_info.get('compress_quality', None)

    if compress_quality is None and not encode_mode:
        if manual_filename is None:
            failed_vars = check_extraction_failed(format_template, season_int, episode_int, quality)
        else:
            failed_vars = []

        if failed_vars:
            failed_item = {
                'original_file_name': file_name,
                'file_size': file_size,
                'chat_id': message.chat.id,
                'message_id': message.id,
                'media_type': media_type,
                'duration': duration,
                'original_ext': original_ext,
                'failed_vars': failed_vars,
                'user_id': user_id,
                'task_info': task_info,
            }
            _add_to_failed_queue(user_id, failed_item)
            failed_var_list = ', '.join(failed_vars)
            try:
                await safe_send_message(
                    chat_id=user_id,
                    text=(
                        f"⚠️ **Auto-Rename Failed — Variable Extraction Error**\n\n"
                        f"**File:** `{file_name}`\n"
                        f"**Could not extract:** `{failed_var_list}`\n\n"
                        f"This file has been saved to your **manual rename queue**.\n"
                        f"After all your current files are processed, the bot will ask you "
                        f"to provide the filename manually.\n\n"
                        f"**Failed queue size:** `{len(_get_failed_queue(user_id))}`\n"
                        f"Use /failed_queue to view pending files."
                    )
                )
            except:
                pass
            return

    dump_enabled = await db.get_dump_enabled(user_id)
    active_dump_channel = await db.get_active_dump_channel(user_id) if dump_enabled else None
    if dump_enabled and active_dump_channel:
        target_chat_id = active_dump_channel
    else:
        target_chat_id = message.chat.id

    media_pref = await db.get_media_preference(user_id)
    if media_pref == "video":
        display_ext = original_ext
        send_as = "video"
    elif media_pref == "audio":
        display_ext = original_ext if media_type == "audio" else ".mp3"
        send_as = "audio"
    else:
        display_ext = original_ext
        send_as = "document"

    # ======================================================================
    # COMPRESS MODE
    # ======================================================================
    if compress_quality is not None:
        try:
            status_msg = await message.reply_text(
                f"🗜️ **Compress Mode Active**\n"
                f"**File:** `{file_name}`\n"
                f"⏬ Downloading before compression…"
            )
        except:
            status_msg = None

        encoded_ext = _pick_encode_ext(original_ext)
        download_path = f"downloads/{user_id}_{int(time.time())}{original_ext}"
        file_path = None
        encoded_paths_to_cleanup = []
        try:
            start_time = time.time()
            try:
                file_path = await message.download(
                    file_name=download_path,
                    progress=progress_for_pyrogram,
                    progress_args=("📥 Downloading...", status_msg if status_msg else message, start_time)
                )
            except TypeError:
                file_path = await message.download(file_name=download_path)

            if not file_path or not os.path.exists(file_path):
                if status_msg:
                    try:
                        await status_msg.edit_text("❌ Download failed!")
                    except:
                        pass
                return

            thumb_path = None
            user_thumb = await db.get_thumbnail(user_id)
            if user_thumb:
                try:
                    thumb_path = f"temp/{user_id}_thumb.jpg"
                    await app.download_media(user_thumb, file_name=thumb_path)
                    thumb_path = await process_thumbnail(thumb_path)
                except:
                    thumb_path = None
            if not thumb_path and media_type == "video" and message.video and message.video.thumbs:
                try:
                    thumb = message.video.thumbs[0]
                    thumb_path = f"temp/{user_id}_video_thumb.jpg"
                    await app.download_media(thumb.file_id, file_name=thumb_path)
                    thumb_path = await process_thumbnail(thumb_path)
                except:
                    thumb_path = None

            if compress_quality == 'all':
                qualities_to_encode = ENCODE_QUALITIES
            elif compress_quality == '480p':
                qualities_to_encode = [(480, '480p')]
            elif compress_quality == '720p':
                qualities_to_encode = [(720, '720p')]
            elif compress_quality == '1080p':
                qualities_to_encode = [(1080, '1080p')]
            else:
                qualities_to_encode = []

            for height, quality_label_str in qualities_to_encode:
                encoded_path = f"temp/{user_id}_encoded_{height}p_{int(time.time())}{encoded_ext}"
                encoded_paths_to_cleanup.append(encoded_path)

                if status_msg:
                    try:
                        await status_msg.edit_text(
                            f"🗜️ **Compressing to {quality_label_str}** (preserving audio & subtitles)\n"
                            f"File: `{file_name}`\n"
                            f"⚙️ Processing {quality_label_str}…"
                        )
                    except:
                        pass

                success = await encode_video(file_path, encoded_path, height, status_msg, quality_label_str)
                if not success:
                    try:
                        await app.send_message(
                            user_id,
                            f"❌ Compression to **{quality_label_str}** failed for `{file_name}`. Skipping."
                        )
                    except:
                        pass
                    await cleanup_files(encoded_path)
                    if encoded_path in encoded_paths_to_cleanup:
                        encoded_paths_to_cleanup.remove(encoded_path)
                    continue

                if manual_filename is not None:
                    new_filename = manual_filename
                else:
                    new_filename = format_template
                    enc_size = os.path.getsize(encoded_path)
                    replacements = {
                        '{filename}': base_name,
                        '{season}': season,
                        '{episode}': episode,
                        '{quality}': quality_label_str,
                        '{filesize}': humanbytes(enc_size),
                        '{duration}': str(timedelta(seconds=duration)) if duration else '00:00:00',
                    }
                    for key, value in replacements.items():
                        new_filename = new_filename.replace(key, value)

                new_filename = re.sub(r'[<>:"/\\|?*]', '', new_filename).strip()
                final_filename = new_filename + encoded_ext

                enc_size = os.path.getsize(encoded_path)
                caption_template = await db.get_caption(user_id)
                if caption_template is None:
                    caption = final_filename
                else:
                    caption = caption_template\
                        .replace("{filename}", os.path.splitext(final_filename)[0])\
                        .replace("{filesize}", humanbytes(enc_size))\
                        .replace("{duration}", str(timedelta(seconds=duration)) if duration else '00:00:00')\
                        .replace("{season}", season)\
                        .replace("{episode}", episode)\
                        .replace("{quality}", quality_label_str)

                metadata_enabled = await db.get_metadata(user_id)
                upload_path = encoded_path
                if metadata_enabled:
                    try:
                        meta_path = f"temp/{user_id}_meta_{height}p_{int(time.time())}{encoded_ext}"
                        upload_path = await add_metadata_correct(encoded_path, meta_path, user_id)
                        if upload_path != encoded_path:
                            encoded_paths_to_cleanup.append(upload_path)
                    except Exception as e:
                        print(f"Metadata error for compress {quality_label_str}: {e}")
                        upload_path = encoded_path

                if status_msg:
                    try:
                        await status_msg.edit_text(f"📤 **Uploading {quality_label_str}…**")
                    except:
                        pass

                upload_start = time.time()
                try:
                    await _send_file(
                        target_chat_id=target_chat_id,
                        output_path=upload_path,
                        send_as=send_as,
                        final_filename=final_filename,
                        caption=caption,
                        thumb_path=thumb_path,
                        duration=duration,
                        message=message,
                        status_msg=status_msg,
                        upload_start=upload_start,
                        user_id=user_id,
                        dump_enabled=dump_enabled,
                        active_dump_channel=active_dump_channel,
                    )
                except Exception as upload_error:
                    print(f"Upload error for {quality_label_str}: {upload_error}")
                    try:
                        await app.send_message(
                            user_id,
                            f"❌ Upload failed for **{quality_label_str}**: `{str(upload_error)[:200]}`"
                        )
                    except:
                        pass

            if status_msg:
                try:
                    await status_msg.delete()
                except:
                    pass

            if compress_quality == 'all':
                done_msg = (
                    f"✅ **Compression complete!**\n"
                    f"File `{file_name}` compressed to **480p, 720p, 1080p** and uploaded.\n"
                    f"Container: `{encoded_ext}` | Audio & subtitles preserved."
                )
            else:
                done_msg = (
                    f"✅ **Compression to {compress_quality} complete!**\n"
                    f"File `{file_name}` compressed and uploaded.\n"
                    f"Container: `{encoded_ext}` | Audio & subtitles preserved."
                )
            try:
                await app.send_message(user_id, done_msg)
            except:
                pass

        except asyncio.TimeoutError:
            if status_msg:
                try:
                    await status_msg.edit_text("⏰ **Compression timeout!**")
                except:
                    pass
            raise
        except Exception as e:
            if status_msg:
                try:
                    await status_msg.edit_text(f"❌ **Compression Error:** {str(e)[:200]}")
                except:
                    pass
            raise
        finally:
            paths_to_delete = [download_path]
            paths_to_delete.extend(encoded_paths_to_cleanup)
            if 'thumb_path' in locals() and thumb_path:
                paths_to_delete.append(thumb_path)
            await cleanup_files(*paths_to_delete)

        return

    # ======================================================================
    # ENCODE MODE
    # ======================================================================
    if encode_mode and media_type in ("video", "document"):
        try:
            status_msg = await message.reply_text(
                f"🎬 **Encode Mode Active**\n"
                f"**File:** `{file_name}`\n"
                f"⏬ Downloading before encoding…"
            )
        except:
            status_msg = None

        encoded_ext = _pick_encode_ext(original_ext)
        download_path = f"downloads/{user_id}_{int(time.time())}{original_ext}"
        file_path = None
        encode_paths_to_cleanup = []
        try:
            start_time = time.time()
            try:
                file_path = await message.download(
                    file_name=download_path,
                    progress=progress_for_pyrogram,
                    progress_args=("📥 Downloading...", status_msg if status_msg else message, start_time)
                )
            except TypeError:
                file_path = await message.download(file_name=download_path)

            if not file_path or not os.path.exists(file_path):
                if status_msg:
                    try:
                        await status_msg.edit_text("❌ Download failed!")
                    except:
                        pass
                return

            thumb_path = None
            user_thumb = await db.get_thumbnail(user_id)
            if user_thumb:
                try:
                    thumb_path = f"temp/{user_id}_thumb.jpg"
                    await app.download_media(user_thumb, file_name=thumb_path)
                    thumb_path = await process_thumbnail(thumb_path)
                except:
                    thumb_path = None
            if not thumb_path and media_type == "video" and message.video and message.video.thumbs:
                try:
                    thumb = message.video.thumbs[0]
                    thumb_path = f"temp/{user_id}_video_thumb.jpg"
                    await app.download_media(thumb.file_id, file_name=thumb_path)
                    thumb_path = await process_thumbnail(thumb_path)
                except:
                    thumb_path = None

            for height, quality_label_str in ENCODE_QUALITIES:
                encoded_path = f"temp/{user_id}_encoded_{height}p_{int(time.time())}{encoded_ext}"
                encode_paths_to_cleanup.append(encoded_path)

                if status_msg:
                    try:
                        await status_msg.edit_text(
                            f"🎬 **Encoding {quality_label_str}** (preserving audio & subtitles)\n"
                            f"File: `{file_name}`\n"
                            f"⚙️ Processing {quality_label_str}…"
                        )
                    except:
                        pass

                success = await encode_video(file_path, encoded_path, height, status_msg, quality_label_str)
                if not success:
                    try:
                        await app.send_message(
                            user_id,
                            f"❌ Encoding to **{quality_label_str}** failed for `{file_name}`. Skipping."
                        )
                    except:
                        pass
                    await cleanup_files(encoded_path)
                    if encoded_path in encode_paths_to_cleanup:
                        encode_paths_to_cleanup.remove(encoded_path)
                    continue

                if manual_filename is not None:
                    new_filename = manual_filename
                else:
                    new_filename = format_template
                    enc_size = os.path.getsize(encoded_path)
                    replacements = {
                        '{filename}': base_name,
                        '{season}': season,
                        '{episode}': episode,
                        '{quality}': quality_label_str,
                        '{filesize}': humanbytes(enc_size),
                        '{duration}': str(timedelta(seconds=duration)) if duration else '00:00:00',
                    }
                    for key, value in replacements.items():
                        new_filename = new_filename.replace(key, value)

                new_filename = re.sub(r'[<>:"/\\|?*]', '', new_filename).strip()
                final_filename = new_filename + encoded_ext

                enc_size = os.path.getsize(encoded_path)
                caption_template = await db.get_caption(user_id)
                if caption_template is None:
                    caption = final_filename
                else:
                    caption = caption_template\
                        .replace("{filename}", os.path.splitext(final_filename)[0])\
                        .replace("{filesize}", humanbytes(enc_size))\
                        .replace("{duration}", str(timedelta(seconds=duration)) if duration else '00:00:00')\
                        .replace("{season}", season)\
                        .replace("{episode}", episode)\
                        .replace("{quality}", quality_label_str)

                metadata_enabled = await db.get_metadata(user_id)
                upload_path = encoded_path
                if metadata_enabled:
                    try:
                        meta_path = f"temp/{user_id}_meta_{height}p_{int(time.time())}{encoded_ext}"
                        upload_path = await add_metadata_correct(encoded_path, meta_path, user_id)
                        if upload_path != encoded_path:
                            encode_paths_to_cleanup.append(upload_path)
                    except Exception as e:
                        print(f"Metadata error for encode {quality_label_str}: {e}")
                        upload_path = encoded_path

                if status_msg:
                    try:
                        await status_msg.edit_text(f"📤 **Uploading {quality_label_str}…**")
                    except:
                        pass

                upload_start = time.time()
                try:
                    await _send_file(
                        target_chat_id=target_chat_id,
                        output_path=upload_path,
                        send_as=send_as,
                        final_filename=final_filename,
                        caption=caption,
                        thumb_path=thumb_path,
                        duration=duration,
                        message=message,
                        status_msg=status_msg,
                        upload_start=upload_start,
                        user_id=user_id,
                        dump_enabled=dump_enabled,
                        active_dump_channel=active_dump_channel,
                    )
                except Exception as upload_error:
                    print(f"Upload error for {quality_label_str}: {upload_error}")
                    try:
                        await app.send_message(
                            user_id,
                            f"❌ Upload failed for **{quality_label_str}**: `{str(upload_error)[:200]}`"
                        )
                    except:
                        pass

            if status_msg:
                try:
                    await status_msg.delete()
                except:
                    pass

            try:
                await app.send_message(
                    user_id,
                    f"✅ **Encode complete!**\n"
                    f"File `{file_name}` encoded to **480p, 720p, 1080p** and uploaded.\n"
                    f"Container: `{encoded_ext}` | All audio and subtitle tracks preserved."
                )
            except:
                pass

        except asyncio.TimeoutError:
            if status_msg:
                try:
                    await status_msg.edit_text("⏰ **Encoding timeout!**")
                except:
                    pass
            raise
        except Exception as e:
            if status_msg:
                try:
                    await status_msg.edit_text(f"❌ **Encode Error:** {str(e)[:200]}")
                except:
                    pass
            raise
        finally:
            paths_to_delete = [download_path]
            paths_to_delete.extend(encode_paths_to_cleanup)
            if 'thumb_path' in locals() and thumb_path:
                paths_to_delete.append(thumb_path)
            await cleanup_files(*paths_to_delete)

        return

    # ======================================================================
    # NORMAL PATH
    # ======================================================================
    if manual_filename is not None:
        new_filename = manual_filename
    else:
        new_filename = format_template
        replacements = {
            '{filename}': base_name,
            '{season}': season,
            '{episode}': episode,
            '{quality}': quality,
            '{filesize}': humanbytes(file_size),
            '{duration}': str(timedelta(seconds=duration)) if duration else '00:00:00',
        }
        for key, value in replacements.items():
            new_filename = new_filename.replace(key, value)

    new_filename = re.sub(r'[<>:"/\\|?*]', '', new_filename)
    final_filename = new_filename.strip() + display_ext

    try:
        status_msg = await message.reply_text(
            f"🔄 **Processing Started**\n"
            f"**File:** `{file_name}`\n"
            f"**New Name:** `{final_filename[:50]}`\n"
            f"**Output Type:** `{send_as.upper()}`"
            + (" _(Manual Rename)_" if manual_filename else "")
        )
    except Exception as e:
        print(f"Error sending status message: {e}")
        status_msg = None

    download_path = f"downloads/{user_id}_{int(time.time())}{original_ext}"
    try:
        start_time = time.time()
        if status_msg:
            try:
                await status_msg.edit_text(f"📥 **Downloading...**\n`{file_name}`")
            except:
                pass
        try:
            file_path = await message.download(
                file_name=download_path,
                progress=progress_for_pyrogram,
                progress_args=("📥 Downloading...", status_msg if status_msg else message, start_time)
            )
        except TypeError:
            file_path = await message.download(file_name=download_path)

        if not file_path or not os.path.exists(file_path):
            if status_msg:
                try:
                    await status_msg.edit_text("❌ Download failed!")
                except:
                    pass
            return

        file_size = os.path.getsize(file_path)
        if status_msg:
            try:
                await status_msg.edit_text(f"✅ **Downloaded!**\n\n**Size:** {humanbytes(file_size)}\n\n⚙️ **Processing...**")
            except:
                pass

        output_path = file_path
        metadata_enabled = await db.get_metadata(user_id)
        if metadata_enabled:
            try:
                metadata_path = f"temp/{user_id}_metadata{original_ext}"
                output_path = await add_metadata_correct(file_path, metadata_path, user_id)
                if output_path != file_path:
                    await cleanup_files(file_path)
            except Exception as e:
                print(f"Metadata error: {e}")
                output_path = file_path

        thumb_path = None
        user_thumb = await db.get_thumbnail(user_id)
        if user_thumb:
            try:
                thumb_path = f"temp/{user_id}_thumb.jpg"
                await app.download_media(user_thumb, file_name=thumb_path)
                thumb_path = await process_thumbnail(thumb_path)
            except:
                thumb_path = None
        if not thumb_path and media_type == "video" and message.video and message.video.thumbs:
            try:
                thumb = message.video.thumbs[0]
                thumb_path = f"temp/{user_id}_video_thumb.jpg"
                await app.download_media(thumb.file_id, file_name=thumb_path)
                thumb_path = await process_thumbnail(thumb_path)
            except:
                thumb_path = None

        caption_template = await db.get_caption(user_id)
        if caption_template is None:
            caption = final_filename
        else:
            caption = caption_template.replace("{filename}", os.path.splitext(final_filename)[0])\
                                     .replace("{filesize}", humanbytes(file_size))\
                                     .replace("{duration}", str(timedelta(seconds=duration)) if duration else '00:00:00')\
                                     .replace("{season}", season)\
                                     .replace("{episode}", episode)\
                                     .replace("{quality}", quality)

        if status_msg:
            try:
                await status_msg.edit_text("📤 **Uploading renamed file...**")
            except:
                pass

        upload_start = time.time()
        try:
            await _send_file(
                target_chat_id=target_chat_id,
                output_path=output_path,
                send_as=send_as,
                final_filename=final_filename,
                caption=caption,
                thumb_path=thumb_path,
                duration=duration,
                message=message,
                status_msg=status_msg,
                upload_start=upload_start,
                user_id=user_id,
                dump_enabled=dump_enabled,
                active_dump_channel=active_dump_channel,
            )
            if status_msg:
                try:
                    await status_msg.delete()
                except:
                    pass
        except Exception as upload_error:
            if status_msg:
                try:
                    await status_msg.edit_text(f"❌ **Upload Error:** {str(upload_error)[:200]}")
                except:
                    pass
            raise
    except asyncio.TimeoutError:
        error_text = "⏰ **Processing timeout!**"
        try:
            if status_msg:
                await status_msg.edit_text(error_text)
        except:
            pass
        raise
    except Exception as e:
        error_text = f"❌ **Error:** {str(e)[:200]}"
        try:
            if status_msg:
                await status_msg.edit_text(error_text)
        except:
            pass
        raise
    finally:
        await cleanup_files(
            download_path if 'download_path' in locals() else None,
            output_path if 'output_path' in locals() and output_path != download_path else None,
            thumb_path if 'thumb_path' in locals() else None
        )

# ==================== BOT CLIENT ====================
os.makedirs("downloads", exist_ok=True)
os.makedirs("temp", exist_ok=True)

app = Client(
    "auto_rename_bot",
    api_id=Config.API_ID,
    api_hash=Config.API_HASH,
    bot_token=Config.BOT_TOKEN,
    workers=10,
    sleep_threshold=10,
    no_updates=False,
    in_memory=True
)

# ==================== GROUP FILE HANDLER ====================
@app.on_message(filters.group & (filters.document | filters.video | filters.audio))
async def group_file_handler(client, message):
    if message.from_user.id in add_dump_waiting:
        return
    try:
        if Config.ACTIVE_MODE:
            if len(Config.ALLOWED_GROUPS) > 0 and message.chat.id not in Config.ALLOWED_GROUPS:
                if message.from_user.id in Config.ADMIN:
                    try:
                        await message.reply_text(
                            "❌ This group is not allowed. Use `/add_group {group_id}` to add this group."
                        )
                    except:
                        pass
                else:
                    try:
                        await message.reply_text("❌ This bot is not enabled for this group.")
                    except:
                        pass
                return

        file_size = 0
        if message.document:
            file_size = message.document.file_size or 0
        elif message.video:
            file_size = message.video.file_size or 0
        elif message.audio:
            file_size = message.audio.file_size or 0

        if file_size > Config.MAX_FILE_SIZE:
            try:
                await message.reply_text(
                    f"❌ **File Too Large**\n\n"
                    f"File size ({humanbytes(file_size)}) exceeds the maximum limit of {humanbytes(Config.MAX_FILE_SIZE)}."
                )
            except:
                pass
            return

        user_id = message.from_user.id
        compress_target = compress_sessions.get(user_id, None)
        if compress_target is not None:
            queue_position, task_id, task_item = processing_queue.add_to_queue(
                message, user_id, encode_mode=False, compress_quality=compress_target
            )
        else:
            is_encode = encode_sessions.get(user_id, False)
            queue_position, task_id, task_item = processing_queue.add_to_queue(
                message, user_id, encode_mode=is_encode, compress_quality=None
            )

        if message.document:
            file_name = message.document.file_name or "file"
        elif message.video:
            file_name = message.video.file_name or "video.mp4"
        elif message.audio:
            file_name = message.audio.file_name or "audio.mp3"
        else:
            file_name = "Unknown"

        status_text = f"✅ **File added to queue!**\n\n**File:** `{file_name[:50]}`\n**Queue Position:** `{queue_position}`\n**Queue Size:** `{processing_queue.get_queue_length()}`\n"
        if compress_target == 'all':
            status_text += "🗜️ **Compress mode (480p, 720p, 1080p) is ON**\n"
        elif compress_target == '480p':
            status_text += "🗜️ **Compress mode (480p only) is ON**\n"
        elif compress_target == '720p':
            status_text += "🗜️ **Compress mode (720p only) is ON**\n"
        elif compress_target == '1080p':
            status_text += "🗜️ **Compress mode (1080p only) is ON**\n"
        elif encode_sessions.get(user_id, False):
            status_text += "🎬 **Encode mode (480p,720p,1080p) is ON**\n"
        else:
            status_text += "⚡ **Normal rename mode**\n"
        status_text += "⏳ **Please wait, files are processed one by one...**"

        try:
            await message.reply_text(status_text)
        except Exception as e:
            print(f"Error sending queue message: {e}")

        print(f"Added file to queue. Task ID: {task_id}, Position: {queue_position}, Compress: {compress_target}, Encode: {encode_sessions.get(user_id, False)}")

    except Exception as e:
        print(f"Error in group file handler: {e}")

# ==================== PRIVATE FILE HANDLER ====================
@app.on_message(filters.private & (filters.document | filters.video | filters.audio))
async def private_file_handler(client, message):
    user_id = message.from_user.id

    # ---------- Add dump via forwarded media (FIXED with enum-safe helpers) ----------
    if user_id in add_dump_waiting:
        ch_id, chat_obj = _extract_fwd_channel(message)
        if ch_id is None:
            await message.reply_text(
                "❌ Could not detect the channel from this forward.\n\n"
                "**Try one of these instead:**\n"
                "• Type the channel ID directly (e.g. `-1001234567890`)\n"
                "• Use `/add_dump -1001234567890`\n"
                "• Forward a public channel message (some private channels hide origin)")
            return
        await _do_add_dump_channel(user_id, ch_id, client, message)
        return

    # ---------- Torrent: handle .torrent file uploads ----------
    if torrent_mode_sessions.get(user_id, False):
        is_torrent_doc = False
        torrent_file_path = None

        if message.document:
            doc = message.document
            fname = doc.file_name or ""
            if fname.lower().endswith('.torrent') or doc.mime_type == 'application/x-bittorrent':
                is_torrent_doc = True

        if is_torrent_doc:
            status_msg = await message.reply_text(
                "🌊 **Torrent file detected!**\n\n"
                "⏬ Downloading .torrent file…"
            )
            try:
                torrent_file_path = f"temp/{user_id}_torrent_{int(time.time())}.torrent"
                await message.download(file_name=torrent_file_path)
                if not os.path.exists(torrent_file_path):
                    await status_msg.edit_text("❌ Failed to download .torrent file.")
                    return
                asyncio.create_task(
                    download_torrent_and_process(user_id, torrent_file_path, status_msg, is_torrent_file=True)
                )
            except Exception as e:
                try:
                    await status_msg.edit_text(f"❌ Error: `{str(e)[:200]}`")
                except:
                    pass
            return

    # ---------- Sequence mode ----------
    if user_id in sequence_sessions and sequence_sessions[user_id].get('active'):
        session = sequence_sessions[user_id]
        session['files'].append(message)
        count = len(session['files'])
        try:
            await message.reply_text(f"📥 Saved for sequencing ({count} files so far).")
        except:
            pass
        return

    try:
        await db.add_user(user_id)

        file_size = 0
        if message.document:
            file_size = message.document.file_size or 0
        elif message.video:
            file_size = message.video.file_size or 0
        elif message.audio:
            file_size = message.audio.file_size or 0

        if file_size > Config.MAX_FILE_SIZE:
            try:
                await message.reply_text(
                    f"❌ **File Too Large**\n\n"
                    f"File size ({humanbytes(file_size)}) exceeds the maximum limit of {humanbytes(Config.MAX_FILE_SIZE)}."
                )
            except:
                pass
            return

        compress_target = compress_sessions.get(user_id, None)
        if compress_target is not None:
            queue_position, task_id, task_item = processing_queue.add_to_queue(
                message, user_id, encode_mode=False, compress_quality=compress_target
            )
        else:
            is_encode = encode_sessions.get(user_id, False)
            queue_position, task_id, task_item = processing_queue.add_to_queue(
                message, user_id, encode_mode=is_encode, compress_quality=None
            )

        if message.document:
            file_name = message.document.file_name or "file"
        elif message.video:
            file_name = message.video.file_name or "video.mp4"
        elif message.audio:
            file_name = message.audio.file_name or "audio.mp3"
        else:
            file_name = "Unknown"

        status_text = f"✅ **File added to queue!**\n\n**File:** `{file_name[:50]}`\n**Queue Position:** `{queue_position}`\n**Queue Size:** `{processing_queue.get_queue_length()}`\n"
        if compress_target == 'all':
            status_text += "🗜️ **Compress mode (480p, 720p, 1080p) is ON**\n"
        elif compress_target == '480p':
            status_text += "🗜️ **Compress mode (480p only) is ON**\n"
        elif compress_target == '720p':
            status_text += "🗜️ **Compress mode (720p only) is ON**\n"
        elif compress_target == '1080p':
            status_text += "🗜️ **Compress mode (1080p only) is ON**\n"
        elif encode_sessions.get(user_id, False):
            status_text += "🎬 **Encode mode (480p,720p,1080p) is ON**\n"
        else:
            status_text += "⚡ **Normal rename mode**\n"
        status_text += "⏳ **Please wait, files are processed one by one...**"

        try:
            await message.reply_text(status_text)
        except Exception as e:
            print(f"Error sending queue message: {e}")

        print(f"Added private file to queue. Task ID: {task_id}, Position: {queue_position}, Compress: {compress_target}, Encode: {encode_sessions.get(user_id, False)}")

    except Exception as e:
        print(f"Error in private file handler: {e}")

# ==================== ADD DUMP VIA FORWARDED TEXT (FIXED with enum-safe helpers) ====================
@app.on_message(filters.private & filters.forwarded & ~filters.media)
async def add_dump_forward_text(client, message):
    user_id = message.from_user.id
    if user_id not in add_dump_waiting:
        return
    ch_id, _ = _extract_fwd_channel(message)
    if ch_id is None:
        await message.reply_text(
            "❌ Could not detect a channel from this forward.\n\n"
            "**Try:** type the channel ID directly, e.g. `-1001234567890`")
        return
    await _do_add_dump_channel(user_id, ch_id, client, message)

# ==================== MANUAL RENAME TEXT HANDLER ====================
@app.on_message(filters.private & filters.text & ~filters.command(
    ["start", "help", "autorename", "set_caption", "view_caption", "clear_caption",
     "metadata", "view_metadata", "delete_metadata", "showmetadata",
     "settitle", "setauthor", "setartist", "setaudio", "setsubtitle", "setvideo", "setallmeta",
     "set_thumbnail", "view_thumbnail", "delete_thumbnail", "view_thumb",
     "mediatype", "queue", "queue_stats", "failed_queue", "skip_failed",
     "admin_priority_on", "admin_priority_off", "clear_queue", "clear_queue_user",
     "stats", "add_group", "remove_group", "list_groups",
     "ssequence", "esequence", "sequence_mode",
     "add_dump_channel", "delete_dump_channel", "list_dump_channels",
     "add_dump", "send_dump", "dissable_dump", "view_dump", "delete_dump",
     "stop_renaming", "start_renaming", "cancel",
     "encode_all", "compress", "compress_480p", "compress_720p", "compress_1080p", "compress_off",
     "start_torrent", "stop_torrent"]
))
async def manual_rename_text_handler(client, message):
    user_id = message.from_user.id

    # ── Guard: skip if waiting for dump channel ───────────────────────────
    if user_id in add_dump_waiting:
        # User typed a channel ID directly
        text = message.text.strip()
        try:
            raw_id = int(text)
            channel_id = _normalize_channel_id(raw_id)
            await _do_add_dump_channel(user_id, channel_id, client, message)
        except ValueError:
            await message.reply_text(
                "❌ Please send a valid channel ID (number) or forward a message from the channel.\n"
                "Example: `-1001234567890`")
        return

    text = message.text.strip()

    # ── TORRENT: handle magnet links when torrent mode is ON ──────────────
    if torrent_mode_sessions.get(user_id, False) and text.lower().startswith('magnet:'):
        if not LIBTORRENT_AVAILABLE:
            await message.reply_text(
                "❌ **libtorrent is not installed.**\n\n"
                "Ask the admin to run:\n`pip install libtorrent --break-system-packages`"
            )
            return
        status_msg = await message.reply_text(
            f"🌊 **Magnet link received!**\n\n"
            f"`{text[:80]}…`\n\n"
            f"🔍 Connecting to torrent swarm…"
        )
        asyncio.create_task(
            download_torrent_and_process(user_id, text, status_msg, is_torrent_file=False)
        )
        return

    # ── Original manual rename logic ──────────────────────────────────────
    if user_id not in manual_rename_waiting:
        return
    waiting_info = manual_rename_waiting[user_id]
    if not waiting_info.get('awaiting'):
        return
    new_name = text
    if not new_name:
        await message.reply_text("❌ Please send a valid filename (non-empty text).")
        return
    new_name = re.sub(r'[<>:"/\\|?*]', '', new_name)
    failed_item = waiting_info['failed_item']
    del manual_rename_waiting[user_id]
    failed_list = _get_failed_queue(user_id)
    if failed_item in failed_list:
        failed_list.remove(failed_item)
    chat_id = failed_item['chat_id']
    message_id = failed_item['message_id']
    try:
        original_message = await app.get_messages(chat_id=chat_id, message_ids=message_id)
    except Exception as e:
        await message.reply_text(
            f"❌ **Could not retrieve the original file.**\n"
            f"Error: `{str(e)[:100]}`\n\n"
            f"The file may have been deleted. Skipping to next..."
        )
        await _prompt_next_manual_rename(user_id)
        return
    if not original_message:
        await message.reply_text(
            "❌ **Original file message not found** (may have been deleted).\n"
            "Skipping to next..."
        )
        await _prompt_next_manual_rename(user_id)
        return
    queue_position, task_id, task_item = processing_queue.add_manual_task_to_queue(
        original_message, user_id, new_name
    )
    await message.reply_text(
        f"✅ **File added to rename queue!**\n\n"
        f"**Original File:** `{failed_item['original_file_name']}`\n"
        f"**New Name:** `{new_name}`\n"
        f"**Queue Position:** `{queue_position}`\n\n"
        f"⏳ The file will be processed shortly."
    )
    print(f"Manual rename queued: '{failed_item['original_file_name']}' -> '{new_name}' for user {user_id}")
    remaining = len(_get_failed_queue(user_id))
    if remaining > 0:
        await asyncio.sleep(1)
        await _prompt_next_manual_rename(user_id)
    else:
        await message.reply_text(
            "🎉 **All manual renames done!** No more files pending manual rename."
        )

# ==================== COMMAND HANDLERS ====================
@app.on_message(filters.command("start") & filters.private)
async def start_handler(client, message):
    try:
        user = message.from_user
        await db.add_user(user.id)
        buttons = InlineKeyboardMarkup([
            [InlineKeyboardButton("📚 ʜᴇʟᴘ", callback_data='help'), InlineKeyboardButton("⚙️ ᴍᴇᴛᴀᴅᴀᴛᴀ", callback_data='metadata')],
            [
                InlineKeyboardButton('📢 ᴜᴘᴅᴀᴛᴇs', url='https://t.me/AnimeMultiDub'),
                InlineKeyboardButton('🆘 sᴜᴘᴘᴏʀᴛ', url='https://t.me/AnimeMultiDub')
            ],
            [
                InlineKeyboardButton('📊 Queue Stats', callback_data='queue_status'),
                InlineKeyboardButton('👑 Admin Priority', callback_data='admin_priority')
            ]
        ])
        if Config.START_PIC:
            await message.reply_photo(
                Config.START_PIC,
                caption=Txt.START_TXT.format(user.mention),
                reply_markup=buttons
            )
        else:
            await message.reply_text(
                Txt.START_TXT.format(user.mention),
                reply_markup=buttons
            )
    except Exception as e:
        print(f"Error in start handler: {e}")

@app.on_message(filters.command("help") & filters.private)
async def help_handler(client, message):
    try:
        buttons = InlineKeyboardMarkup([
            [InlineKeyboardButton("🏠 ʜᴏᴍᴇ", callback_data='home')],
            [InlineKeyboardButton("⚙️ ᴍᴇᴛᴀᴅᴀᴛᴀ", callback_data='metadata'), InlineKeyboardButton("📊 Queue", callback_data='queue_status')],
            [InlineKeyboardButton("👑 Admin Priority", callback_data='admin_priority')]
        ])
        await message.reply_text(
            Txt.HELP_TXT,
            reply_markup=buttons,
            disable_web_page_preview=True
        )
    except Exception as e:
        print(f"Error in help handler: {e}")

# ==================== TORRENT COMMANDS ====================
@app.on_message(filters.command("start_torrent") & filters.private)
async def start_torrent_cmd(client, message):
    user_id = message.from_user.id
    await db.add_user(user_id)

    if not LIBTORRENT_AVAILABLE:
        await message.reply_text(
            "❌ **libtorrent is not installed on this server.**\n\n"
            "This feature requires the `libtorrent` Python package.\n"
            "Ask the admin to install it:\n"
            "`pip install libtorrent --break-system-packages`"
        )
        return

    torrent_mode_sessions[user_id] = True
    await message.reply_text(
        "🌊 **Torrent Mode: ON**\n\n"
        "You can now send:\n"
        "• A **magnet link** (paste the magnet URI as a text message)\n"
        "• A **.torrent file** (upload the .torrent file directly)\n\n"
        "**What gets downloaded:**\n"
        "Only **video** and **audio** files from the torrent are downloaded.\n\n"
        "**Supported video:** mp4, mkv, avi, mov, wmv, flv, webm, m4v, ts, 3gp, m2ts\n"
        "**Supported audio:** mp3, flac, aac, wav, ogg, m4a, opus, wma, ac3, dts\n\n"
        "**Rename & send:**\n"
        "Each downloaded file is renamed with your `/autorename` format template "
        "and sent following your dump channel settings.\n\n"
        "Use `/stop_torrent` to exit torrent mode."
    )

@app.on_message(filters.command("stop_torrent") & filters.private)
async def stop_torrent_cmd(client, message):
    user_id = message.from_user.id
    if user_id in torrent_mode_sessions:
        del torrent_mode_sessions[user_id]
    await message.reply_text(
        "🌊 **Torrent Mode: OFF**\n\n"
        "Torrent downloads are now disabled.\n"
        "Use `/start_torrent` to re-enable."
    )

# ==================== ENCODE ALL COMMAND ====================
@app.on_message(filters.command("encode_all") & (filters.private | filters.group))
async def encode_all_handler(client, message):
    try:
        user_id = message.from_user.id
        if compress_sessions.get(user_id, None) is not None:
            compress_sessions[user_id] = None
        current = encode_sessions.get(user_id, False)
        new_state = not current
        encode_sessions[user_id] = new_state

        if new_state:
            await message.reply_text(
                "🎬 **Encode Mode: ON**\n\n"
                "All video files you send will be encoded to:\n"
                "• **480p** — standard definition\n"
                "• **720p** — HD\n"
                "• **1080p** — Full HD\n\n"
                "Output container matches input (MKV→MKV, MP4→MP4, others→MKV).\n"
                "All audio tracks, subtitles and metadata are preserved.\n\n"
                "Use `/encode_all` again to turn encode mode **OFF**.\n"
                "To use compress mode with per‑quality control, try `/compress`."
            )
        else:
            await message.reply_text(
                "🎬 **Encode Mode: OFF**\n\n"
                "Files will now be processed normally (rename only)."
            )
    except Exception as e:
        print(f"Error in encode_all handler: {e}")

# ==================== COMPRESS MODE COMMANDS ====================
@app.on_message(filters.command("compress") & (filters.private | filters.group))
async def compress_handler(client, message):
    user_id = message.from_user.id
    if encode_sessions.get(user_id, False):
        encode_sessions[user_id] = False
    compress_sessions[user_id] = 'all'
    await message.reply_text(
        "🗜️ **Compress Mode: ON (All Resolutions)**\n\n"
        "Your next video files will be compressed to:\n"
        "• **480p**\n"
        "• **720p**\n"
        "• **1080p**\n\n"
        "Each compressed version will be renamed automatically with `{quality}` set to the actual resolution.\n"
        "Output container matches input (MKV→MKV, MP4→MP4, others→MKV).\n"
        "All audio and subtitle tracks are preserved.\n\n"
        "Use `/compress_480p`, `/compress_720p`, or `/compress_1080p` to compress only one quality.\n"
        "Use `/compress_off` to exit compress mode."
    )

@app.on_message(filters.command("compress_480p") & (filters.private | filters.group))
async def compress_480p_handler(client, message):
    user_id = message.from_user.id
    if encode_sessions.get(user_id, False):
        encode_sessions[user_id] = False
    compress_sessions[user_id] = '480p'
    await message.reply_text(
        "🗜️ **Compress Mode: 480p Only**\n\n"
        "Your next video files will be compressed to **480p** only.\n"
        "The `{quality}` variable will be replaced with `480p`.\n"
        "Use `/compress_off` to exit compress mode."
    )

@app.on_message(filters.command("compress_720p") & (filters.private | filters.group))
async def compress_720p_handler(client, message):
    user_id = message.from_user.id
    if encode_sessions.get(user_id, False):
        encode_sessions[user_id] = False
    compress_sessions[user_id] = '720p'
    await message.reply_text(
        "🗜️ **Compress Mode: 720p Only**\n\n"
        "Your next video files will be compressed to **720p** only.\n"
        "The `{quality}` variable will be replaced with `720p`.\n"
        "Use `/compress_off` to exit compress mode."
    )

@app.on_message(filters.command("compress_1080p") & (filters.private | filters.group))
async def compress_1080p_handler(client, message):
    user_id = message.from_user.id
    if encode_sessions.get(user_id, False):
        encode_sessions[user_id] = False
    compress_sessions[user_id] = '1080p'
    await message.reply_text(
        "🗜️ **Compress Mode: 1080p Only**\n\n"
        "Your next video files will be compressed to **1080p** only.\n"
        "The `{quality}` variable will be replaced with `1080p`.\n"
        "Use `/compress_off` to exit compress mode."
    )

@app.on_message(filters.command("compress_off") & (filters.private | filters.group))
async def compress_off_handler(client, message):
    user_id = message.from_user.id
    if user_id in compress_sessions:
        del compress_sessions[user_id]
    await message.reply_text(
        "🗜️ **Compress Mode: OFF**\n\n"
        "Files will now be processed normally (rename only)."
    )

# ==================== AUTORENAME ====================
@app.on_message(filters.command("autorename") & filters.private)
async def autorename_handler(client, message):
    try:
        user_id = message.from_user.id
        await db.add_user(user_id)
        if len(message.command) < 2:
            await message.reply_text(
                "**Please provide a rename format!**\n\n"
                "**Example:** `/autorename {filename} [S{season}E{episode}] - {quality}`\n\n"
                "**Available variables:**\n"
                "- `{filename}`: Original filename\n"
                "- `{season}`: Season number\n"
                "- `{episode}`: Episode number\n"
                "- `{quality}`: Video quality (auto-set in compress/encode mode)\n"
                "- `{filesize}`: File size\n"
                "- `{duration}`: Duration (for videos)\n\n"
                "**Note:** This setting is saved per user."
            )
            return
        format_template = message.text.split(" ", 1)[1]
        await db.set_format_template(user_id, format_template)
        await message.reply_text(
            f"**✅ Rename format set successfully!**\n\n"
            f"**Your format:** `{format_template}`\n\n"
            "Now send me any file in an allowed group or private chat to rename it automatically."
        )
    except Exception as e:
        print(f"Error in autorename handler: {e}")

@app.on_message(filters.command("set_caption") & filters.private)
async def set_caption_handler(client, message):
    try:
        user_id = message.from_user.id
        await db.add_user(user_id)
        if len(message.command) < 2:
            await message.reply_text(
                "**Please provide a caption format!**\n\n"
                "**Example:** `/set_caption {filename} | {filesize}`\n\n"
                "**Available variables:**\n"
                "- `{filename}`: Original filename\n"
                "- `{filesize}`: File size\n"
                "- `{duration}`: Duration (for videos)\n\n"
                "**Note:** Leave empty to remove caption."
            )
            return
        caption = message.text.split(" ", 1)[1]
        await db.set_caption(user_id, caption)
        await message.reply_text(f"**✅ Caption format set successfully!**\n\n**Your caption:** `{caption}`")
    except Exception as e:
        print(f"Error in set_caption handler: {e}")

@app.on_message(filters.command("view_caption") & filters.private)
async def view_caption_handler(client, message):
    try:
        user_id = message.from_user.id
        caption = await db.get_caption(user_id)
        if caption:
            await message.reply_text(
                f"**📝 Your Current Caption Format:**\n\n"
                f"`{caption}`\n\n"
                "**Variables Available:**\n"
                "- `{filename}`: Original filename\n"
                "- `{filesize}`: File size\n"
                "- `{duration}`: Duration (for videos)"
            )
        else:
            await message.reply_text(
                "**❌ No caption format set!**\n\n"
                "Use `/set_caption [format]` to set a caption format."
            )
    except Exception as e:
        print(f"Error in view_caption handler: {e}")

@app.on_message(filters.command("clear_caption") & filters.private)
async def clear_caption_handler(client, message):
    try:
        user_id = message.from_user.id
        await db.add_user(user_id)
        await db.set_caption(user_id, None)
        await message.reply_text(
            "✅ **Caption reset to default!**\n\n"
            "From now on, the caption will be the **full renamed file name with its original extension**.\n"
            "Example: `My Video [S01E02] - 1080p.mkv`\n\n"
            "To set a custom caption, use `/set_caption`."
        )
    except Exception as e:
        print(f"Error in clear_caption handler: {e}")

@app.on_message(filters.command("metadata") & filters.private)
async def metadata_interface_handler(client, message):
    try:
        user_id = message.from_user.id
        await db.add_user(user_id)
        metadata_enabled = await db.get_metadata(user_id)
        status = "✅ **ENABLED**" if metadata_enabled else "❌ **DISABLED**"
        buttons = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔧 View Metadata", callback_data='view_metadata')],
            [InlineKeyboardButton(f"{'❌ Disable' if metadata_enabled else '✅ Enable'} Metadata",
                                  callback_data='toggle_metadata')],
            [InlineKeyboardButton("🏠 ʜᴏᴍᴇ", callback_data='home')]
        ])
        await message.reply_text(
            f"**⚙️ Metadata Settings**\n\n"
            f"**Current Status:** {status}\n\n"
            f"Metadata adds title, author, artist, and other info to your files.\n"
            f"How to set metadata: use /settitle /setauthor /setartist /setaudio /setsubtitle /setvideo /setallmeta\n"
            f"Example: `/setaudio @AnimeMultiDub`",
            reply_markup=buttons
        )
    except Exception as e:
        print(f"Error in metadata interface handler: {e}")

@app.on_message(filters.command("view_metadata") & filters.private)
async def view_metadata_handler(client, message):
    try:
        user_id = message.from_user.id
        await db.add_user(user_id)
        title = await db.get_title(user_id)
        author = await db.get_author(user_id)
        artist = await db.get_artist(user_id)
        audio = await db.get_audio(user_id)
        subtitle = await db.get_subtitle(user_id)
        video = await db.get_video(user_id)
        metadata_enabled = await db.get_metadata(user_id)
        status = "✅ **ENABLED**" if metadata_enabled else "❌ **DISABLED**"
        await message.reply_text(
            f"**📊 Your Metadata Settings**\n\n"
            f"**Metadata Status:** {status}\n\n"
            f"**Title:** `{title}`\n"
            f"**Author:** `{author}`\n"
            f"**Artist:** `{artist}`\n"
            f"**Audio:** `{audio}`\n"
            f"**Subtitle:** `{subtitle}`\n"
            f"**Video:** `{video}`\n\n"
            f"**Commands to change:**\n"
            f"- `/settitle [text]`\n"
            f"- `/setauthor [text]`\n"
            f"- `/setartist [text]`\n"
            f"- `/setaudio [text]`\n"
            f"- `/setsubtitle [text]`\n"
            f"- `/setvideo [text]`\n"
            f"- `/setallmeta [text]` (sets all at once)\n"
            f"- `/metadata` to open settings interface"
        )
    except Exception as e:
        print(f"Error in view_metadata handler: {e}")

@app.on_message(filters.command("delete_metadata") & filters.private)
async def delete_metadata_handler(client, message):
    try:
        user_id = message.from_user.id
        await db.set_title(user_id, "Encoded by @AnimeMultiDub")
        await db.set_author(user_id, "@AnimeMultiDub")
        await db.set_artist(user_id, "@AnimeMultiDub")
        await db.set_audio(user_id, "By @AnimeMultiDub")
        await db.set_subtitle(user_id, "By @AnimeMultiDub")
        await db.set_video(user_id, "Encoded By @AnimeMultiDub")
        await message.reply_text(
            "**✅ Metadata reset to default values!**\n\n"
            "All metadata fields have been reset to default values."
        )
    except Exception as e:
        print(f"Error in delete_metadata handler: {e}")

@app.on_message(filters.command("showmetadata") & filters.private)
async def showmetadata_handler(client, message):
    await view_metadata_handler(client, message)

@app.on_message(filters.command("settitle") & filters.private)
async def settitle_handler(client, message):
    try:
        user_id = message.from_user.id
        await db.add_user(user_id)
        if len(message.command) < 2:
            await message.reply_text("**Please provide a title!**\n\nExample: `/settitle My Custom Title`")
            return
        title = message.text.split(" ", 1)[1]
        await db.set_title(user_id, title)
        await message.reply_text(f"**✅ Title set to:** `{title}`")
    except Exception as e:
        print(f"Error in settitle handler: {e}")

@app.on_message(filters.command("setauthor") & filters.private)
async def setauthor_handler(client, message):
    try:
        user_id = message.from_user.id
        await db.add_user(user_id)
        if len(message.command) < 2:
            await message.reply_text("**Please provide an author!**\n\nExample: `/setauthor Author Name`")
            return
        author = message.text.split(" ", 1)[1]
        await db.set_author(user_id, author)
        await message.reply_text(f"**✅ Author set to:** `{author}`")
    except Exception as e:
        print(f"Error in setauthor handler: {e}")

@app.on_message(filters.command("setartist") & filters.private)
async def setartist_handler(client, message):
    try:
        user_id = message.from_user.id
        await db.add_user(user_id)
        if len(message.command) < 2:
            await message.reply_text("**Please provide an artist!**\n\nExample: `/setartist Artist Name`")
            return
        artist = message.text.split(" ", 1)[1]
        await db.set_artist(user_id, artist)
        await message.reply_text(f"**✅ Artist set to:** `{artist}`")
    except Exception as e:
        print(f"Error in setartist handler: {e}")

@app.on_message(filters.command("setaudio") & filters.private)
async def setaudio_handler(client, message):
    try:
        user_id = message.from_user.id
        await db.add_user(user_id)
        if len(message.command) < 2:
            await message.reply_text("**Please provide audio metadata!**\n\nExample: `/setaudio Audio Metadata`")
            return
        audio = message.text.split(" ", 1)[1]
        await db.set_audio(user_id, audio)
        await message.reply_text(f"**✅ Audio metadata set to:** `{audio}`")
    except Exception as e:
        print(f"Error in setaudio handler: {e}")

@app.on_message(filters.command("setsubtitle") & filters.private)
async def setsubtitle_handler(client, message):
    try:
        user_id = message.from_user.id
        await db.add_user(user_id)
        if len(message.command) < 2:
            await message.reply_text("**Please provide subtitle metadata!**\n\nExample: `/setsubtitle Subtitle Metadata`")
            return
        subtitle = message.text.split(" ", 1)[1]
        await db.set_subtitle(user_id, subtitle)
        await message.reply_text(f"**✅ Subtitle metadata set to:** `{subtitle}`")
    except Exception as e:
        print(f"Error in setsubtitle handler: {e}")

@app.on_message(filters.command("setvideo") & filters.private)
async def setvideo_handler(client, message):
    try:
        user_id = message.from_user.id
        await db.add_user(user_id)
        if len(message.command) < 2:
            await message.reply_text("**Please provide video metadata!**\n\nExample: `/setvideo Video Metadata`")
            return
        video = message.text.split(" ", 1)[1]
        await db.set_video(user_id, video)
        await message.reply_text(f"**✅ Video metadata set to:** `{video}`")
    except Exception as e:
        print(f"Error in setvideo handler: {e}")

@app.on_message(filters.command("setallmeta") & filters.private)
async def setallmeta_handler(client, message):
    try:
        user_id = message.from_user.id
        await db.add_user(user_id)
        if len(message.command) < 2:
            await message.reply_text(
                "**Please provide a value for all metadata fields!**\n\n"
                "**Usage:** `/setallmeta <text>`\n\n"
                "**Example:** `/setallmeta @AnimeMultiDub`\n\n"
                "This will set **title, author, artist, audio, subtitle, and video** to the same text.\n"
                "You can still change individual fields with their respective commands."
            )
            return
        meta_value = message.text.split(" ", 1)[1]
        await db.set_title(user_id, meta_value)
        await db.set_author(user_id, meta_value)
        await db.set_artist(user_id, meta_value)
        await db.set_audio(user_id, meta_value)
        await db.set_subtitle(user_id, meta_value)
        await db.set_video(user_id, meta_value)
        await message.reply_text(
            f"**✅ All metadata fields set to:** `{meta_value}`\n\n"
            f"**Updated fields:** Title, Author, Artist, Audio, Subtitle, Video\n\n"
            f"Use `/showmetadata` to view all settings."
        )
    except Exception as e:
        print(f"Error in setallmeta handler: {e}")

@app.on_message(filters.command("set_thumbnail") & filters.private)
async def set_thumbnail_handler(client, message):
    try:
        user_id = message.from_user.id
        await db.add_user(user_id)
        if message.reply_to_message and message.reply_to_message.photo:
            photo = message.reply_to_message.photo
            file_id = photo.file_id
            await db.set_thumbnail(user_id, file_id)
            await message.reply_text(
                "**✅ Thumbnail set successfully!**\n\n"
                "This thumbnail will be used for your uploaded files.\n"
                "Use `/view_thumbnail` to see it or `/delete_thumbnail` to remove it."
            )
        else:
            await message.reply_text(
                "**Please reply to a photo to set it as thumbnail!**\n\n"
                "**Usage:**\n"
                "1. Send a photo\n"
                "2. Reply to it with `/set_thumbnail`"
            )
    except Exception as e:
        print(f"Error in set_thumbnail handler: {e}")

@app.on_message(filters.command("view_thumbnail") & filters.private)
async def view_thumbnail_handler(client, message):
    try:
        user_id = message.from_user.id
        await db.add_user(user_id)
        thumbnail = await db.get_thumbnail(user_id)
        if thumbnail:
            await message.reply_photo(
                thumbnail,
                caption="**📸 Your Current Thumbnail**\n\n"
                        "Use `/delete_thumbnail` to remove this thumbnail."
            )
        else:
            await message.reply_text(
                "**📸 No thumbnail set!**\n\n"
                "Use `/set_thumbnail` to set a thumbnail from a photo.\n"
                "Reply to any photo with `/set_thumbnail` to set it as your thumbnail."
            )
    except Exception as e:
        print(f"Error in view_thumbnail handler: {e}")

@app.on_message(filters.command("delete_thumbnail") & filters.private)
async def delete_thumbnail_handler(client, message):
    try:
        user_id = message.from_user.id
        await db.set_thumbnail(user_id, None)
        await message.reply_text(
            "**✅ Thumbnail deleted successfully!**\n\n"
            "Your files will now use default thumbnails.\n"
            "Use `/set_thumbnail` to set a new thumbnail."
        )
    except Exception as e:
        print(f"Error in delete_thumbnail handler: {e}")

@app.on_message(filters.command("view_thumb") & filters.private)
async def view_thumb_handler(client, message):
    await view_thumbnail_handler(client, message)

# ==================== FAILED QUEUE COMMANDS ====================
@app.on_message(filters.command("failed_queue") & filters.private)
async def failed_queue_handler(client, message):
    user_id = message.from_user.id
    failed = _get_failed_queue(user_id)
    if not failed:
        await message.reply_text(
            "✅ **No files pending manual rename!**\n\n"
            "All your files have been processed successfully."
        )
        return
    text = f"📋 **Files Pending Manual Rename: {len(failed)}**\n\n"
    for i, item in enumerate(failed, 1):
        fname = item.get('original_file_name', 'Unknown')
        fsize = humanbytes(item.get('file_size', 0))
        failed_vars = ', '.join(item.get('failed_vars', []))
        text += f"**{i}.** `{fname[:50]}`\n"
        text += f"   Size: `{fsize}` | Failed: `{failed_vars}`\n\n"
    is_waiting = user_id in manual_rename_waiting
    if is_waiting:
        text += "\n⏳ _Bot is currently waiting for your filename input._"
    elif not _has_pending_queue_tasks(user_id):
        text += "\n💡 _Use /skip_failed to skip the current file or wait for the bot to prompt you._"
        await _prompt_next_manual_rename(user_id)
    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("⏭️ Skip Current", callback_data=f"skip_manual_{user_id}")],
        [InlineKeyboardButton("❌ Clear All Failed", callback_data=f"cancel_manual_{user_id}")]
    ])
    await message.reply_text(text, reply_markup=buttons)

@app.on_message(filters.command("skip_failed") & filters.private)
async def skip_failed_handler(client, message):
    user_id = message.from_user.id
    if user_id not in manual_rename_waiting:
        failed = _get_failed_queue(user_id)
        if failed:
            await message.reply_text(
                f"ℹ️ You have {len(failed)} file(s) in your failed queue, "
                "but the bot is not currently prompting you.\n"
                "Use /failed_queue to trigger the prompt."
            )
        else:
            await message.reply_text("✅ No files pending manual rename.")
        return
    waiting_info = manual_rename_waiting[user_id]
    failed_item = waiting_info['failed_item']
    del manual_rename_waiting[user_id]
    failed_list = _get_failed_queue(user_id)
    if failed_item in failed_list:
        failed_list.remove(failed_item)
    original_name = failed_item.get('original_file_name', 'Unknown')
    remaining = len(_get_failed_queue(user_id))
    await message.reply_text(
        f"⏭️ **Skipped:** `{original_name}`\n\n"
        f"**Remaining in failed queue:** `{remaining}`"
    )
    if remaining > 0:
        await asyncio.sleep(0.5)
        await _prompt_next_manual_rename(user_id)
    else:
        await message.reply_text("✅ **Failed queue is now empty!**")

# ======================= DUMP CHANNEL COMMANDS =======================
@app.on_message(filters.command("add_dump") & filters.private)
async def add_dump_cmd(client, message):
    user_id = message.from_user.id
    # Support direct channel ID as argument: /add_dump -1001234567890
    if len(message.command) > 1:
        try:
            raw_id = int(message.command[1])
            channel_id = _normalize_channel_id(raw_id)
            await _do_add_dump_channel(user_id, channel_id, client, message)
            return
        except ValueError:
            await message.reply_text("❌ Invalid channel ID. Use a number, e.g. `-1001234567890`")
            return
    add_dump_waiting[user_id] = True
    await message.reply_text(
        "📤 **Add Dump Channel**\n\n"
        "**Option 1:** Forward any message from the channel\n"
        "**Option 2:** Type the channel ID directly (e.g. `-1001234567890`)\n\n"
        "Make sure the bot is admin in that channel and has **Post Messages** permission.\n\n"
        "Type /cancel to cancel."
    )

@app.on_message(filters.command("cancel") & filters.private)
async def cancel_add_dump_cmd(client, message):
    user_id = message.from_user.id
    if user_id in add_dump_waiting:
        del add_dump_waiting[user_id]
        await message.reply_text("❌ Dump channel addition cancelled.")
    else:
        await message.reply_text("Nothing to cancel.")

@app.on_message(filters.command("send_dump") & filters.private)
async def send_dump_cmd(client, message):
    user_id = message.from_user.id
    channels = await db.get_dump_channels(user_id)
    if not channels:
        await message.reply_text("You have no dump channels. Use /add_dump to add one.")
        return
    buttons = []
    for raw_id in channels:
        if isinstance(raw_id, dict):
            ch_id = raw_id.get('channel_id') or raw_id.get('id') or raw_id.get('_id')
            try:
                ch_id = int(ch_id)
            except (TypeError, ValueError):
                continue
        else:
            ch_id = raw_id
        try:
            chat = await client.get_chat(ch_id)
            name = chat.title if hasattr(chat, 'title') else str(ch_id)
        except:
            name = str(ch_id)
        buttons.append([InlineKeyboardButton(name, callback_data=f"sd_{abs(ch_id)}")])
    buttons.append([InlineKeyboardButton("❌ Cancel", callback_data="cancel_select_dump")])
    await message.reply_text(
        "📤 **Select the dump channel to send renamed files to:**",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

@app.on_message(filters.command("dissable_dump") & filters.private)
async def disable_dump_cmd(client, message):
    user_id = message.from_user.id
    await db.set_dump_enabled(user_id, False)
    await db.set_active_dump_channel(user_id, None)
    await message.reply_text(
        "✅ Dump mode disabled. Files will be sent to your private chat.\n"
        "_(Also cleared the active dump channel.)_"
    )

@app.on_message(filters.command("view_dump") & filters.private)
async def view_dump_cmd(client, message):
    user_id = message.from_user.id
    enabled = await db.get_dump_enabled(user_id)
    active_ch = await db.get_active_dump_channel(user_id)
    channels = await db.get_dump_channels(user_id)
    text = "🗂 **Dump Channel Settings**\n\n"
    if enabled and active_ch:
        try:
            chat = await client.get_chat(active_ch)
            name = chat.title if hasattr(chat, 'title') else str(active_ch)
        except:
            name = str(active_ch)
        text += f"✅ Dump mode: **ENABLED**\n"
        text += f"📤 Active channel: `{active_ch}` - {name}\n\n"
    else:
        text += f"❌ Dump mode: **DISABLED**\n\n"
    if channels:
        text += "**All dump channels:**\n"
        for ch_id in channels:
            try:
                chat = await client.get_chat(ch_id)
                name = chat.title if hasattr(chat, 'title') else str(ch_id)
            except:
                name = str(ch_id)
            text += f"• `{ch_id}` - {name}\n"
    else:
        text += "No dump channels added.\n"
    text += "\nUse /add_dump to add, /send_dump to enable, /delete_dump to remove."
    await message.reply_text(text)

@app.on_message(filters.command("delete_dump") & filters.private)
async def delete_dump_cmd(client, message):
    user_id = message.from_user.id
    args = message.command
    if len(args) > 1:
        try:
            channel_id = int(args[1])
        except:
            await message.reply_text("Invalid channel ID.")
            return
        current_channels = await db.get_dump_channels(user_id)
        if channel_id not in current_channels:
            await message.reply_text("Channel not in dump list.")
            return
        await db.remove_dump_channel(user_id, channel_id)
        active = await db.get_active_dump_channel(user_id)
        if active == channel_id:
            await db.set_active_dump_channel(user_id, None)
            await db.set_dump_enabled(user_id, False)
            await message.reply_text(f"✅ Dump channel `{channel_id}` removed and dump mode disabled.")
        else:
            await message.reply_text(f"✅ Dump channel `{channel_id}` removed.")
    else:
        channels = await db.get_dump_channels(user_id)
        if not channels:
            await message.reply_text("You have no dump channels.")
            return
        buttons = []
        for ch_id in channels:
            try:
                chat = await client.get_chat(ch_id)
                name = chat.title if hasattr(chat, 'title') else str(ch_id)
            except:
                name = str(ch_id)
            buttons.append([InlineKeyboardButton(f"❌ {name}", callback_data=f"dd_{abs(ch_id)}")])
        buttons.append([InlineKeyboardButton("Cancel", callback_data="cancel_delete_dump")])
        await message.reply_text(
            "Select a dump channel to delete:",
            reply_markup=InlineKeyboardMarkup(buttons)
        )

@app.on_message(filters.command("list_dump_channels") & filters.private)
async def list_dump_channels_cmd(client, message):
    await view_dump_cmd(client, message)

# ==================== STOP/START RENAMING (admin) ====================
@app.on_message(filters.command("stop_renaming") & filters.private)
async def stop_renaming_cmd(client, message):
    if message.from_user.id not in Config.ADMIN:
        return await message.reply_text("❌ Admin only command.")
    global renaming_paused
    renaming_paused = True
    await message.reply_text("⏸️ Renaming process stopped. Use /start_renaming to resume.")

@app.on_message(filters.command("start_renaming") & filters.private)
async def start_renaming_cmd(client, message):
    if message.from_user.id not in Config.ADMIN:
        return await message.reply_text("❌ Admin only command.")
    global renaming_paused
    renaming_paused = False
    await message.reply_text("▶️ Renaming process resumed.")

# ======================= /mediatype with interactive buttons =======================
@app.on_message(filters.command("mediatype") & filters.private)
async def mediatype_handler(client, message):
    try:
        user_id = message.from_user.id
        await db.add_user(user_id)
        if len(message.command) >= 2:
            media_type = message.command[1].lower()
            if media_type not in ["document", "video", "audio"]:
                await message.reply_text(
                    "**Invalid media type!**\n\n"
                    "**Available options:** document, video, audio\n"
                    "**Example:** `/mediatype video`"
                )
                return
            await db.set_media_preference(user_id, media_type)
            await message.reply_text(
                f"**✅ Output media type set to:** `{media_type}`\n\n"
                f"**Video files will keep their original extension.**\n"
                f"To change back, use `/mediatype document`."
            )
            return
        current = await db.get_media_preference(user_id)
        buttons = InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    f"{'✅ ' if current == 'document' else ''}Document",
                    callback_data="set_mediatype_document"
                ),
                InlineKeyboardButton(
                    f"{'✅ ' if current == 'video' else ''}Video",
                    callback_data="set_mediatype_video"
                ),
                InlineKeyboardButton(
                    f"{'✅ ' if current == 'audio' else ''}Audio",
                    callback_data="set_mediatype_audio"
                )
            ],
            [InlineKeyboardButton("🏠 Cancel", callback_data="home")]
        ])
        await message.reply_text(
            f"**🎬 Choose output media type**\n\n"
            f"Currently: `{current}`\n\n"
            "Tap a button to change:",
            reply_markup=buttons
        )
    except Exception as e:
        print(f"Error in mediatype handler: {e}")

@app.on_message(filters.command("queue") & filters.private)
async def queue_handler(client, message):
    try:
        user_id = message.from_user.id
        queue_info = processing_queue.get_queue_info()
        user_tasks = []
        for task in queue_info['waiting_list']:
            if task['user_id'] == user_id:
                user_tasks.append(task)
        if not user_tasks and queue_info['current'] and queue_info['current']['user_id'] != user_id:
            await message.reply_text(
                "**📭 You have no files in the queue!**\n\n"
                "Send any file in an allowed group or private chat to add it to the queue."
            )
            return
        response = "**📊 Your Queue Status**\n\n"
        if queue_info['current'] and queue_info['current']['user_id'] == user_id:
            current = queue_info['current']
            response += f"🔄 **Currently Processing:**\n"
            response += f"• `{current.get('file_name', 'Unknown')[:40]}`\n"
            if 'start_time' in current:
                elapsed = time.time() - current['start_time']
                response += f"• Processing for: `{TimeFormatter(elapsed*1000)}`\n"
            response += "\n"
        if user_tasks:
            response += f"**📋 Waiting in Queue:** `{len(user_tasks)}` files\n\n"
            for i, task in enumerate(user_tasks[:5]):
                wait_time_seconds = task.get('waiting_time', time.time() - task.get('added_time', 0))
                response += f"**#{task['position']}** - `{task['file_name'][:40]}`\n"
                response += f"  ⏱️ Waiting: `{TimeFormatter(wait_time_seconds*1000)}`\n\n"
            if len(user_tasks) > 5:
                response += f"... and {len(user_tasks) - 5} more files\n\n"
        failed = _get_failed_queue(user_id)
        if failed:
            response += f"⚠️ **Failed Queue (manual rename needed):** `{len(failed)}`\n"
            response += f"Use /failed_queue to view them.\n\n"
        compress_target = compress_sessions.get(user_id, None)
        if compress_target == 'all':
            response += f"🗜️ **Compress Mode:** `ALL (480p/720p/1080p)`\n"
        elif compress_target == '480p':
            response += f"🗜️ **Compress Mode:** `480p only`\n"
        elif compress_target == '720p':
            response += f"🗜️ **Compress Mode:** `720p only`\n"
        elif compress_target == '1080p':
            response += f"🗜️ **Compress Mode:** `1080p only`\n"
        else:
            encode_active = encode_sessions.get(user_id, False)
            response += f"🎬 **Encode Mode:** `{'ON' if encode_active else 'OFF'}`\n"
        torrent_active = torrent_mode_sessions.get(user_id, False)
        response += f"🌊 **Torrent Mode:** `{'ON' if torrent_active else 'OFF'}`\n"
        response += f"\n**📈 Queue Statistics:**\n"
        response += f"• Total in queue: `{queue_info['total']}`\n"
        response += f"• Admin waiting: `{queue_info['admin_waiting']}`\n"
        response += f"• Users waiting: `{queue_info['user_waiting']}`\n"
        response += f"• Currently processing: `{'Yes' if queue_info['is_processing'] else 'No'}`\n"
        await message.reply_text(response)
    except Exception as e:
        print(f"Error in queue handler: {e}")

@app.on_message(filters.command("queue_stats") & filters.private)
async def queue_stats_handler(client, message):
    try:
        queue_info = processing_queue.get_queue_info()
        if queue_info['total'] == 0 and not queue_info['is_processing'] and queue_info['paused'] == 0:
            await message.reply_text("📭 **Queue is empty!**\nNo files in processing queue.")
            return
        status_text = "📊 **Queue Statistics**\n\n"
        admin_priority_status = "✅ **ENABLED**" if queue_info['admin_priority'] else "❌ **DISABLED**"
        status_text += f"**Admin Priority:** {admin_priority_status}\n"
        if queue_info['admin_mode']:
            status_text += "**Admin Mode:** 🚨 **ACTIVE**\n\n"
        else:
            status_text += "**Admin Mode:** ✅ **INACTIVE**\n\n"
        if queue_info['is_processing'] and queue_info.get('current'):
            current = queue_info['current']
            priority_text = "🚨 **ADMIN**" if current.get('is_admin') else "👤 **USER**"
            status_text += f"🔄 **Currently Processing ({priority_text}):**\n"
            status_text += f"   • `{current.get('file_name', 'Unknown')[:30]}`\n"
            status_text += f"   • User ID: `{current.get('user_id', 'Unknown')}`\n"
            if 'start_time' in current:
                elapsed = time.time() - current['start_time']
                status_text += f"   • Processing for: `{TimeFormatter(elapsed*1000)}`\n"
            status_text += "\n"
        status_text += f"📋 **Waiting in Queue:** `{queue_info['total']}` files\n"
        status_text += f"   • 👑 Admin: `{queue_info['admin_waiting']}`\n"
        status_text += f"   • 👤 Users: `{queue_info['user_waiting']}`\n"
        if message.from_user.id in queue_info['user_stats']:
            status_text += f"\n**Your Tasks in Queue:** `{queue_info['user_stats'][message.from_user.id]}`\n"
        failed = _get_failed_queue(message.from_user.id)
        if failed:
            status_text += f"\n⚠️ **Your Failed Queue:** `{len(failed)}` (need manual rename)\n"
        status_text += f"\n**Overall Statistics:**\n"
        status_text += f"• ✅ Completed: `{queue_info['completed']}`\n"
        status_text += f"• ❌ Failed: `{queue_info['failed']}`\n"
        status_text += f"• ⏸️ Paused: `{queue_info['paused']}`\n"
        await message.reply_text(status_text)
    except Exception as e:
        print(f"Error in queue_stats handler: {e}")

@app.on_message(filters.command("admin_priority_on") & filters.private)
async def admin_priority_on_handler(client, message):
    try:
        if message.from_user.id not in Config.ADMIN:
            await message.reply_text("❌ **Admin only command!**")
            return
        processing_queue.admin_priority_mode = True
        await message.reply_text(
            "✅ **Admin Priority Mode ENABLED!**\n\n"
            "Admin files will now be processed with highest priority.\n"
            "User files may be paused if admin files are added to queue."
        )
    except Exception as e:
        print(f"Error in admin_priority_on handler: {e}")

@app.on_message(filters.command("admin_priority_off") & filters.private)
async def admin_priority_off_handler(client, message):
    try:
        if message.from_user.id not in Config.ADMIN:
            await message.reply_text("❌ **Admin only command!**")
            return
        processing_queue.admin_priority_mode = False
        await message.reply_text(
            "✅ **Admin Priority Mode DISABLED!**\n\n"
            "All files will now be processed in normal queue order."
        )
    except Exception as e:
        print(f"Error in admin_priority_off handler: {e}")

@app.on_message(filters.command("clear_queue") & filters.private)
async def clear_queue_handler(client, message):
    try:
        if message.from_user.id not in Config.ADMIN:
            await message.reply_text("❌ **Admin only command!**")
            return
        queue_length = processing_queue.get_queue_length()
        processing_queue.clear_queue()
        await message.reply_text(
            f"✅ **Queue cleared successfully!**\n\n"
            f"• Removed `{queue_length}` waiting tasks\n"
            f"• Queue is now empty"
        )
    except Exception as e:
        print(f"Error in clear_queue handler: {e}")

@app.on_message(filters.command("clear_queue_user") & filters.private)
async def clear_queue_user_handler(client, message):
    try:
        user_id = message.from_user.id
        target_id = user_id
        if len(message.command) > 1:
            if user_id not in Config.ADMIN:
                await message.reply_text("❌ Only admins can clear other users' queue.")
                return
            try:
                target_id = int(message.command[1])
            except ValueError:
                await message.reply_text("❌ Invalid user ID.")
                return
        removed_count, has_current = await processing_queue.clear_user_queue(target_id)
        if removed_count == 0 and not has_current:
            await message.reply_text("❌ No pending files in queue for this user.")
        else:
            response = ""
            if removed_count > 0:
                response += f"✅ Cleared `{removed_count}` waiting file(s) from the queue.\n"
            if has_current:
                response += "ℹ️ One file is currently being processed and cannot be stopped."
            await message.reply_text(response)
    except Exception as e:
        print(f"Error in clear_queue_user handler: {e}")

@app.on_message(filters.command("stats") & filters.private)
async def stats_handler(client, message):
    try:
        if message.from_user.id not in Config.ADMIN:
            await message.reply_text("❌ **Admin only command!**")
            return
        uptime_seconds = time.time() - Config.BOT_UPTIME
        uptime_str = str(timedelta(seconds=int(uptime_seconds)))
        total_users = await db.total_users_count()
        queue_info = processing_queue.get_queue_info()
        total_groups = len(Config.ALLOWED_GROUPS)
        total_failed_pending = sum(len(v) for v in failed_rename_queue.values())
        encode_active_users = sum(1 for v in encode_sessions.values() if v)
        compress_active_users = sum(1 for v in compress_sessions.values() if v is not None)
        torrent_active_users = sum(1 for v in torrent_mode_sessions.values() if v)
        stats_text = f"""
📊 **Bot Statistics**

🤖 **Bot Info:**
• Uptime: `{uptime_str}`
• Pyrogram Version: `{__version__}`
• Pyrogram Enums: `{'✅ v2 native' if _PYROGRAM_ENUMS else '⚠️ v1 string fallback'}`
• Total Users: `{total_users}`
• Allowed Groups: `{total_groups}`

🌊 **Torrent:**
• Torrent mode active users: `{torrent_active_users}`
• libtorrent available: `{'✅ Yes' if LIBTORRENT_AVAILABLE else '❌ No'}`

🗜️ **Compress / Encode:**
• Compress mode active: `{compress_active_users}`
• Encode mode active: `{encode_active_users}`

👑 **Admin Priority:**
• Status: `{"✅ ENABLED" if processing_queue.admin_priority_mode else "❌ DISABLED"}`

📋 **Queue Status:**
• Currently Processing: `{"Yes" if queue_info['is_processing'] else "No"}`
• Waiting in Queue: `{queue_info['total']}`
• Admin Waiting: `{queue_info['admin_waiting']}`
• Users Waiting: `{queue_info['user_waiting']}`
• Failed (Manual Rename Pending): `{total_failed_pending}`

📈 **Task History:**
• Completed Tasks: `{queue_info['completed']}`
• Failed Tasks: `{queue_info['failed']}`
• Total Processed: `{queue_info['completed'] + queue_info['failed']}`
"""
        await message.reply_text(stats_text)
    except Exception as e:
        print(f"Error in stats handler: {e}")

@app.on_message(filters.command("add_group") & filters.private)
async def add_group_handler(client, message):
    try:
        if message.from_user.id not in Config.ADMIN:
            await message.reply_text("❌ **Admin only command!**")
            return
        if len(message.command) < 2:
            await message.reply_text(
                "**Please provide a group ID!**\n\n"
                "**Usage:** `/add_group [group_id]`\n\n"
                "**How to get group ID:**\n"
                "1. Add `@MissRose_bot` to your group\n"
                "2. Use `/id` command\n"
                "3. Copy the group ID (negative number)"
            )
            return
        group_id = int(message.command[1])
        if group_id in Config.ALLOWED_GROUPS:
            await message.reply_text(f"❌ Group `{group_id}` is already in the allowed list!")
            return
        await db.add_group(group_id)
        await message.reply_text(
            f"✅ **Group added successfully!**\n\n"
            f"**Group ID:** `{group_id}`\n\n"
            f"Now users can use the bot in this group."
        )
    except ValueError:
        await message.reply_text("❌ **Invalid group ID!** Please provide a valid numeric group ID.")
    except Exception as e:
        print(f"Error in add_group handler: {e}")

@app.on_message(filters.command("remove_group") & filters.private)
async def remove_group_handler(client, message):
    try:
        if message.from_user.id not in Config.ADMIN:
            await message.reply_text("❌ **Admin only command!**")
            return
        if len(message.command) < 2:
            await message.reply_text(
                "**Please provide a group ID!**\n\n"
                "**Usage:** `/remove_group [group_id]`\n\n"
                "**View allowed groups:** `/list_groups`"
            )
            return
        group_id = int(message.command[1])
        if group_id not in Config.ALLOWED_GROUPS:
            await message.reply_text(f"❌ Group `{group_id}` is not in the allowed list!")
            return
        await db.remove_group(group_id)
        await message.reply_text(
            f"✅ **Group removed successfully!**\n\n"
            f"**Group ID:** `{group_id}`\n\n"
            f"Users can no longer use the bot in this group."
        )
    except ValueError:
        await message.reply_text("❌ **Invalid group ID!** Please provide a valid numeric group ID.")
    except Exception as e:
        print(f"Error in remove_group handler: {e}")

@app.on_message(filters.command("list_groups") & filters.private)
async def list_groups_handler(client, message):
    try:
        if message.from_user.id not in Config.ADMIN:
            await message.reply_text("❌ **Admin only command!**")
            return
        groups = await db.get_all_groups()
        if not groups:
            await message.reply_text("📭 **No groups in allowed list!**")
            return
        response = f"📋 **Allowed Groups ({len(groups)})**\n\n"
        for i, group in enumerate(groups, 1):
            group_id = group['_id']
            added_date = group.get('added_date', 'Unknown')
            try:
                chat = await app.get_chat(group_id)
                group_name = chat.title if hasattr(chat, 'title') else f"Group {group_id}"
                response += f"{i}. **{group_name}**\n"
                response += f"   • ID: `{group_id}`\n"
            except:
                response += f"{i}. **Group {group_id}**\n"
            response += f"   • Added: `{added_date[:10]}`\n"
            response += f"   • Remove: `/remove_group {group_id}`\n\n"
        await message.reply_text(response[:4000])
    except Exception as e:
        print(f"Error in list_groups handler: {e}")

# ==================== SEQUENCE COMMANDS (updated with 3 modes) ====================
@app.on_message(filters.command("sequence_mode") & filters.private)
async def sequence_mode_handler(client, message):
    """Set or view the default sequence sort mode."""
    uid = message.from_user.id
    await db.add_user(uid)
    MODES = {
        1: "Season → Quality → Episode",
        2: "Season → Episode → Quality",
        3: "Quality → Season → Episode",
    }
    if len(message.command) == 1:
        current_mode = await db.get_sequence_mode(uid)
        await message.reply_text(
            f"🔄 **Current Sequence Mode:** `{current_mode}` — {MODES[current_mode]}\n\n"
            "**Available modes:**\n"
            "• Mode 1: Season → Quality → Episode\n"
            "• Mode 2: Season → Episode → Quality\n"
            "• Mode 3: Quality → Season → Episode\n\n"
            "Use `/sequence_mode [1|2|3]` to change."
        )
        return
    try:
        mode = int(message.command[1])
    except ValueError:
        await message.reply_text("❌ Use 1, 2, or 3.")
        return
    if mode not in (1, 2, 3):
        await message.reply_text("❌ Use 1, 2, or 3.")
        return
    await db.set_sequence_mode(uid, mode)
    await message.reply_text(f"✅ Sequence mode set to **{mode}** — {MODES[mode]}")

@app.on_message(filters.command("ssequence") & filters.private)
async def ssequence_handler(client, message):
    user_id = message.from_user.id
    if user_id in sequence_sessions and sequence_sessions[user_id].get('active'):
        await message.reply_text("⚠️ You are already in sequence mode. Send files or use /esequence to finish.")
        return
    sequence_sessions[user_id] = {'active': True, 'files': [], 'sorted_files': []}
    await message.reply_text(
        "🔄 **Sequence mode started!**\n\n"
        "Send me all the files you want to sort. They will be saved and **not** processed yet.\n\n"
        "When done, use `/esequence` to choose sort mode and sort them.\n\n"
        "Use `/sequence_mode` to view/set your default sort mode."
    )

@app.on_message(filters.command("esequence") & filters.private)
async def esequence_handler(client, message):
    user_id = message.from_user.id
    if user_id not in sequence_sessions or not sequence_sessions[user_id].get('active'):
        await message.reply_text("❌ You are not in sequence mode. Start with `/ssequence` first.")
        return
    session = sequence_sessions[user_id]
    session['active'] = False
    files = session['files']
    count = len(files)
    if count == 0:
        del sequence_sessions[user_id]
        await message.reply_text("⚠️ No files were saved. Sequence mode cancelled.")
        return
    # Show 3 mode buttons
    btns = InlineKeyboardMarkup([
        [InlineKeyboardButton("1️⃣ Season → Quality → Episode", callback_data=f"sort_seq_1_{user_id}")],
        [InlineKeyboardButton("2️⃣ Season → Episode → Quality", callback_data=f"sort_seq_2_{user_id}")],
        [InlineKeyboardButton("3️⃣ Quality → Season → Episode", callback_data=f"sort_seq_3_{user_id}")],
        [InlineKeyboardButton("❌ Cancel", callback_data="cancel_seq")]
    ])
    await message.reply_text(
        f"📁 **{count} files saved.**\n\n"
        "Choose a **sort mode**:",
        reply_markup=btns
    )

# ==================== CALLBACK QUERY HANDLER ====================
@app.on_callback_query()
async def callback_query_handler(client, callback_query):
    try:
        user_id = callback_query.from_user.id
        data = callback_query.data

        # Manual rename skip/cancel
        if data.startswith("skip_manual_"):
            parts = data.split("_")
            target_uid = int(parts[2])
            if user_id != target_uid:
                await callback_query.answer("This is not for you.", show_alert=True)
                return
            if target_uid not in manual_rename_waiting:
                failed = _get_failed_queue(target_uid)
                if failed:
                    await callback_query.answer("Triggering manual rename prompt...", show_alert=False)
                    await _prompt_next_manual_rename(target_uid)
                else:
                    await callback_query.answer("No files pending manual rename.", show_alert=True)
                return
            waiting_info = manual_rename_waiting[target_uid]
            failed_item = waiting_info['failed_item']
            del manual_rename_waiting[target_uid]
            failed_list = _get_failed_queue(target_uid)
            if failed_item in failed_list:
                failed_list.remove(failed_item)
            original_name = failed_item.get('original_file_name', 'Unknown')
            remaining = len(_get_failed_queue(target_uid))
            try:
                await callback_query.message.edit_text(
                    f"⏭️ **Skipped:** `{original_name}`\n"
                    f"**Remaining:** `{remaining}`"
                )
            except:
                pass
            await callback_query.answer("Skipped!")
            if remaining > 0:
                await asyncio.sleep(0.5)
                await _prompt_next_manual_rename(target_uid)
            else:
                try:
                    await app.send_message(target_uid, "✅ **Failed queue is now empty!**")
                except:
                    pass
        elif data.startswith("cancel_manual_"):
            parts = data.split("_")
            target_uid = int(parts[2])
            if user_id != target_uid:
                await callback_query.answer("This is not for you.", show_alert=True)
                return
            if target_uid in manual_rename_waiting:
                del manual_rename_waiting[target_uid]
            count = len(_get_failed_queue(target_uid))
            if target_uid in failed_rename_queue:
                del failed_rename_queue[target_uid]
            try:
                await callback_query.message.edit_text(
                    f"❌ **Cancelled all {count} manual rename(s).**\n\n"
                    "Files have been removed from the failed queue."
                )
            except:
                pass
            await callback_query.answer("All manual renames cancelled.")

        # ─── Sequence sort (3 modes) ─────────────────────────────────────
        elif data.startswith("sort_seq_"):
            # Expected format: sort_seq_{mode}_{user_id}
            parts = data.split("_")
            if len(parts) != 4:
                await callback_query.answer("Invalid data.")
                return
            mode = int(parts[2])
            session_user_id = int(parts[3])
            if user_id != session_user_id:
                await callback_query.answer("This is not for you.", show_alert=True)
                return
            if session_user_id not in sequence_sessions or not sequence_sessions[session_user_id].get('files'):
                await callback_query.answer("No files found.", show_alert=True)
                return

            files = sequence_sessions[session_user_id]['files']
            sorted_files = sorted(files, key=lambda m: sort_key_for_mode(m, mode))
            sequence_sessions[session_user_id]['sorted_files'] = sorted_files
            sequence_sessions[session_user_id]['mode'] = mode

            try:
                await callback_query.message.edit_text("🔀 **Sorting files... please wait.**")
            except:
                pass

            for msg in sorted_files:
                try:
                    await msg.copy(chat_id=user_id)
                    await asyncio.sleep(0.3)
                except Exception as e:
                    print(f"Failed to forward file during sorting: {e}")

            summary = generate_sort_summary(sorted_files, mode)
            buttons = InlineKeyboardMarkup([
                [InlineKeyboardButton("🚀 Add to Queue (in order)", callback_data=f"enqueue_seq_{session_user_id}")],
                [InlineKeyboardButton("❌ Cancel", callback_data="cancel_seq")]
            ])
            try:
                await client.send_message(
                    chat_id=user_id,
                    text=f"📁 **{len(sorted_files)} files sorted.**\n\n{summary}",
                    reply_markup=buttons,
                    disable_web_page_preview=True
                )
                await callback_query.message.delete()
            except Exception as e:
                print(f"Sort summary send error: {e}")
            await callback_query.answer("Sorted!")

        elif data.startswith("enqueue_seq_"):
            parts = data.split("_")
            if len(parts) < 3:
                return
            session_user_id = int(parts[2])
            if user_id != session_user_id:
                await callback_query.answer("This is not for you.", show_alert=True)
                return
            if session_user_id not in sequence_sessions or 'sorted_files' not in sequence_sessions[session_user_id]:
                await callback_query.answer("No sorted files to enqueue.", show_alert=True)
                return
            sorted_files = sequence_sessions[session_user_id]['sorted_files']
            count = len(sorted_files)
            compress_target = compress_sessions.get(session_user_id, None)
            for msg in sorted_files:
                if compress_target is not None:
                    processing_queue.add_to_queue(msg, session_user_id, encode_mode=False, compress_quality=compress_target)
                else:
                    is_encode = encode_sessions.get(session_user_id, False)
                    processing_queue.add_to_queue(msg, session_user_id, encode_mode=is_encode, compress_quality=None)
            del sequence_sessions[session_user_id]
            await callback_query.message.edit_text(
                f"✅ **{count} files added to the processing queue in sorted order!**\n\n"
                "They will be processed one by one.",
                reply_markup=None
            )
            await callback_query.answer("Added to queue!")
        elif data == "cancel_seq":
            if user_id in sequence_sessions:
                del sequence_sessions[user_id]
            await callback_query.message.edit_text("❌ Sequence session cancelled.")
            await callback_query.answer("Cancelled.")

        # Media type buttons
        elif data.startswith("set_mediatype_"):
            media = data.split("_")[2]
            if media not in ["document", "video", "audio"]:
                await callback_query.answer("Invalid type")
                return
            await db.set_media_preference(user_id, media)
            await callback_query.answer(f"Media type set to {media}", show_alert=True)
            current = await db.get_media_preference(user_id)
            buttons = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(f"{'✅ ' if current == 'document' else ''}Document", callback_data="set_mediatype_document"),
                    InlineKeyboardButton(f"{'✅ ' if current == 'video' else ''}Video", callback_data="set_mediatype_video"),
                    InlineKeyboardButton(f"{'✅ ' if current == 'audio' else ''}Audio", callback_data="set_mediatype_audio")
                ],
                [InlineKeyboardButton("🏠 Cancel", callback_data="home")]
            ])
            await callback_query.message.edit_text(
                f"**🎬 Output media type updated!**\n\nCurrent: `{current}`",
                reply_markup=buttons
            )

        # ---------- DUMP CALLBACKS ----------
        elif data.startswith("sd_"):
            try:
                raw_part = int(data[3:])
                channel_id = _normalize_channel_id(raw_part)
            except (IndexError, ValueError):
                await callback_query.answer("Invalid data.")
                return
            await db.set_active_dump_channel(user_id, channel_id)
            await db.set_dump_enabled(user_id, True)
            await callback_query.answer("Dump channel set and enabled!", show_alert=True)
            try:
                await callback_query.message.edit_text(
                    f"✅ Dump channel selected: `{channel_id}`\n\n"
                    "From now on, renamed files will be sent **only** to this dump channel.\n"
                    "Use /dissable_dump to revert to private chat."
                )
            except:
                pass

        elif data.startswith("dd_"):
            try:
                raw_part = int(data[3:])
                channel_id = _normalize_channel_id(raw_part)
            except (IndexError, ValueError):
                await callback_query.answer("Invalid data.")
                return
            await db.remove_dump_channel(user_id, channel_id)
            active = await db.get_active_dump_channel(user_id)
            if active == channel_id:
                await db.set_active_dump_channel(user_id, None)
                await db.set_dump_enabled(user_id, False)
                await callback_query.answer("Channel deleted. Dump mode disabled.", show_alert=True)
            else:
                await callback_query.answer("Channel deleted.", show_alert=True)
            try:
                await callback_query.message.edit_text("Dump channel deleted successfully.")
            except:
                pass
        elif data == "cancel_select_dump":
            await callback_query.message.edit_text("Selection cancelled.")
            await callback_query.answer()
        elif data.startswith("delete_dump_"):
            channel_id = int(data.split("_")[2])
            await db.remove_dump_channel(user_id, channel_id)
            active = await db.get_active_dump_channel(user_id)
            if active == channel_id:
                await db.set_active_dump_channel(user_id, None)
                await db.set_dump_enabled(user_id, False)
                await callback_query.answer("Channel deleted. Dump mode disabled.", show_alert=True)
            else:
                await callback_query.answer("Channel deleted.", show_alert=True)
            try:
                await callback_query.message.edit_text("Dump channel deleted successfully.")
            except:
                pass
        elif data == "cancel_delete_dump":
            await callback_query.message.edit_text("Deletion cancelled.")
            await callback_query.answer()

        # Default callbacks (home, help, metadata, etc.)
        else:
            if callback_query.data == 'help':
                buttons = InlineKeyboardMarkup([
                    [InlineKeyboardButton("🏠 ʜᴏᴍᴇ", callback_data='home')],
                    [InlineKeyboardButton("⚙️ ᴍᴇᴛᴀᴅᴀᴛᴀ", callback_data='metadata'),
                     InlineKeyboardButton("📊 Queue", callback_data='queue_status')],
                    [InlineKeyboardButton("👑 Admin Priority", callback_data='admin_priority')]
                ])
                try:
                    await callback_query.message.edit_text(
                        Txt.HELP_TXT, reply_markup=buttons, disable_web_page_preview=True
                    )
                except Exception:
                    await callback_query.message.delete()
                    await callback_query.message.reply_text(
                        Txt.HELP_TXT, reply_markup=buttons, disable_web_page_preview=True
                    )
            elif callback_query.data == 'home':
                buttons = InlineKeyboardMarkup([
                    [InlineKeyboardButton("📚 ʜᴇʟᴘ", callback_data='help'),
                     InlineKeyboardButton("⚙️ ᴍᴇᴛᴀᴅᴀᴛᴀ", callback_data='metadata')],
                    [
                        InlineKeyboardButton('📢 ᴜᴘᴅᴀᴛᴇs', url='https://t.me/AnimeMultiDub'),
                        InlineKeyboardButton('🆘 sᴜᴘᴘᴏʀᴛ', url='https://t.me/AnimeMultiDub')
                    ],
                    [
                        InlineKeyboardButton('📊 Queue Stats', callback_data='queue_status'),
                        InlineKeyboardButton('👑 Admin Priority', callback_data='admin_priority')
                    ]
                ])
                try:
                    await callback_query.message.edit_text(
                        Txt.START_TXT.format(callback_query.from_user.mention), reply_markup=buttons
                    )
                except Exception:
                    await callback_query.message.delete()
                    await callback_query.message.reply_text(
                        Txt.START_TXT.format(callback_query.from_user.mention), reply_markup=buttons
                    )
            elif callback_query.data == 'metadata':
                metadata_enabled = await db.get_metadata(user_id)
                status = "✅ **ENABLED**" if metadata_enabled else "❌ **DISABLED**"
                buttons = InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔧 View Metadata", callback_data='view_metadata')],
                    [InlineKeyboardButton(f"{'❌ Disable' if metadata_enabled else '✅ Enable'} Metadata",
                                          callback_data='toggle_metadata')],
                    [InlineKeyboardButton("🏠 ʜᴏᴍᴇ", callback_data='home')]
                ])
                try:
                    await callback_query.message.edit_text(
                        f"**⚙️ Metadata Settings**\n\n**Current Status:** {status}\n\nMetadata adds title, author, artist, and other info to your files.\n"
                        f"How to set metadata : use /settitle /setauthor /setartist /setaudio /setsubtitle /setvideo /setallmeta\n"
                        f"Example: `/setaudio @AnimeMultiDub`",
                        reply_markup=buttons
                    )
                except Exception:
                    await callback_query.message.delete()
                    await callback_query.message.reply_text(
                        f"**⚙️ Metadata Settings**\n\n**Current Status:** {status}\n\nMetadata adds title, author, artist, and other info to your files.\n"
                        f"How to set metadata : use /settitle /setauthor /setartist /setaudio /setsubtitle /setvideo /setallmeta\n"
                        f"Example: `/setaudio @AnimeMultiDub`",
                        reply_markup=buttons
                    )
            elif callback_query.data == 'toggle_metadata':
                current = await db.get_metadata(user_id)
                new_value = not current
                await db.set_metadata(user_id, new_value)
                status = "✅ **ENABLED**" if new_value else "❌ **DISABLED**"
                buttons = InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔧 View Metadata", callback_data='view_metadata')],
                    [InlineKeyboardButton(f"{'❌ Disable' if new_value else '✅ Enable'} Metadata",
                                          callback_data='toggle_metadata')],
                    [InlineKeyboardButton("🏠 ʜᴏᴍᴇ", callback_data='home')]
                ])
                try:
                    await callback_query.message.edit_text(
                        f"**✅ Metadata setting updated!**\n\n**New Status:** {status}",
                        reply_markup=buttons
                    )
                except Exception:
                    await callback_query.message.delete()
                    await callback_query.message.reply_text(
                        f"**✅ Metadata setting updated!**\n\n**New Status:** {status}",
                        reply_markup=buttons
                    )
            elif callback_query.data == 'view_metadata':
                title = await db.get_title(user_id)
                author = await db.get_author(user_id)
                artist = await db.get_artist(user_id)
                audio = await db.get_audio(user_id)
                subtitle = await db.get_subtitle(user_id)
                video = await db.get_video(user_id)
                metadata_enabled = await db.get_metadata(user_id)
                status = "✅ **ENABLED**" if metadata_enabled else "❌ **DISABLED**"
                buttons = InlineKeyboardMarkup([
                    [InlineKeyboardButton("⚙️ Back to Settings", callback_data='metadata')],
                    [InlineKeyboardButton("🏠 ʜᴏᴍᴇ", callback_data='home')]
                ])
                try:
                    await callback_query.message.edit_text(
                        f"**📊 Your Metadata Settings**\n\n**Metadata Status:** {status}\n\n"
                        f"**Title:** `{title}`\n**Author:** `{author}`\n**Artist:** `{artist}`\n"
                        f"**Audio:** `{audio}`\n**Subtitle:** `{subtitle}`\n**Video:** `{video}`",
                        reply_markup=buttons
                    )
                except Exception:
                    await callback_query.message.delete()
                    await callback_query.message.reply_text(
                        f"**📊 Your Metadata Settings**\n\n**Metadata Status:** {status}\n\n"
                        f"**Title:** `{title}`\n**Author:** `{author}`\n**Artist:** `{artist}`\n"
                        f"**Audio:** `{audio}`\n**Subtitle:** `{subtitle}`\n**Video:** `{video}`",
                        reply_markup=buttons
                    )
            elif callback_query.data == 'queue_status':
                await callback_query.answer()
                await queue_stats_handler(client, callback_query.message)
            elif callback_query.data == 'admin_priority':
                if user_id not in Config.ADMIN:
                    await callback_query.answer("❌ Admin only feature!", show_alert=True)
                    return
                status = "✅ **ENABLED**" if processing_queue.admin_priority_mode else "❌ **DISABLED**"
                buttons = InlineKeyboardMarkup([
                    [InlineKeyboardButton(f"{'❌ Disable' if processing_queue.admin_priority_mode else '✅ Enable'} Priority",
                                          callback_data='toggle_admin_priority')],
                    [InlineKeyboardButton("🏠 ʜᴏᴍᴇ", callback_data='home')]
                ])
                try:
                    await callback_query.message.edit_text(
                        f"**👑 Admin Priority Settings**\n\n**Current Status:** {status}",
                        reply_markup=buttons
                    )
                except Exception:
                    await callback_query.message.delete()
                    await callback_query.message.reply_text(
                        f"**👑 Admin Priority Settings**\n\n**Current Status:** {status}",
                        reply_markup=buttons
                    )
            elif callback_query.data == 'toggle_admin_priority':
                if user_id not in Config.ADMIN:
                    await callback_query.answer("❌ Admin only feature!", show_alert=True)
                    return
                processing_queue.admin_priority_mode = not processing_queue.admin_priority_mode
                status = "✅ **ENABLED**" if processing_queue.admin_priority_mode else "❌ **DISABLED**"
                buttons = InlineKeyboardMarkup([
                    [InlineKeyboardButton(f"{'❌ Disable' if processing_queue.admin_priority_mode else '✅ Enable'} Priority",
                                          callback_data='toggle_admin_priority')],
                    [InlineKeyboardButton("🏠 ʜᴏᴍᴇ", callback_data='home')]
                ])
                try:
                    await callback_query.message.edit_text(
                        f"**✅ Admin Priority updated!**\n\n**New Status:** {status}",
                        reply_markup=buttons
                    )
                except Exception:
                    await callback_query.message.delete()
                    await callback_query.message.reply_text(
                        f"**✅ Admin Priority updated!**\n\n**New Status:** {status}",
                        reply_markup=buttons
                    )
            await callback_query.answer()
    except Exception as e:
        print(f"Error in callback handler: {e}")

# ==================== MAIN ====================
async def main():
    await app.start()
    await db.init_db()
    asyncio.create_task(queue_worker())
    me = await app.get_me()
    print(f"✅ Bot started as @{me.username}")
    print(f"✅ Bot ID: {me.id}")
    print(f"✅ Allowed Groups: {len(Config.ALLOWED_GROUPS)} groups")
    print("✅ Bot is ready and commands will work continuously!")
    print("✅ Files can be sent in private chat OR allowed groups.")
    print(f"✅ ACTIVE_MODE = {Config.ACTIVE_MODE}")
    print(f"✅ Pyrogram enums: {'v2 native' if _PYROGRAM_ENUMS else 'v1 string fallback'}")
    print("✅ Dump channel fix active — enum-safe type/status checks, multi-fallback fwd detection!")
    print("✅ Dump: /add_dump (forward OR type ID OR /add_dump -100xxx), /send_dump, /dissable_dump, /view_dump, /delete_dump")
    print("✅ /stop_renaming & /start_renaming (admin) available")
    print("✅ /encode_all — toggle video encoding to 480p/720p/1080p (preserves ALL streams, container-aware)")
    print("✅ /compress, /compress_480p, /compress_720p, /compress_1080p — compress+rename mode")
    print("✅ Container logic: MKV→MKV, MP4→MP4, other→MKV (subtitle-safe)")
    print(f"✅ Torrent mode: /start_torrent, /stop_torrent — libtorrent {'AVAILABLE' if LIBTORRENT_AVAILABLE else 'NOT AVAILABLE'}")
    print("✅ Sequence: /ssequence, /esequence (3 sort modes), /sequence_mode [1|2|3]")
    try:
        await app.send_message(
            Config.LOG_CHANNEL,
            f"🤖 **Bot Started Successfully!**\n\n"
            f"**Name:** {me.first_name}\n"
            f"**Username:** @{me.username}\n"
            f"**ID:** `{me.id}`\n"
            f"**Time:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            f"**Features:** Subtitle/audio/metadata preservation, container-aware encoding, "
            f"dump channel fix (enum-safe), 3-mode sequence sorting, "
            f"torrent download mode ({'✅ libtorrent ready' if LIBTORRENT_AVAILABLE else '❌ libtorrent missing'})."
        )
    except:
        pass
    await idle()
    await app.stop()

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    try:
        result = subprocess.run(['ffmpeg', '-version'], capture_output=True, text=True, check=True)
        print("✅ FFmpeg is installed and working")
    except:
        print("⚠️ WARNING: FFmpeg not found! Metadata and encode features will not work.")
    print("\n" + "="*60)
    print("🚀 Starting Advanced Auto Rename Bot (Merged)...")
    print("="*60)
    print(f"👑 Admins: {Config.ADMIN}")
    print(f"📋 Allowed Groups: {len(Config.ALLOWED_GROUPS)}")
    print(f"👷 Queue System: ACTIVE")
    print(f"📦 Max File Size: {humanbytes(Config.MAX_FILE_SIZE)}")
    print("👑 Admin Priority: DISABLED by default")
    print("🗂 Dump channels: FIXED (enum-safe, forward/type-ID/direct-arg all supported)")
    print("⏸️ Renaming control: /stop_renaming, /start_renaming")
    print("🎬 Encode mode: /encode_all (container-aware, preserves ALL streams)")
    print("🗜️ Compress mode: /compress (all), /compress_480p, /compress_720p, /compress_1080p")
    print("📦 Container: MKV→MKV, MP4→MP4, others→MKV (subtitle-safe)")
    print(f"🌊 Torrent mode: /start_torrent, /stop_torrent ({'libtorrent READY' if LIBTORRENT_AVAILABLE else 'libtorrent NOT INSTALLED'})")
    print("🔄 Sequence: 3 sort modes — /ssequence, /esequence, /sequence_mode [1|2|3]")
    if not LIBTORRENT_AVAILABLE:
        print("   To enable torrent: pip install libtorrent --break-system-packages")
    print("🤖 Bot is running. Press Ctrl+C to stop.")
    print("="*60 + "\n")
    try:
        app.run(main())
    except KeyboardInterrupt:
        print("\n👋 Bot stopped by user")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()