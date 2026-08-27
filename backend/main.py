import base64
import asyncio
import hashlib
import html
import hmac
import json
import os
import re
import secrets
import shutil
import subprocess
import tempfile
import time
import uuid
import unicodedata
from collections import deque
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Literal, Optional

import cloudinary
import cloudinary.uploader
import yt_dlp
from dotenv import load_dotenv
from fastapi import BackgroundTasks, Depends, FastAPI, File, Form, Header, HTTPException, Query, UploadFile, WebSocket, WebSocketDisconnect, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator
from supabase import Client, create_client

load_dotenv()

app = FastAPI(title="LuNu Music API", version="2.0.0")

configured_origins = [
    origin.strip().rstrip('/')
    for origin in os.getenv('CORS_ORIGINS', '').split(',')
    if origin.strip()
]
allowed_origins = list(dict.fromkeys([
    'https://lunu-music.vercel.app',
    'http://localhost:5173',
    'http://localhost:4173',
    *configured_origins,
]))
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=False,
    allow_methods=['GET', 'POST', 'PATCH', 'DELETE', 'OPTIONS'],
    allow_headers=['Authorization', 'Content-Type'],
)

DEFAULT_COVER = '/images/ChoCiu.jpg'
CLOUDINARY_PLAN_LIMIT_BYTES = 100 * 1024 * 1024
CLOUDINARY_SAFE_VIDEO_BYTES = 92 * 1024 * 1024
VIDEO_TRANSCODE_TIMEOUT_SECONDS = int(os.getenv('LUNU_VIDEO_TRANSCODE_TIMEOUT_SECONDS', '900'))
RENDER_MAX_DOWNLOAD_BYTES = int(os.getenv('LUNU_RENDER_MAX_DOWNLOAD_BYTES', str(450 * 1024 * 1024)))
CHAT_ATTACHMENT_MAX_BYTES = int(os.getenv('LUNU_CHAT_ATTACHMENT_MAX_BYTES', str(25 * 1024 * 1024)))
CHAT_ATTACHMENT_MAX_FILENAME = 160
CHAT_IMAGE_MIMES = {'image/jpeg', 'image/png', 'image/webp', 'image/gif'}
CHAT_FILE_MIMES = {'application/pdf', 'text/plain', 'text/csv', 'application/json', 'application/zip', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', 'application/vnd.openxmlformats-officedocument.presentationml.presentation'}
CHAT_EXTENSION_MIMES = {'.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.png': 'image/png', '.webp': 'image/webp', '.gif': 'image/gif', '.pdf': 'application/pdf', '.txt': 'text/plain', '.csv': 'text/csv', '.json': 'application/json', '.zip': 'application/zip', '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', '.pptx': 'application/vnd.openxmlformats-officedocument.presentationml.presentation'}

SUPABASE_URL = os.getenv('SUPABASE_URL', '').strip()
SUPABASE_KEY = os.getenv('SUPABASE_KEY', '').strip()
AUTH_SECRET = os.getenv('LUNU_AUTH_SECRET', '').strip() or 'change-this-secret-in-production'
if AUTH_SECRET == 'change-this-secret-in-production':
    print('⚠️ LUNU_AUTH_SECRET chưa được cấu hình; hãy thay bằng secret dài trên Render.')

supabase: Optional[Client] = None
import_jobs: dict[str, dict] = {}
chat_connections: dict[str, set[WebSocket]] = {}
chat_connection_users: dict[WebSocket, str] = {}
chat_send_windows: dict[str, deque[float]] = {}
CHAT_RATE_LIMIT_COUNT = 30
CHAT_RATE_LIMIT_WINDOW_SECONDS = 60.0

if SUPABASE_URL and SUPABASE_KEY:
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception as error:
        print('⚠️ Lỗi khởi tạo Supabase:', error)
else:
    print('⚠️ Thiếu SUPABASE_URL hoặc SUPABASE_KEY; API database sẽ trả lỗi cấu hình.')

cloudinary_configured = all(os.getenv(key, '').strip() for key in ('CLOUDINARY_CLOUD_NAME', 'CLOUDINARY_API_KEY', 'CLOUDINARY_API_SECRET'))
if cloudinary_configured:
    cloudinary.config(
        cloud_name=os.getenv('CLOUDINARY_CLOUD_NAME'),
        api_key=os.getenv('CLOUDINARY_API_KEY'),
        api_secret=os.getenv('CLOUDINARY_API_SECRET'),
        secure=True,
    )
else:
    print('⚠️ Thiếu Cloudinary credentials; upload sẽ bị từ chối rõ ràng.')


_cleanup_task: Optional[asyncio.Task] = None


async def periodic_cinema_cleanup() -> None:
    await asyncio.sleep(15)
    while True:
        if supabase is not None:
            try:
                result = await asyncio.to_thread(cleanup_expired_cinema_videos, supabase)
                if result['deleted_count'] or result['failed_count']:
                    print(f'🧹 Cinema cleanup: đã xóa {result["deleted_count"]}, lỗi {result["failed_count"]}.')
            except Exception as error:
                print(f'⚠️ Cinema cleanup chưa chạy được: {error}')
            try:
                deleted_chat = await asyncio.to_thread(cleanup_expired_chat_messages, supabase)
                if deleted_chat:
                    print(f'🧹 Chat cleanup: đã xóa {deleted_chat} tin nhắn hết hạn.')
            except Exception as error:
                print(f'⚠️ Chat cleanup chưa chạy được: {error}')
        await asyncio.sleep(15 * 60)


@app.on_event('startup')
async def start_periodic_cleanup() -> None:
    global _cleanup_task
    _cleanup_task = asyncio.create_task(periodic_cinema_cleanup())


@app.on_event('shutdown')
async def stop_periodic_cleanup() -> None:
    global _cleanup_task
    if _cleanup_task:
        _cleanup_task.cancel()
        try:
            await _cleanup_task
        except asyncio.CancelledError:
            pass
        _cleanup_task = None


class MediaTooLargeError(RuntimeError):
    pass


class AddSongRequest(BaseModel):
    video_id: str = Field(min_length=6, max_length=32, pattern=r'^[A-Za-z0-9_-]+$')
    title: str = Field(min_length=1, max_length=240)
    artist: str = Field(min_length=1, max_length=160)
    cover: str = Field(default='', max_length=500)
    lyrics: str = Field(default='', max_length=100000)

    @field_validator('title', 'artist', 'cover', 'lyrics')
    @classmethod
    def strip_text(cls, value: str) -> str:
        return value.strip()


class UpdateSongRequest(BaseModel):
    title: str = Field(min_length=1, max_length=240)
    artist: str = Field(min_length=1, max_length=160)
    cover: str = Field(default='', max_length=500)
    lyrics: str = Field(default='', max_length=100000)

    @field_validator('title', 'artist', 'cover', 'lyrics')
    @classmethod
    def strip_text(cls, value: str) -> str:
        return value.strip()


class BulkLyricsItem(BaseModel):
    id: str = Field(min_length=1, max_length=80)
    lyrics: str = Field(min_length=1, max_length=100000)

    @field_validator('id', 'lyrics')
    @classmethod
    def strip_bulk_lyrics_text(cls, value: str) -> str:
        return value.strip()


class BulkLyricsRequest(BaseModel):
    items: list[BulkLyricsItem] = Field(min_length=1, max_length=500)


class AddVideoRequest(BaseModel):
    video_id: str = Field(min_length=6, max_length=32, pattern=r'^[A-Za-z0-9_-]+$')
    title: str = Field(min_length=1, max_length=240)
    uploader: str = Field(default='YouTube', max_length=160)
    cover: str = Field(default='', max_length=500)
    description: str = Field(default='', max_length=5000)
    retention_mode: Literal['permanent', 'temporary'] = 'permanent'

    @field_validator('title', 'uploader', 'cover', 'description')
    @classmethod
    def strip_text(cls, value: str) -> str:
        return value.strip()


class MediaProposalRequest(BaseModel):
    kind: Literal['song', 'video']
    source_id: str = Field(min_length=6, max_length=32, pattern=r'^[A-Za-z0-9_-]+$')
    title: str = Field(min_length=1, max_length=240)
    artist: str = Field(default='', max_length=160)
    uploader: str = Field(default='YouTube', max_length=160)
    cover: str = Field(default='', max_length=500)
    description: str = Field(default='', max_length=5000)

    @field_validator('title', 'artist', 'uploader', 'cover', 'description')
    @classmethod
    def strip_proposal_text(cls, value: str) -> str:
        return value.strip()


class ProposalDecision(BaseModel):
    reason: str = Field(default='', max_length=1000)


class LoginRequest(BaseModel):
    username: str = Field(min_length=2, max_length=80)
    password: str = Field(min_length=1, max_length=256)


class UserRequest(BaseModel):
    username: str = Field(min_length=2, max_length=80)
    password: str = Field(min_length=8, max_length=256)
    role: str = Field(default='user', pattern=r'^(user|admin)$')

    @field_validator('username')
    @classmethod
    def normalize_username(cls, value: str) -> str:
        return value.strip().lower()


class ProfileUpdateRequest(BaseModel):
    display_name: str = Field(default='', max_length=120)
    bio: str = Field(default='', max_length=280)

    @field_validator('display_name', 'bio')
    @classmethod
    def normalize_profile_text(cls, value: str) -> str:
        return value.strip()


class PasswordChangeRequest(BaseModel):
    current_password: str = Field(min_length=1, max_length=256)
    new_password: str = Field(min_length=8, max_length=256)


class AdminUserProfileRequest(BaseModel):
    display_name: str = Field(default='', max_length=120)
    avatar_url: str = Field(default='', max_length=1000)
    bio: str = Field(default='', max_length=280)
    role: str = Field(default='user', pattern=r'^(user|admin)$')

    @field_validator('display_name', 'avatar_url', 'bio')
    @classmethod
    def normalize_admin_profile_text(cls, value: str) -> str:
        return value.strip()


class CreateRoomRequest(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    visibility: Literal['private', 'public'] = 'private'
    max_members: int = Field(default=8, ge=2, le=50)

    @field_validator('name')
    @classmethod
    def normalize_room_name(cls, value: str) -> str:
        return value.strip()


class JoinRoomRequest(BaseModel):
    invite_code: str = Field(min_length=4, max_length=24)

    @field_validator('invite_code')
    @classmethod
    def normalize_invite_code(cls, value: str) -> str:
        return value.strip().upper()


class RoomStateRequest(BaseModel):
    current_song: Optional[dict] = None
    queue: list[dict] = Field(default_factory=list, max_length=300)
    is_playing: bool = False
    position_seconds: float = Field(default=0, ge=0, le=86400)
    expected_version: Optional[int] = Field(default=None, ge=0)


class RoomSettingsRequest(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    visibility: Literal['private', 'public'] = 'private'
    max_members: int = Field(default=8, ge=2, le=50)

    @field_validator('name')
    @classmethod
    def normalize_settings_name(cls, value: str) -> str:
        return value.strip()


class FriendTargetRequest(BaseModel):
    user_id: str = Field(min_length=1, max_length=80)


class PrivacySettingsRequest(BaseModel):
    allow_friend_requests: Literal['everyone', 'friends_of_friends', 'nobody'] = 'everyone'
    allow_direct_messages: Literal['friends', 'room_members', 'nobody'] = 'friends'
    show_online_status: bool = True
    show_current_room: bool = False


class ChatTargetRequest(BaseModel):
    user_id: str = Field(min_length=1, max_length=80)


class ChatMessageRequest(BaseModel):
    body: str = Field(min_length=1, max_length=2000)

    @field_validator('body')
    @classmethod
    def normalize_message_body(cls, value: str) -> str:
        return value.strip()


class ChatReportRequest(BaseModel):
    reason: str = Field(min_length=1, max_length=500)

    @field_validator('reason')
    @classmethod
    def normalize_report_reason(cls, value: str) -> str:
        return value.strip()


def require_supabase() -> Client:
    if supabase is None:
        raise HTTPException(status_code=503, detail='Supabase chưa được cấu hình trên server.')
    return supabase


def password_hash(password: str, salt: Optional[bytes] = None) -> str:
    salt = salt or secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac('sha256', password.encode(), salt, 260_000)
    return f'pbkdf2_sha256$260000${base64.urlsafe_b64encode(salt).decode()}${base64.urlsafe_b64encode(digest).decode()}'


def verify_password(password: str, stored: str) -> bool:
    if not stored:
        return False
    if not stored.startswith('pbkdf2_sha256$'):
        # Backward-compatible one-time migration for the repository's legacy plaintext rows.
        return hmac.compare_digest(password, stored)
    try:
        _, iterations, salt_value, digest_value = stored.split('$', 3)
        salt = base64.urlsafe_b64decode(salt_value.encode())
        expected = base64.urlsafe_b64decode(digest_value.encode())
        actual = hashlib.pbkdf2_hmac('sha256', password.encode(), salt, int(iterations))
        return hmac.compare_digest(actual, expected)
    except (ValueError, TypeError):
        return False


def issue_token(user_id: str, role: str) -> str:
    payload = {'sub': str(user_id), 'role': role, 'exp': int(time.time()) + 60 * 60 * 24 * 7}
    encoded = base64.urlsafe_b64encode(json.dumps(payload, separators=(',', ':')).encode()).decode().rstrip('=')
    signature = hmac.new(AUTH_SECRET.encode(), encoded.encode(), hashlib.sha256).digest()
    return f'{encoded}.{base64.urlsafe_b64encode(signature).decode().rstrip("=")}'


def decode_token(token: str) -> dict:
    try:
        encoded, signature = token.split('.', 1)
        expected = hmac.new(AUTH_SECRET.encode(), encoded.encode(), hashlib.sha256).digest()
        provided = base64.urlsafe_b64decode(signature + '=' * (-len(signature) % 4))
        if not hmac.compare_digest(expected, provided):
            raise ValueError('invalid signature')
        payload = json.loads(base64.urlsafe_b64decode(encoded + '=' * (-len(encoded) % 4)))
        if int(payload.get('exp', 0)) < int(time.time()):
            raise ValueError('expired token')
        return payload
    except (ValueError, TypeError, json.JSONDecodeError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Phiên đăng nhập không hợp lệ hoặc đã hết hạn.')


async def get_current_user(authorization: Optional[str] = Header(default=None)) -> dict:
    if not authorization or not authorization.lower().startswith('bearer '):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Cần đăng nhập để tiếp tục.')
    payload = decode_token(authorization.split(' ', 1)[1].strip())
    client = require_supabase()
    try:
        result = client.table('users').select('id, username, role').eq('id', payload.get('sub')).limit(1).execute()
    except Exception as error:
        error_text = str(error)
        if 'PGRST303' in error_text or 'JWT issued at future' in error_text:
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail='SUPABASE_KEY trên Render đang bị Supabase từ chối vì JWT phát hành ở tương lai. Hãy thay bằng Secret/Service Role key hiện tại trên Supabase rồi redeploy Render.') from error
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail='Backend không thể xác thực tài khoản với Supabase. Kiểm tra SUPABASE_URL và SUPABASE_KEY trên Render.') from error
    if not result.data:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Tài khoản không còn tồn tại.')
    return result.data[0]


async def require_admin(current_user: dict = Depends(get_current_user)) -> dict:
    if current_user.get('role') != 'admin':
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Bạn không có quyền quản trị.')
    return current_user


PROFILE_COLUMNS = 'id,username,role,display_name,avatar_url,bio'


def public_user_payload(record: dict) -> dict:
    return {
        'id': record.get('id'),
        'username': record.get('username', ''),
        'role': record.get('role', 'user'),
        'display_name': record.get('display_name') or record.get('username', ''),
        'avatar_url': record.get('avatar_url') or '',
        'bio': record.get('bio') or '',
    }


def get_profile_record(client: Client, user_id: str) -> dict:
    try:
        response = client.table('users').select(PROFILE_COLUMNS).eq('id', user_id).limit(1).execute()
        record = (response.data or [None])[0]
    except Exception:
        response = client.table('users').select('id,username,role').eq('id', user_id).limit(1).execute()
        record = (response.data or [None])[0]
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Không tìm thấy tài khoản.')
    return record


def update_profile_record(client: Client, user_id: str, payload: dict) -> dict:
    try:
        response = client.table('users').update(payload).eq('id', user_id).select(PROFILE_COLUMNS).execute()
    except Exception as error:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail='Profile chưa được bật. Admin cần chạy supabase/user_profiles.sql trước.') from error
    record = (response.data or [None])[0]
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Không tìm thấy tài khoản.')
    return record


def get_ydl_opts(is_download: bool = False, temp_dir: Optional[str] = None, *, client: str = 'web', format_selector: Optional[str] = None, output_template: Optional[str] = None, postprocessors: Optional[list[dict]] = None, max_filesize: Optional[int] = None) -> dict:
    opts = {
        'extractor_args': {'youtube': {'player_client': [client]}},
        'js_runtimes': {'node': {}},
        'remote_components': ['ejs:github'],
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36'
        },
        'source_address': '0.0.0.0',
        'socket_timeout': 30,
    }
    if is_download:
        cookie_path = Path(os.getenv('YOUTUBE_COOKIES_PATH', '')).expanduser() if os.getenv('YOUTUBE_COOKIES_PATH', '').strip() else Path.cwd() / 'cookies.txt'
        cookies_b64 = os.getenv('YOUTUBE_COOKIES_B64', '').strip()
        if cookies_b64:
            cookie_path = Path(tempfile.gettempdir()) / 'lunu-youtube-cookies.txt'
            try:
                cookie_path.write_bytes(base64.b64decode(cookies_b64))
            except Exception as error:
                raise RuntimeError(f'YOUTUBE_COOKIES_B64 không hợp lệ: {error}')
        if cookie_path.exists():
            opts['cookiefile'] = str(cookie_path)
        if temp_dir:
            opts.update({
                'format': format_selector or 'best[acodec!=none][ext=m4a]/best[acodec!=none][ext=webm]/best[acodec!=none]/best',
                'noplaylist': True,
                'outtmpl': output_template or str(Path(temp_dir) / '%(id)s.%(ext)s'),
                'postprocessors': postprocessors if postprocessors is not None else [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '192'}],
                'merge_output_format': 'mp4',
                'retries': 3,
                'fragment_retries': 3,
                'continuedl': True,
            })
            if max_filesize:
                opts['max_filesize'] = max_filesize
    else:
        opts.update({'extract_flat': True, 'quiet': True, 'skip_download': True})
    return opts


def today_stamp() -> str:
    return datetime.now(ZoneInfo('Asia/Ho_Chi_Minh')).strftime('%d%m%Y')


def tomorrow_midnight_iso() -> str:
    local_now = datetime.now(ZoneInfo('Asia/Ho_Chi_Minh'))
    tomorrow = (local_now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    return tomorrow.isoformat()


def next_media_key(client: Client, table: str, prefix: str = '') -> str:
    try:
        rows = client.table(table).select('media_key').execute().data or []
    except Exception:
        rows = []
    used = set()
    width = 2 if prefix else 3
    pattern = re.compile(rf'^{re.escape(prefix)}(\d{{{width}}})')
    for row in rows:
        match = pattern.match(str(row.get('media_key') or ''))
        if match:
            used.add(int(match.group(1)))
    default_start = int(os.getenv('LUNU_SONG_START_SEQUENCE', '199')) - 1 if not prefix else 0
    sequence = max(used or {default_start}) + 1
    return f'{prefix}{sequence:02d}{today_stamp()}' if prefix else f'{sequence:03d}{today_stamp()}'


def cloudinary_public_id_from_url(url: str) -> Optional[str]:
    if not url:
        return None
    if not url.startswith(('http://', 'https://')):
        return url.strip()
    match = re.search(r'/(?:upload|raw)/(.+)$', url)
    if not match:
        return None
    public_id = match.group(1).split('?', 1)[0]
    public_id = re.sub(r'^v\d+/', '', public_id)
    return re.sub(r'\.[A-Za-z0-9]+$', '', public_id)



def delete_cloudinary_asset(url: str, resource_type: str = 'video') -> None:
    public_id = cloudinary_public_id_from_url(url)
    if not public_id:
        return
    cloudinary.uploader.destroy(public_id, resource_type=resource_type, invalidate=True)


def sanitize_chat_filename(filename: str) -> str:
    clean = Path(filename or 'attachment').name
    clean = ''.join(char for char in clean if ord(char) >= 32 and ord(char) != 127)
    clean = re.sub(r'[^A-Za-z0-9._() -]+', '_', clean).strip(' .')
    return clean[:CHAT_ATTACHMENT_MAX_FILENAME] or 'attachment'


def validate_chat_attachment(filename: str, content_type: str, header: bytes) -> tuple[str, str]:
    suffix = Path(filename).suffix.lower()
    mime = (content_type or '').split(';', 1)[0].strip().lower()
    mime = mime if mime in CHAT_IMAGE_MIMES | CHAT_FILE_MIMES else CHAT_EXTENSION_MIMES.get(suffix, '')
    if mime not in CHAT_IMAGE_MIMES | CHAT_FILE_MIMES:
        raise HTTPException(status_code=415, detail='Định dạng tệp chưa được hỗ trợ. Chỉ nhận ảnh phổ biến, PDF, TXT, CSV, JSON, ZIP và Office.')
    if mime == 'image/jpeg' and not header.startswith(b'\xff\xd8\xff'):
        raise HTTPException(status_code=415, detail='Tệp JPEG không hợp lệ.')
    if mime == 'image/png' and not header.startswith(b'\x89PNG\r\n\x1a\n'):
        raise HTTPException(status_code=415, detail='Tệp PNG không hợp lệ.')
    if mime == 'image/gif' and not header.startswith((b'GIF87a', b'GIF89a')):
        raise HTTPException(status_code=415, detail='Tệp GIF không hợp lệ.')
    if mime == 'image/webp' and not (header.startswith(b'RIFF') and header[8:12] == b'WEBP'):
        raise HTTPException(status_code=415, detail='Tệp WebP không hợp lệ.')
    if mime == 'application/pdf' and not header.startswith(b'%PDF'):
        raise HTTPException(status_code=415, detail='Tệp PDF không hợp lệ.')
    if mime in {'application/zip', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', 'application/vnd.openxmlformats-officedocument.presentationml.presentation'} and not header.startswith(b'PK'):
        raise HTTPException(status_code=415, detail='Tệp Office/ZIP không hợp lệ.')
    return mime, 'image' if mime in CHAT_IMAGE_MIMES else 'file'


def upload_chat_attachment(file_path: Path, public_id: str, resource_type: str) -> dict:
    if not cloudinary_configured:
        raise HTTPException(status_code=503, detail='Cloudinary chưa được cấu hình để nhận tệp chat.')
    return cloudinary.uploader.upload_large(str(file_path), resource_type=resource_type, public_id=public_id, overwrite=False, unique_filename=False, chunk_size=10 * 1024 * 1024)


def delete_chat_attachment(public_id: str, resource_type: str) -> None:
    if not public_id:
        return
    cloudinary.uploader.destroy(public_id, resource_type=resource_type if resource_type in {'image', 'raw', 'video'} else 'raw', invalidate=True)


async def read_chat_upload(file: UploadFile) -> tuple[Path, str, str, int, str]:
    filename = sanitize_chat_filename(file.filename or 'attachment')
    first_chunk = await file.read(8192)
    if not first_chunk:
        raise HTTPException(status_code=400, detail='Tệp đính kèm đang trống.')
    mime, kind = validate_chat_attachment(filename, file.content_type or '', first_chunk)
    temp_handle, temp_name = tempfile.mkstemp(prefix='lunu-chat-', suffix=Path(filename).suffix.lower())
    os.close(temp_handle)
    temp_path = Path(temp_name)
    size = 0
    try:
        with temp_path.open('wb') as output:
            chunk = first_chunk
            while chunk:
                size += len(chunk)
                if size > CHAT_ATTACHMENT_MAX_BYTES:
                    raise HTTPException(status_code=413, detail=f'Tệp quá lớn. Giới hạn attachment chat là {CHAT_ATTACHMENT_MAX_BYTES // (1024 * 1024)} MiB.')
                output.write(chunk)
                chunk = await file.read(1024 * 1024)
        return temp_path, filename, mime, size, kind
    except Exception:
        temp_path.unlink(missing_ok=True)
        raise
    finally:
        await file.close()


def strip_legacy_song_fields(song: dict) -> dict:
    allowed = {'id', 'title', 'artist', 'url', 'cover', 'lyrics'}
    return {key: value for key, value in song.items() if key in allowed}


def _decode_json_text(value: str) -> str:
    try:
        return json.loads(f'"{value}"')
    except json.JSONDecodeError:
        return html.unescape(value).replace('\\"', '"')


def plain_lyrics(value: str) -> str:
    text = str(value or '')
    text = re.sub(r'\[\d{1,2}:\d{2}(?:[.:]\d{1,3})?\]\s*', '', text)
    return re.sub(r'\n{3,}', '\n\n', text).strip()


def search_lrclib(track_name: str, artist_name: str) -> list[dict]:
    params = urllib.parse.urlencode({'track_name': track_name, 'artist_name': artist_name})
    request = urllib.request.Request(
        f'https://lrclib.net/api/search?{params}',
        headers={
            'User-Agent': 'LuNuMusic/2.1 (https://lunu-music.vercel.app)',
            'Accept': 'application/json',
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            payload = json.loads(response.read().decode('utf-8'))
    except urllib.error.HTTPError as error:
        if error.code == 404:
            return []
        raise RuntimeError(f'LRCLIB trả HTTP {error.code}') from error
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as error:
        raise RuntimeError(f'Không thể kết nối LRCLIB: {error}') from error

    if not isinstance(payload, list) or not payload:
        fallback_params = urllib.parse.urlencode({'q': track_name})
        fallback_request = urllib.request.Request(
            f'https://lrclib.net/api/search?{fallback_params}',
            headers={'User-Agent': 'LuNuMusic/2.1 (https://lunu-music.vercel.app)', 'Accept': 'application/json'},
        )
        try:
            with urllib.request.urlopen(fallback_request, timeout=15) as response:
                payload = json.loads(response.read().decode('utf-8'))
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, json.JSONDecodeError):
            payload = []

    results = []
    for item in payload if isinstance(payload, list) else []:
        lyrics = plain_lyrics(item.get('plainLyrics') or item.get('syncedLyrics') or '')
        if not lyrics:
            continue
        results.append({
            'provider': 'LRCLIB',
            'provider_id': item.get('id'),
            'title': item.get('trackName') or item.get('name') or track_name,
            'artist': item.get('artistName') or artist_name,
            'album': item.get('albumName') or '',
            'duration': item.get('duration'),
            'lyrics': lyrics,
            'source_url': f"https://lrclib.net/api/get/{item.get('id')}" if item.get('id') else 'https://lrclib.net',
        })
    return results[:5]


def search_youtube_channel_api(query: str) -> list[dict]:
    api_key = os.getenv('YOUTUBE_API_KEY', '').strip()
    if not api_key:
        return []
    channel_params = urllib.parse.urlencode({'part': 'snippet', 'type': 'channel', 'maxResults': 1, 'q': query, 'regionCode': 'VN', 'relevanceLanguage': 'vi', 'key': api_key})
    channel_request = urllib.request.Request(f'https://www.googleapis.com/youtube/v3/search?{channel_params}', headers={'User-Agent': 'LuNu Music API/1.0'})
    with urllib.request.urlopen(channel_request, timeout=20) as response:
        channel_payload = json.loads(response.read().decode('utf-8'))
    channel_items = channel_payload.get('items') or []
    channel_id = ((channel_items[0].get('id') or {}).get('channelId')) if channel_items else None
    if not channel_id:
        return []
    params = urllib.parse.urlencode({'part': 'snippet', 'type': 'video', 'channelId': channel_id, 'order': 'date', 'maxResults': 10, 'regionCode': 'VN', 'relevanceLanguage': 'vi', 'key': api_key})
    request = urllib.request.Request(f'https://www.googleapis.com/youtube/v3/search?{params}', headers={'User-Agent': 'LuNu Music API/1.0'})
    with urllib.request.urlopen(request, timeout=20) as response:
        payload = json.loads(response.read().decode('utf-8'))
    results = []
    channel_title = (channel_items[0].get('snippet') or {}).get('channelTitle') or query
    for item in payload.get('items') or []:
        video_id = (item.get('id') or {}).get('videoId')
        snippet = item.get('snippet') or {}
        thumbnails = snippet.get('thumbnails') or {}
        thumbnail = (thumbnails.get('high') or thumbnails.get('medium') or thumbnails.get('default') or {}).get('url')
        if video_id:
            results.append({'id': video_id, 'title': html.unescape(snippet.get('title') or ''), 'uploader': snippet.get('channelTitle') or channel_title, 'thumbnail': thumbnail or f'https://i.ytimg.com/vi/{video_id}/hqdefault.jpg'})
    return normalize_search_entries(results)


def search_youtube_data_api(query: str) -> list[dict]:
    api_key = os.getenv('YOUTUBE_API_KEY', '').strip()
    if not api_key:
        return []
    params = urllib.parse.urlencode({'part': 'snippet', 'type': 'video', 'maxResults': 10, 'q': query, 'regionCode': 'VN', 'relevanceLanguage': 'vi', 'key': api_key})
    request = urllib.request.Request(f'https://www.googleapis.com/youtube/v3/search?{params}', headers={'User-Agent': 'LuNu Music API/1.0'})
    with urllib.request.urlopen(request, timeout=20) as response:
        payload = json.loads(response.read().decode('utf-8'))
    results = []
    for item in payload.get('items', []):
        video_id = (item.get('id') or {}).get('videoId')
        snippet = item.get('snippet') or {}
        if video_id and snippet.get('title'):
            thumbnails = snippet.get('thumbnails') or {}
            thumbnail = (thumbnails.get('high') or thumbnails.get('medium') or thumbnails.get('default') or {}).get('url')
            results.append({'id': video_id, 'title': html.unescape(snippet['title']), 'uploader': snippet.get('channelTitle') or 'YouTube', 'thumbnail': thumbnail or f'https://i.ytimg.com/vi/{video_id}/hqdefault.jpg'})
    return normalize_search_entries(results)


def search_youtube_music(query: str) -> list[dict]:
    user_agent = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36'
    page_url = f"https://music.youtube.com/search?q={urllib.parse.quote_plus(query)}"
    page_request = urllib.request.Request(page_url, headers={'User-Agent': user_agent, 'Accept-Language': 'vi-VN,vi;q=0.9,en;q=0.8'})
    with urllib.request.urlopen(page_request, timeout=25) as response:
        page = response.read().decode('utf-8', errors='replace')
    key_match = re.search(r'"INNERTUBE_API_KEY":"([^"]+)"', page)
    version_match = re.search(r'"INNERTUBE_CLIENT_VERSION":"([^"]+)"', page)
    if not key_match or not version_match:
        return []
    body = json.dumps({'context': {'client': {'clientName': 'WEB_REMIX', 'clientVersion': version_match.group(1), 'hl': 'vi', 'gl': 'VN'}}, 'query': query}).encode('utf-8')
    api_request = urllib.request.Request(
        f"https://music.youtube.com/youtubei/v1/search?key={key_match.group(1)}", data=body,
        headers={'User-Agent': user_agent, 'Content-Type': 'application/json', 'Origin': 'https://music.youtube.com'}, method='POST')
    with urllib.request.urlopen(api_request, timeout=25) as response:
        payload = json.loads(response.read().decode('utf-8'))
    results = []

    def text_from_column(column: dict) -> str:
        text = column.get('text', {}) if isinstance(column, dict) else {}
        runs = text.get('runs', []) if isinstance(text, dict) else []
        return ''.join(run.get('text', '') for run in runs if isinstance(run, dict)) or (text.get('simpleText', '') if isinstance(text, dict) else '')

    def collect(node: object) -> None:
        if isinstance(node, dict):
            renderer = node.get('musicResponsiveListItemRenderer')
            if isinstance(renderer, dict):
                playlist_data = renderer.get('playlistItemData') or {}
                video_id = playlist_data.get('videoId') or renderer.get('videoId')
                columns = renderer.get('flexColumns') or []
                title = text_from_column((columns[0].get('musicResponsiveListItemFlexColumnRenderer') or {}) if columns else {})
                artist = text_from_column((columns[1].get('musicResponsiveListItemFlexColumnRenderer') or {}) if len(columns) > 1 else {})
                thumbnails = renderer.get('thumbnail', {}).get('musicThumbnailRenderer', {}).get('thumbnail', {}).get('thumbnails', [])
                if video_id and title:
                    results.append({'id': video_id, 'title': title, 'uploader': artist or 'YouTube', 'thumbnail': thumbnails[-1].get('url') if thumbnails else f'https://i.ytimg.com/vi/{video_id}/hqdefault.jpg'})
            music_video = node.get('musicVideoRenderer')
            if isinstance(music_video, dict):
                video_id = music_video.get('videoId')
                title = text_from_column(music_video.get('title') or {})
                artist = text_from_column(music_video.get('shortDescription') or {})
                if video_id and title:
                    results.append({'id': video_id, 'title': title, 'uploader': artist or 'YouTube', 'thumbnail': f'https://i.ytimg.com/vi/{video_id}/hqdefault.jpg'})
            for value in node.values():
                collect(value)
        elif isinstance(node, list):
            for value in node:
                collect(value)

    collect(payload)
    return normalize_search_entries(results)


def search_youtube_internal(query: str) -> list[dict]:
    page_url = f"https://www.youtube.com/results?search_query={urllib.parse.quote_plus(query)}&hl=vi&gl=VN"
    page_request = urllib.request.Request(page_url, headers={
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/124 Safari/537.36',
        'Accept-Language': 'vi-VN,vi;q=0.9,en;q=0.8',
    })
    with urllib.request.urlopen(page_request, timeout=25) as response:
        page = response.read().decode('utf-8', errors='replace')
    key_match = re.search(r'"INNERTUBE_API_KEY":"([^"]+)"', page)
    version_match = re.search(r'"INNERTUBE_CLIENT_VERSION":"([^"]+)"', page)
    if not key_match or not version_match:
        return []
    request_body = json.dumps({
        'context': {'client': {'clientName': 'WEB', 'clientVersion': version_match.group(1), 'hl': 'vi', 'gl': 'VN'}},
        'query': query,
    }).encode('utf-8')
    api_request = urllib.request.Request(
        f"https://www.youtube.com/youtubei/v1/search?key={key_match.group(1)}",
        data=request_body,
        headers={'User-Agent': 'Mozilla/5.0', 'Content-Type': 'application/json', 'Origin': 'https://www.youtube.com'},
        method='POST',
    )
    with urllib.request.urlopen(api_request, timeout=25) as response:
        payload = json.loads(response.read().decode('utf-8'))
    results = []

    def collect(node: object) -> None:
        if isinstance(node, dict):
            renderer = node.get('videoRenderer')
            if isinstance(renderer, dict):
                video_id = renderer.get('videoId')
                title = renderer.get('title', {})
                title_runs = title.get('runs') if isinstance(title, dict) else []
                title_text = ''.join(item.get('text', '') for item in title_runs if isinstance(item, dict)) if title_runs else title.get('simpleText', '') if isinstance(title, dict) else ''
                owner = renderer.get('ownerText', {})
                owner_runs = owner.get('runs') if isinstance(owner, dict) else []
                owner_text = ''.join(item.get('text', '') for item in owner_runs if isinstance(item, dict)) if owner_runs else 'YouTube'
                thumbnails = renderer.get('thumbnail', {}).get('thumbnails', [])
                thumbnail = thumbnails[-1].get('url') if thumbnails else ''
                if video_id and title_text:
                    results.append({'id': video_id, 'title': title_text, 'uploader': owner_text or 'YouTube', 'thumbnail': thumbnail or f'https://i.ytimg.com/vi/{video_id}/hqdefault.jpg'})
            for value in node.values():
                collect(value)
        elif isinstance(node, list):
            for value in node:
                collect(value)

    collect(payload)
    return normalize_search_entries(results)


def search_youtube_html(query: str) -> list[dict]:
    search_url = f"https://www.youtube.com/results?search_query={urllib.parse.quote_plus(query)}&hl=vi&gl=VN"
    request = urllib.request.Request(search_url, headers={
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/124 Safari/537.36',
        'Accept-Language': 'vi-VN,vi;q=0.9,en;q=0.8',
    })
    with urllib.request.urlopen(request, timeout=25) as response:
        page = response.read().decode('utf-8', errors='replace')
    results = []
    seen = set()
    video_matches = list(re.finditer(r'"videoId":"([A-Za-z0-9_-]{6,})"', page))
    for video_match in video_matches:
        video_id = video_match.group(1)
        if video_id in seen:
            continue
        start = max(0, video_match.start() - 2200)
        end = min(len(page), video_match.end() + 7000)
        block = page[start:end]
        title_match = re.search(r'"title":\{"runs":\[\{"text":"((?:\\.|[^"\\])*)"', block)
        if not title_match:
            title_match = re.search(r'"title":\{"simpleText":"((?:\\.|[^"\\])*)"', block)
        uploader_match = re.search(r'"ownerText":\{"runs":\[\{"text":"((?:\\.|[^"\\])*)"', block)
        if not title_match:
            continue
        seen.add(video_id)
        results.append({
            'id': video_id,
            'title': _decode_json_text(title_match.group(1)),
            'uploader': _decode_json_text(uploader_match.group(1)) if uploader_match else 'YouTube',
            'thumbnail': f'https://i.ytimg.com/vi/{video_id}/hqdefault.jpg',
        })
    return results


def _search_tokens(value: str) -> list[str]:
    normalized = unicodedata.normalize('NFKD', value.casefold())
    normalized = ''.join(char for char in normalized if not unicodedata.combining(char))
    return re.findall(r'[\w]+', normalized, flags=re.UNICODE)


def search_query_variants(query: str) -> list[str]:
    ascii_query = ''.join(char for char in unicodedata.normalize('NFKD', query) if not unicodedata.combining(char))
    variants = [ascii_query, query] if ascii_query.casefold() != query.casefold() else [query]
    return list(dict.fromkeys(variant.strip() for variant in variants if variant.strip()))


def music_search_query_variants(query: str) -> list[str]:
    ascii_query = ''.join(char for char in unicodedata.normalize('NFKD', query) if not unicodedata.combining(char))
    return list(dict.fromkeys([ascii_query, f'{ascii_query} song', f'{ascii_query} MV', f'{ascii_query} music', f'{ascii_query} official', query]))


def has_relevant_result(results: list[dict], query: str) -> bool:
    query_text = ' '.join(_search_tokens(query))
    if not query_text:
        return False
    return any(query_text in ' '.join(_search_tokens(result.get('title', ''))) for result in results)


def rank_search_results(results: list[dict], query: str) -> list[dict]:
    query_tokens = _search_tokens(query)
    query_text = ' '.join(query_tokens)
    unique_results = list({result.get('id'): result for result in results if result.get('id')}.values())

    def score(result: dict) -> tuple[int, str]:
        title_text = ' '.join(_search_tokens(result.get('title', '')))
        token_hits = sum(token in title_text.split() for token in query_tokens)
        phrase_hit = bool(query_text and query_text in title_text)
        return (int(phrase_hit) * 100 + token_hits * 10, title_text)

    return sorted(unique_results, key=score, reverse=True)


def normalize_search_entries(entries: list[dict]) -> list[dict]:
    results = []
    seen = set()
    for entry in entries:
        if not entry:
            continue
        video_id = entry.get('id') or entry.get('videoId')
        title = entry.get('title') or entry.get('name')
        if not video_id or not title or video_id in seen:
            continue
        seen.add(video_id)
        results.append({
            'id': video_id,
            'title': title,
            'uploader': entry.get('uploader') or entry.get('channel') or entry.get('uploader_id') or 'YouTube',
            'thumbnail': entry.get('thumbnail') or f'https://i.ytimg.com/vi/{video_id}/hqdefault.jpg',
        })
    return results


def set_import_job(job_id: str, **updates: object) -> None:
    if job_id in import_jobs:
        import_jobs[job_id].update(updates)


def notify_users(client: Client, user_ids: list[str], title: str, body: str, kind: str = 'system', link: str = '') -> None:
    recipients = list(dict.fromkeys(str(user_id) for user_id in user_ids if user_id))
    if not recipients:
        return
    payload = [{'user_id': user_id, 'title': title[:160], 'body': body[:1000], 'kind': kind[:40], 'link': link[:240], 'is_read': False} for user_id in recipients]
    try:
        client.table('notifications').insert(payload).execute()
    except Exception as error:
        print(f'⚠️ Không thể tạo notification: {error}')


def notify_proposal_status(client: Client, proposal: dict, title: str, body: str, kind: str = 'proposal') -> None:
    notify_users(client, [str(proposal.get('requested_by') or '')], title, body, kind, f"proposal:{proposal.get('id', '')}")


def update_proposal(client: Client, proposal_id: str, updates: dict) -> None:
    try:
        client.table('media_proposals').update(updates).eq('id', proposal_id).execute()
    except Exception as error:
        print(f'⚠️ Không thể cập nhật media proposal {proposal_id}: {error}')


def cleanup_expired_cinema_videos(client: Client, limit: int = 50) -> dict:
    now = datetime.now(ZoneInfo('Asia/Ho_Chi_Minh')).isoformat()
    response = (
        client.table('cinema_videos')
        .select('id,media_key,url,cloudinary_public_id,expires_at')
        .eq('retention_mode', 'temporary')
        .lt('expires_at', now)
        .order('expires_at')
        .limit(limit)
        .execute()
    )
    deleted = 0
    failed = 0
    for row in response.data or []:
        try:
            asset = row.get('cloudinary_public_id') or row.get('url')
            if asset:
                delete_cloudinary_asset(asset, resource_type='video')
            client.table('cinema_videos').delete().eq('id', row['id']).execute()
            deleted += 1
        except Exception as error:
            failed += 1
            print(f'⚠️ Không thể dọn video tạm {row.get("media_key")}: {error}')
    return {'deleted_count': deleted, 'failed_count': failed, 'scanned_count': len(response.data or [])}


def is_missing_table_error(error: Exception, table_name: str) -> bool:
    detail = str(error)
    return table_name in detail and ('PGRST205' in detail or 'schema cache' in detail or 'Could not find the table' in detail)


def available_media_files(temp_dir: str, video_id: str) -> list[Path]:
    image_extensions = {'.jpg', '.jpeg', '.png', '.webp', '.gif', '.vtt', '.part', '.ytdl'}
    return [item for item in Path(temp_dir).glob(f'{video_id}*') if item.is_file() and item.suffix.lower() not in image_extensions]


def cloudinary_rejects_large_file(error: Exception) -> bool:
    message = str(error).lower()
    nginx_413 = '413' in message and ('request entity too large' in message or 'nginx' in message)
    explicit_limit = (
        ('file size too large' in message or 'maximum is' in message or 'maximum file size' in message)
        and ('104857600' in message or '100 mb' in message or '100mb' in message)
    )
    return nginx_413 or explicit_limit


def _media_duration_seconds(input_path: Path) -> float:
    probe = subprocess.run(
        [
            'ffprobe', '-v', 'error', '-show_entries', 'format=duration',
            '-of', 'default=noprint_wrappers=1:nokey=1', str(input_path),
        ], capture_output=True, text=True, timeout=60,
    )
    try:
        duration = float(probe.stdout.strip())
    except (TypeError, ValueError):
        duration = 0
    if duration <= 0:
        raise RuntimeError('Không xác định được thời lượng media để nén tương thích Cloudinary.')
    return duration


def transcode_audio_for_cloudinary(input_path: Path, output_path: Path) -> None:
    duration = _media_duration_seconds(input_path)
    target_bits_per_second = int((CLOUDINARY_SAFE_VIDEO_BYTES * 8 * 0.82) / duration)
    audio_bitrate = max(32_000, min(128_000, target_bits_per_second))
    command = [
        'ffmpeg', '-y', '-i', str(input_path),
        '-map', '0:a:0?', '-vn', '-codec:a', 'libmp3lame',
        '-b:a', str(audio_bitrate), '-ar', '44100', '-ac', '2',
        '-id3v2_version', '3', str(output_path),
    ]
    completed = subprocess.run(
        command, capture_output=True, text=True, timeout=VIDEO_TRANSCODE_TIMEOUT_SECONDS,
    )
    if completed.returncode != 0 or not output_path.exists():
        raise RuntimeError(f'FFmpeg không thể nén MP3 để upload: {completed.stderr[-800:]}')
    compressed_size = output_path.stat().st_size
    if compressed_size >= CLOUDINARY_PLAN_LIMIT_BYTES:
        output_path.unlink(missing_ok=True)
        raise RuntimeError(
            f'MP3 sau khi nén vẫn vượt giới hạn Cloudinary ({compressed_size} bytes >= {CLOUDINARY_PLAN_LIMIT_BYTES}).'
        )


def transcode_video_for_cloudinary(input_path: Path, output_path: Path) -> None:
    duration = _media_duration_seconds(input_path)

    target_bits_per_second = int((CLOUDINARY_SAFE_VIDEO_BYTES * 8 * 0.88) / duration)
    audio_bitrate = 64_000
    video_bitrate = max(180_000, target_bits_per_second - audio_bitrate)
    command = [
        'ffmpeg', '-y', '-i', str(input_path),
        '-vf', "scale='min(1280,iw)':-2",
        '-c:v', 'libx264', '-preset', 'veryfast', '-b:v', str(video_bitrate),
        '-maxrate', str(video_bitrate), '-bufsize', str(video_bitrate * 2),
        '-c:a', 'aac', '-b:a', str(audio_bitrate), '-ac', '2',
        '-movflags', '+faststart', '-threads', '2', str(output_path),
    ]
    completed = subprocess.run(
        command, capture_output=True, text=True, timeout=VIDEO_TRANSCODE_TIMEOUT_SECONDS,
    )
    if completed.returncode != 0 or not output_path.exists():
        raise RuntimeError(f'FFmpeg không thể nén video để upload: {completed.stderr[-800:]}')
    compressed_size = output_path.stat().st_size
    if compressed_size >= CLOUDINARY_PLAN_LIMIT_BYTES:
        output_path.unlink(missing_ok=True)
        raise RuntimeError(
            f'Video sau khi nén vẫn vượt giới hạn Cloudinary ({compressed_size} bytes >= {CLOUDINARY_PLAN_LIMIT_BYTES}).'
        )


def upload_cloudinary_media(file_path: Path, public_id: str, resource_type: str, status_callback=None, fallback_kind: str = 'video') -> dict:
    if resource_type == 'video':
        try:
            if status_callback:
                status_callback('Đang upload video Cloudinary theo chunk 20 MiB...')
            return cloudinary.uploader.upload_large(
                str(file_path),
                resource_type='video',
                public_id=public_id,
                overwrite=False,
                unique_filename=False,
                chunk_size=20 * 1024 * 1024,
            )
        except Exception as error:
            if not cloudinary_rejects_large_file(error):
                raise
            extension = 'mp3' if fallback_kind == 'audio' else 'mp4'
            compressed_path = file_path.with_name(f'{file_path.stem}-cloudinary.{extension}')
            if status_callback:
                status_callback(
                    'Cloudinary plan giới hạn 100 MiB; đang nén '
                    f'{"MP3" if fallback_kind == "audio" else "video"} xuống bản tương thích...'
                )
            try:
                if fallback_kind == 'audio':
                    transcode_audio_for_cloudinary(file_path, compressed_path)
                else:
                    transcode_video_for_cloudinary(file_path, compressed_path)
                if status_callback:
                    status_callback(
                        f'Đã nén {"MP3" if fallback_kind == "audio" else "video"} còn '
                        f'{compressed_path.stat().st_size} bytes; đang upload bản tương thích...'
                    )
                try:
                    return cloudinary.uploader.upload(
                        str(compressed_path),
                        resource_type=resource_type,
                        public_id=public_id,
                        overwrite=False,
                        unique_filename=False,
                    )
                except Exception as fallback_error:
                    if cloudinary_rejects_large_file(fallback_error):
                        raise RuntimeError(
                            f'{"MP3" if fallback_kind == "audio" else "Video"} đã nén vẫn bị Cloudinary từ chối do vượt giới hạn 100 MiB.'
                        ) from fallback_error
                    raise
            finally:
                compressed_path.unlink(missing_ok=True)
    return cloudinary.uploader.upload(
        str(file_path),
        resource_type=resource_type,
        public_id=public_id,
        overwrite=False,
        unique_filename=False,
    )


def run_ffmpeg(input_path: Path, output_path: Path, mode: str) -> None:
    if mode == 'song':
        command = ['ffmpeg', '-y', '-i', str(input_path), '-vn', '-codec:a', 'libmp3lame', '-b:a', '192k', str(output_path)]
    else:
        command = ['ffmpeg', '-y', '-i', str(input_path), '-c:v', 'libx264', '-c:a', 'aac', '-movflags', '+faststart', str(output_path)]
    completed = subprocess.run(command, capture_output=True, text=True, timeout=240)
    if completed.returncode != 0:
        if mode == 'video':
            fallback = ['ffmpeg', '-y', '-i', str(input_path), '-c:v', 'libx264', '-an', '-movflags', '+faststart', str(output_path)]
            completed = subprocess.run(fallback, capture_output=True, text=True, timeout=240)
        if completed.returncode != 0:
            raise RuntimeError(f'FFmpeg không thể chuyển đổi file: {completed.stderr[-600:]}')


def download_media(video_id: str, temp_dir: str, mode: str) -> Path:
    url = f'https://www.youtube.com/watch?v={video_id}'
    profiles = [
        ('web', 'best[acodec!=none][ext=m4a]/best[acodec!=none][ext=webm]/best[acodec!=none]/best'),
        ('tv', 'best[acodec!=none]/best'),
        ('ios', 'best[acodec!=none]/best'),
    ] if mode == 'song' else [
        ('web', 'best[height<=480][filesize<450M][ext=mp4]/best[height<=360][filesize<450M][ext=mp4]/best[height<=360]'),
        ('tv', 'best[height<=360][filesize<450M]/best[height<=360]'),
        ('ios', 'best[height<=360][filesize<450M]/best[height<=360]'),
    ]
    errors = []
    for profile_index, (client, selector) in enumerate(profiles):
        if profile_index:
            time.sleep(min(6, 1.5 * (2 ** (profile_index - 1))))
        try:
            options = get_ydl_opts(
                True,
                temp_dir,
                client=client,
                format_selector=selector,
                postprocessors=[] if mode == 'video' else None,
                max_filesize=RENDER_MAX_DOWNLOAD_BYTES if mode == 'video' else None,
            )
            with yt_dlp.YoutubeDL(options) as ydl:
                info = ydl.extract_info(url, download=False)
                if mode == 'video':
                    selected_formats = info.get('requested_formats') or [info]
                    estimated_size = sum(
                        int(item.get('filesize') or item.get('filesize_approx') or 0)
                        for item in selected_formats if isinstance(item, dict)
                    )
                    if estimated_size > RENDER_MAX_DOWNLOAD_BYTES:
                        raise MediaTooLargeError(
                            f'Video nguồn khoảng {estimated_size} bytes, vượt giới hạn an toàn của Render '
                            f'{RENDER_MAX_DOWNLOAD_BYTES} bytes (mặc định 450 MiB). Hãy chọn video/chất lượng thấp hơn hoặc upload file từ máy cá nhân.'
                        )
                if mode == 'song':
                    formats = info.get('formats') or []
                    has_audio = any(item.get('acodec') not in (None, 'none') for item in formats)
                    if not has_audio:
                        raise RuntimeError('YouTube chỉ trả thumbnail/hình ảnh cho video này, không có audio stream để tải.')
                ydl.download([url])
            files = available_media_files(temp_dir, video_id)
            if mode == 'song':
                mp3_files = sorted(Path(temp_dir).glob(f'{video_id}*.mp3'))
                if mp3_files:
                    return mp3_files[0]
                source = next((item for item in files if item.suffix.lower() in {'.m4a', '.webm', '.mp4', '.opus', '.aac'}), None)
                if not source:
                    raise FileNotFoundError('yt-dlp không tạo được file audio.')
                output = Path(temp_dir) / f'{video_id}.mp3'
                run_ffmpeg(source, output, 'song')
                return output
            mp4_files = sorted(Path(temp_dir).glob(f'{video_id}*.mp4'))
            if mp4_files:
                return mp4_files[0]
            source = next((item for item in files if item.suffix.lower() in {'.webm', '.mkv', '.mov', '.m4v'}), None)
            if not source:
                raise FileNotFoundError('yt-dlp không tạo được file video.')
            output = Path(temp_dir) / f'{video_id}.mp4'
            run_ffmpeg(source, output, 'video')
            return output
        except MediaTooLargeError:
            raise
        except Exception as error:
            error_text = str(error)
            if '[Errno 101]' in error_text or 'Network is unreachable' in error_text:
                errors.append(f'{client}: Render không có route mạng tới stream YouTube (Errno 101); đã thử lại với IPv4/backoff')
            else:
                errors.append(f'{client}: {error}')
            for item in available_media_files(temp_dir, video_id):
                item.unlink(missing_ok=True)
    raise RuntimeError('Không tải được media từ YouTube sau nhiều profile: ' + ' | '.join(errors[-3:]))


def process_and_upload_song(job_id: str, request_data: dict) -> None:
    video_id = request_data['video_id']
    proposal_id = request_data.get('proposal_id')
    temp_dir = tempfile.mkdtemp(prefix='lunu-song-')
    file_path: Optional[Path] = None
    client: Optional[Client] = None
    set_import_job(job_id, status='processing', message='Đang tải audio từ YouTube...')
    try:
        client = require_supabase()
        if not all(os.getenv(key, '').strip() for key in ('CLOUDINARY_CLOUD_NAME', 'CLOUDINARY_API_KEY', 'CLOUDINARY_API_SECRET')):
            raise RuntimeError('Cloudinary chưa được cấu hình trên Render.')
        media_key = next_media_key(client, 'songs')
        file_path = download_media(video_id, temp_dir, 'song')
        file_size_bytes = file_path.stat().st_size if file_path.exists() else None
        if proposal_id:
            update_proposal(client, proposal_id, {'file_size_bytes': file_size_bytes})
        set_import_job(job_id, message=f'Đã tải MP3 ({file_size_bytes or 0} bytes), đang upload Cloudinary với mã {media_key}...')
        public_id = f'lunu_music/{media_key}'
        result = upload_cloudinary_media(
            file_path,
            public_id,
            'video',
            status_callback=lambda message: set_import_job(job_id, message=f'{message} Mã {media_key}.'),
            fallback_kind='audio',
        )
        secure_url = result.get('secure_url')
        if not secure_url:
            raise RuntimeError('Cloudinary không trả về secure_url.')
        song_data = {
            'id': str(uuid.uuid4()), 'media_key': media_key, 'source_id': video_id,
            'cloudinary_public_id': public_id, 'title': request_data['title'], 'artist': request_data['artist'],
            'url': secure_url, 'cover': DEFAULT_COVER,
            'lyrics': request_data.get('lyrics', ''),
        }
        set_import_job(job_id, message='Đã upload Cloudinary, đang ghi metadata vào Supabase...')
        existing = client.table('songs').select('id,url,cloudinary_public_id').eq('source_id', video_id).limit(1).execute()
        if existing.data:
            old = existing.data[0]
            client.table('songs').update({key: value for key, value in song_data.items() if key != 'id'}).eq('id', old['id']).execute()
            song_data['id'] = old['id']
            if old.get('url') and old.get('url') != secure_url:
                try:
                    delete_cloudinary_asset(old['url'])
                except Exception as cleanup_error:
                    print(f'⚠️ Không xóa được asset cũ: {cleanup_error}')
            message = 'Đã cập nhật bài hát và thay file Cloudinary thành công.'
        else:
            client.table('songs').insert(song_data).execute()
            message = 'Đã thêm bài hát và file MP3 vào thư viện.'
        set_import_job(job_id, status='completed', message=message, song=song_data)
        if proposal_id and client:
            update_proposal(client, proposal_id, {'status': 'approved', 'job_id': job_id, 'media_key': media_key, 'file_size_bytes': file_path.stat().st_size if file_path and file_path.exists() else None})
            notify_proposal_status(client, request_data.get('proposal', {}), 'Đề xuất nhạc đã được duyệt', f'Bài “{song_data["title"]}” đã được admin duyệt và thêm vào thư viện LuNu Music.', 'proposal-approved')
        print(f'✅ Đã thêm bài hát {media_key}: {song_data["title"]}')
    except Exception as error:
        set_import_job(job_id, status='failed', message=str(error))
        if proposal_id and client:
            update_proposal(client, proposal_id, {'status': 'failed', 'job_id': job_id, 'rejection_reason': str(error)[:1000]})
            notify_proposal_status(client, request_data.get('proposal', {}), 'Đề xuất nhạc chưa thể xử lý', f'Bài “{request_data.get("title", "")}" chưa được thêm: {error}', 'proposal-failed')
        print(f'❌ Lỗi xử lý audio {video_id}: {error}')
    finally:
        if file_path and file_path.exists():
            file_path.unlink(missing_ok=True)
        shutil.rmtree(temp_dir, ignore_errors=True)


def process_and_upload_video(job_id: str, request_data: dict) -> None:
    video_id = request_data['video_id']
    proposal_id = request_data.get('proposal_id')
    temp_dir = tempfile.mkdtemp(prefix='lunu-cinema-')
    file_path: Optional[Path] = None
    client: Optional[Client] = None
    set_import_job(job_id, status='processing', message='Đang tải video từ YouTube...')
    try:
        client = require_supabase()
        if not all(os.getenv(key, '').strip() for key in ('CLOUDINARY_CLOUD_NAME', 'CLOUDINARY_API_KEY', 'CLOUDINARY_API_SECRET')):
            raise RuntimeError('Cloudinary chưa được cấu hình trên Render.')
        media_key = next_media_key(client, 'cinema_videos', 'VD')
        file_path = download_media(video_id, temp_dir, 'video')
        file_size_bytes = file_path.stat().st_size if file_path.exists() else None
        if proposal_id:
            update_proposal(client, proposal_id, {'file_size_bytes': file_size_bytes})
        set_import_job(job_id, message=f'Đã tải video ({file_size_bytes or 0} bytes), đang upload Cloudinary với mã {media_key}...')
        public_id = f'lunu_cinema/{media_key}'
        set_import_job(job_id, message=f'Đã tải video ({file_size_bytes or 0} bytes), đang upload Cloudinary theo chunk 20 MiB với mã {media_key}...')
        result = upload_cloudinary_media(
            file_path,
            public_id,
            'video',
            status_callback=lambda message: set_import_job(job_id, message=f'{message} Mã {media_key}.'),
        )
        secure_url = result.get('secure_url')
        if not secure_url:
            raise RuntimeError('Cloudinary không trả về secure_url cho video.')
        retention_mode = request_data.get('retention_mode') or 'permanent'
        expires_at = tomorrow_midnight_iso() if retention_mode == 'temporary' else None
        video_data = {
            'id': str(uuid.uuid4()), 'media_key': media_key, 'source_id': video_id,
            'cloudinary_public_id': public_id, 'title': request_data['title'], 'uploader': request_data.get('uploader') or 'YouTube',
            'url': secure_url, 'cover': DEFAULT_COVER,
            'description': request_data.get('description', ''),
            'retention_mode': retention_mode, 'expires_at': expires_at,
        }
        set_import_job(job_id, message='Đã upload Cloudinary, đang ghi video vào Supabase...')
        existing = client.table('cinema_videos').select('id,url').eq('source_id', video_id).limit(1).execute()
        if existing.data:
            old = existing.data[0]
            client.table('cinema_videos').update({key: value for key, value in video_data.items() if key != 'id'}).eq('id', old['id']).execute()
            video_data['id'] = old['id']
            if old.get('url') and old.get('url') != secure_url:
                try:
                    delete_cloudinary_asset(old['url'])
                except Exception as cleanup_error:
                    print(f'⚠️ Không xóa được video Cloudinary cũ: {cleanup_error}')
            message = 'Đã cập nhật video trong LuNu Cinema.'
        else:
            client.table('cinema_videos').insert(video_data).execute()
            message = 'Đã thêm video vào LuNu Cinema.'
        set_import_job(job_id, status='completed', message=message, video=video_data)
        if proposal_id and client:
            update_proposal(client, proposal_id, {'status': 'approved', 'job_id': job_id, 'media_key': media_key, 'file_size_bytes': file_path.stat().st_size if file_path and file_path.exists() else None})
            notify_proposal_status(client, request_data.get('proposal', {}), 'Đề xuất video đã được duyệt', f'Video “{video_data["title"]}” đã được admin duyệt và thêm vào LuNu Tea Room.', 'proposal-approved')
        print(f'✅ Đã thêm video {media_key}: {video_data["title"]}')
    except Exception as error:
        set_import_job(job_id, status='failed', message=str(error))
        if proposal_id and client:
            update_proposal(client, proposal_id, {'status': 'failed', 'job_id': job_id, 'rejection_reason': str(error)[:1000]})
            notify_proposal_status(client, request_data.get('proposal', {}), 'Đề xuất video chưa thể xử lý', f'Video “{request_data.get("title", "")}" chưa được thêm: {error}', 'proposal-failed')
        print(f'❌ Lỗi xử lý video {video_id}: {error}')
    finally:
        if file_path and file_path.exists():
            file_path.unlink(missing_ok=True)
        shutil.rmtree(temp_dir, ignore_errors=True)


def normalize_room_media(item: Optional[dict]) -> Optional[dict]:
    if not isinstance(item, dict):
        return None
    allowed = ('id', 'title', 'artist', 'cover', 'url', 'audio_url', 'audioUrl', 'media_key')
    payload = {}
    for key in allowed:
        value = item.get(key)
        if value is not None and value != '':
            payload[key] = str(value)[:1000]
    return payload or None


def room_snapshot(client: Client, room: dict) -> dict:
    member_rows = client.table('room_members').select('id,room_id,user_id,role,joined_at,last_seen_at').eq('room_id', room['id']).order('joined_at').limit(50).execute().data or []
    user_ids = [row.get('user_id') for row in member_rows if row.get('user_id')]
    users_by_id = {}
    if user_ids:
        user_rows = client.table('users').select('id,username,role,display_name,avatar_url').in_('id', user_ids).limit(50).execute().data or []
        users_by_id = {str(row['id']): public_user_payload(row) for row in user_rows}
    members = [{**row, 'user': users_by_id.get(str(row.get('user_id')), {'id': row.get('user_id'), 'username': 'member', 'display_name': 'Member', 'avatar_url': '', 'role': 'user', 'bio': ''})} for row in member_rows]
    return {
        'id': room.get('id'), 'name': room.get('name'), 'invite_code': room.get('invite_code'),
        'host_id': room.get('host_id'), 'visibility': room.get('visibility', 'private'),
        'max_members': room.get('max_members', 8), 'status': room.get('status', 'active'),
        'current_song': room.get('current_song'), 'queue': room.get('queue') or [],
        'is_playing': bool(room.get('is_playing')), 'position_seconds': float(room.get('position_seconds') or 0),
        'state_version': int(room.get('state_version') or 0), 'created_at': room.get('created_at'),
        'updated_at': room.get('updated_at'), 'members': members,
    }


def get_room(client: Client, room_id: str) -> dict:
    response = client.table('listening_rooms').select('*').eq('id', room_id).limit(1).execute()
    room = (response.data or [None])[0]
    if not room:
        raise HTTPException(status_code=404, detail='Không tìm thấy phòng nghe.')
    if room.get('status') != 'active':
        raise HTTPException(status_code=410, detail='Phòng nghe này đã đóng.')
    return room


def get_room_member(client: Client, room_id: str, user_id: str) -> Optional[dict]:
    response = client.table('room_members').select('id,room_id,user_id,role,joined_at,last_seen_at').eq('room_id', room_id).eq('user_id', user_id).limit(1).execute()
    return (response.data or [None])[0]


def make_invite_code() -> str:
    return re.sub(r'[^A-Z0-9]', '', secrets.token_urlsafe(8).upper())[:10]


def chat_get_conversation(client: Client, conversation_id: str) -> dict:
    row = (client.table('conversations').select('id,kind,room_id,direct_key,created_by,created_at,updated_at').eq('id', conversation_id).limit(1).execute().data or [None])[0]
    if not row:
        raise HTTPException(status_code=404, detail='Không tìm thấy cuộc trò chuyện.')
    return row


def chat_member(client: Client, conversation_id: str, user_id: str) -> Optional[dict]:
    return (client.table('conversation_members').select('conversation_id,user_id,joined_at,last_read_at').eq('conversation_id', conversation_id).eq('user_id', user_id).limit(1).execute().data or [None])[0]


def assert_chat_access(client: Client, conversation_id: str, user_id: str) -> tuple[dict, dict]:
    """Require a current conversation membership and re-check its social/room authority."""
    conversation = chat_get_conversation(client, conversation_id)
    membership = chat_member(client, conversation_id, user_id)
    if not membership:
        raise HTTPException(status_code=403, detail='Bạn không thuộc cuộc trò chuyện này.')
    kind = conversation.get('kind')
    if kind == 'room':
        room_id = str(conversation.get('room_id') or '')
        if not room_id:
            raise HTTPException(status_code=403, detail='Cuộc trò chuyện phòng không hợp lệ.')
        get_room(client, room_id)
        if not get_room_member(client, room_id, user_id):
            raise HTTPException(status_code=403, detail='Bạn không còn là thành viên của phòng nghe này.')
    elif kind == 'direct':
        direct_ids = [part for part in str(conversation.get('direct_key') or '').split(':') if part]
        if user_id not in direct_ids or len(direct_ids) != 2:
            raise HTTPException(status_code=403, detail='Bạn không có quyền truy cập cuộc trò chuyện này.')
        other_id = direct_ids[0] if direct_ids[1] == user_id else direct_ids[1]
        if chat_is_blocked(client, user_id, other_id):
            raise HTTPException(status_code=403, detail='Cuộc trò chuyện đã bị chặn.')
        if not chat_are_friends(client, user_id, other_id):
            raise HTTPException(status_code=403, detail='Cuộc trò chuyện trực tiếp chỉ dành cho bạn bè đã chấp nhận.')
        if chat_privacy(client, other_id).get('allow_direct_messages', 'friends') == 'nobody':
            raise HTTPException(status_code=403, detail='User này hiện không nhận tin nhắn trực tiếp.')
    else:
        raise HTTPException(status_code=403, detail='Loại cuộc trò chuyện không được hỗ trợ.')
    return conversation, membership


def enforce_chat_send_rate_limit(user_id: str) -> None:
    now = time.monotonic()
    window = chat_send_windows.setdefault(str(user_id), deque())
    while window and now - window[0] >= CHAT_RATE_LIMIT_WINDOW_SECONDS:
        window.popleft()
    if len(window) >= CHAT_RATE_LIMIT_COUNT:
        raise HTTPException(status_code=429, detail='Bạn gửi tin nhắn quá nhanh. Vui lòng thử lại sau một lát.')
    window.append(now)
    if len(chat_send_windows) > 5000:
        for key in list(chat_send_windows)[:1000]:
            if not chat_send_windows[key]:
                chat_send_windows.pop(key, None)


def chat_is_blocked(client: Client, first_id: str, second_id: str) -> bool:
    rows = client.table('blocks').select('id').or_(f'and(blocker_id.eq.{first_id},blocked_id.eq.{second_id}),and(blocker_id.eq.{second_id},blocked_id.eq.{first_id})').limit(1).execute().data or []
    return bool(rows)


def chat_are_friends(client: Client, first_id: str, second_id: str) -> bool:
    rows = client.table('friendships').select('id').eq('status', 'accepted').or_(f'and(requester_id.eq.{first_id},addressee_id.eq.{second_id}),and(requester_id.eq.{second_id},addressee_id.eq.{first_id})').limit(1).execute().data or []
    return bool(rows)


def chat_privacy(client: Client, user_id: str) -> dict:
    try:
        row = (client.table('users').select('privacy_settings').eq('id', user_id).limit(1).execute().data or [{}])[0]
        return row.get('privacy_settings') or {}
    except Exception:
        return {}


def chat_message_payload(row: dict, users: dict) -> dict:
    sender_id = str(row.get('sender_id') or '')
    return {**row, 'sender': users.get(sender_id, {'id': sender_id, 'username': 'member', 'display_name': 'Member', 'avatar_url': '', 'role': 'user', 'bio': ''})}


def cleanup_expired_chat_messages(client: Client, limit: int = 100) -> int:
    cutoff = datetime.now(ZoneInfo('UTC')).isoformat()
    rows = client.table('chat_messages').select('id,attachment_public_id,attachment_resource_type').lte('expires_at', cutoff).order('expires_at').limit(limit).execute().data or []
    deleted = 0
    for row in rows:
        try:
            if row.get('attachment_public_id'):
                delete_chat_attachment(row['attachment_public_id'], row.get('attachment_resource_type') or 'raw')
            client.table('chat_messages').delete().eq('id', row['id']).execute()
            deleted += 1
        except Exception as error:
            print(f'⚠️ Không thể dọn attachment chat {row.get("id")}: {error}')
    return deleted


async def broadcast_chat_event(conversation_id: str, event: dict) -> None:
    connections = chat_connections.get(str(conversation_id), set()).copy()
    stale = []
    for connection in connections:
        try:
            await connection.send_json(event)
        except Exception:
            stale.append(connection)
    for connection in stale:
        chat_connections.get(str(conversation_id), set()).discard(connection)
        chat_connection_users.pop(connection, None)


@app.get('/api/health')
async def health() -> dict:
    return {
        'ok': True,
        'supabase_configured': supabase is not None,
        'video_pipeline': 'preflight-450mb-chunked',
        'video_download_limit_bytes': RENDER_MAX_DOWNLOAD_BYTES,
        'chat_attachment_max_bytes': CHAT_ATTACHMENT_MAX_BYTES,
    }


def social_users_map(client: Client, user_ids: list[str]) -> dict:
    if not user_ids:
        return {}
    try:
        rows = client.table('users').select('id,username,role,display_name,avatar_url,bio').in_('id', user_ids).limit(50).execute().data or []
    except Exception:
        rows = client.table('users').select('id,username,role').in_('id', user_ids).limit(50).execute().data or []
    return {str(row.get('id')): public_user_payload(row) for row in rows}


def friendship_payload(row: dict, users: dict, current_user_id: str) -> dict:
    other_id = row.get('addressee_id') if str(row.get('requester_id')) == str(current_user_id) else row.get('requester_id')
    return {**row, 'other_user': users.get(str(other_id), {'id': other_id, 'username': 'member', 'display_name': 'Member', 'avatar_url': '', 'role': 'user', 'bio': ''}), 'direction': 'outgoing' if str(row.get('requester_id')) == str(current_user_id) else 'incoming'}


@app.get('/api/users/search')
async def search_users(q: str = Query(default='', min_length=0, max_length=80), client: Client = Depends(require_supabase), current_user: dict = Depends(get_current_user)) -> list:
    query = re.sub(r'[^a-zA-Z0-9À-ỹ _.-]', '', q).strip()
    if len(query) < 2:
        return []
    try:
        response = client.table('users').select(PROFILE_COLUMNS).or_(f'username.ilike.%{query}%,display_name.ilike.%{query}%').neq('id', current_user['id']).limit(20).execute()
    except Exception:
        response = client.table('users').select('id,username,role').ilike('username', f'%{query}%').neq('id', current_user['id']).limit(20).execute()
    return [public_user_payload(row) for row in (response.data or [])]


@app.get('/api/friends')
async def get_friends(client: Client = Depends(require_supabase), current_user: dict = Depends(get_current_user)) -> dict:
    try:
        rows = client.table('friendships').select('id,requester_id,addressee_id,status,created_at,updated_at,accepted_at').or_(f'requester_id.eq.{current_user["id"]},addressee_id.eq.{current_user["id"]}').order('updated_at', desc=True).limit(100).execute().data or []
        ids = list({str(row.get('requester_id')) for row in rows} | {str(row.get('addressee_id')) for row in rows})
        users = social_users_map(client, ids)
        return {'items': [friendship_payload(row, users, str(current_user['id'])) for row in rows], 'friends': [friendship_payload(row, users, str(current_user['id'])) for row in rows if row.get('status') == 'accepted']}
    except Exception as error:
        raise HTTPException(status_code=503, detail='Friend system chưa được bật. Admin cần chạy supabase/social_friends.sql trước.') from error


@app.post('/api/friends/requests', status_code=status.HTTP_201_CREATED)
async def send_friend_request(request: FriendTargetRequest, client: Client = Depends(require_supabase), current_user: dict = Depends(get_current_user)) -> dict:
    target_id = str(request.user_id)
    if target_id == str(current_user['id']):
        raise HTTPException(status_code=400, detail='Bạn không thể tự gửi lời mời kết bạn cho mình.')
    target = client.table('users').select('id,username,role,display_name,avatar_url,bio').eq('id', target_id).limit(1).execute().data or []
    if not target:
        raise HTTPException(status_code=404, detail='Không tìm thấy user này.')
    blocked = client.table('blocks').select('id').or_(f'and(blocker_id.eq.{current_user["id"]},blocked_id.eq.{target_id}),and(blocker_id.eq.{target_id},blocked_id.eq.{current_user["id"]})').limit(1).execute().data or []
    if blocked:
        raise HTTPException(status_code=403, detail='Không thể gửi lời mời do một trong hai tài khoản đang chặn nhau.')
    existing = client.table('friendships').select('id,status,requester_id,addressee_id').or_(f'and(requester_id.eq.{current_user["id"]},addressee_id.eq.{target_id}),and(requester_id.eq.{target_id},addressee_id.eq.{current_user["id"]})').limit(1).execute().data or []
    if existing:
        row = existing[0]
        if row.get('status') == 'rejected':
            updated = client.table('friendships').update({'requester_id': current_user['id'], 'addressee_id': target_id, 'status': 'pending', 'updated_at': datetime.now(ZoneInfo('Asia/Ho_Chi_Minh')).isoformat()}).eq('id', row['id']).select('*').execute().data or []
            friendship = (updated or [row])[0]
        else:
            raise HTTPException(status_code=409, detail='Hai tài khoản đã có một quan hệ hoặc lời mời đang tồn tại.')
    else:
        friendship = (client.table('friendships').insert({'requester_id': current_user['id'], 'addressee_id': target_id, 'status': 'pending'}).select('*').execute().data or [None])[0]
    try:
        notify_users(client, [target_id], 'Lời mời kết bạn mới', f'{current_user.get("display_name") or current_user.get("username", "Một user")} muốn kết bạn với bạn.', 'friend-request', f'friendship:{friendship["id"]}')
    except Exception as error:
        print(f'⚠️ Không thể tạo notification friend request: {error}')
    return {'success': True, 'friendship': friendship, 'message': 'Đã gửi lời mời kết bạn.'}


@app.post('/api/friends/requests/{friendship_id}/accept')
async def accept_friend_request(friendship_id: str, client: Client = Depends(require_supabase), current_user: dict = Depends(get_current_user)) -> dict:
    row = (client.table('friendships').select('*').eq('id', friendship_id).eq('addressee_id', current_user['id']).eq('status', 'pending').limit(1).execute().data or [None])[0]
    if not row:
        raise HTTPException(status_code=404, detail='Không tìm thấy lời mời đang chờ.')
    updated = (client.table('friendships').update({'status': 'accepted', 'accepted_at': datetime.now(ZoneInfo('Asia/Ho_Chi_Minh')).isoformat(), 'updated_at': datetime.now(ZoneInfo('Asia/Ho_Chi_Minh')).isoformat()}).eq('id', friendship_id).select('*').execute().data or [row])[0]
    try:
        notify_users(client, [row['requester_id']], 'Lời mời kết bạn đã được chấp nhận', f'{current_user.get("display_name") or current_user.get("username", "User")} đã chấp nhận lời mời của bạn.', 'friend-accepted', f'friendship:{friendship_id}')
    except Exception as error:
        print(f'⚠️ Không thể tạo notification friend accepted: {error}')
    return {'success': True, 'friendship': updated, 'message': 'Đã trở thành bạn bè.'}


@app.post('/api/friends/requests/{friendship_id}/reject')
async def reject_friend_request(friendship_id: str, client: Client = Depends(require_supabase), current_user: dict = Depends(get_current_user)) -> dict:
    row = (client.table('friendships').select('*').eq('id', friendship_id).eq('addressee_id', current_user['id']).eq('status', 'pending').limit(1).execute().data or [None])[0]
    if not row:
        raise HTTPException(status_code=404, detail='Không tìm thấy lời mời đang chờ.')
    client.table('friendships').update({'status': 'rejected', 'updated_at': datetime.now(ZoneInfo('Asia/Ho_Chi_Minh')).isoformat()}).eq('id', friendship_id).execute()
    return {'success': True, 'message': 'Đã từ chối lời mời.'}


@app.post('/api/friends/requests/{friendship_id}/cancel')
async def cancel_friend_request(friendship_id: str, client: Client = Depends(require_supabase), current_user: dict = Depends(get_current_user)) -> dict:
    row = (client.table('friendships').select('id').eq('id', friendship_id).eq('requester_id', current_user['id']).eq('status', 'pending').limit(1).execute().data or [None])[0]
    if not row:
        raise HTTPException(status_code=404, detail='Không tìm thấy lời mời do bạn gửi.')
    client.table('friendships').update({'status': 'cancelled', 'updated_at': datetime.now(ZoneInfo('Asia/Ho_Chi_Minh')).isoformat()}).eq('id', friendship_id).execute()
    return {'success': True, 'message': 'Đã hủy lời mời kết bạn.'}


@app.delete('/api/friends/{user_id}')
async def remove_friend(user_id: str, client: Client = Depends(require_supabase), current_user: dict = Depends(get_current_user)) -> dict:
    result = client.table('friendships').delete().eq('status', 'accepted').or_(f'and(requester_id.eq.{current_user["id"]},addressee_id.eq.{user_id}),and(requester_id.eq.{user_id},addressee_id.eq.{current_user["id"]})').execute()
    if not result.data:
        raise HTTPException(status_code=404, detail='Không tìm thấy quan hệ bạn bè.')
    return {'success': True, 'message': 'Đã hủy kết bạn.'}


@app.post('/api/blocks/{user_id}')
async def block_user(user_id: str, client: Client = Depends(require_supabase), current_user: dict = Depends(get_current_user)) -> dict:
    if str(user_id) == str(current_user['id']):
        raise HTTPException(status_code=400, detail='Bạn không thể tự chặn mình.')
    target = client.table('users').select('id').eq('id', user_id).limit(1).execute().data or []
    if not target:
        raise HTTPException(status_code=404, detail='Không tìm thấy user này.')
    client.table('blocks').upsert({'blocker_id': current_user['id'], 'blocked_id': user_id}, on_conflict='blocker_id,blocked_id').execute()
    client.table('friendships').delete().or_(f'and(requester_id.eq.{current_user["id"]},addressee_id.eq.{user_id}),and(requester_id.eq.{user_id},addressee_id.eq.{current_user["id"]})').execute()
    return {'success': True, 'message': 'Đã chặn user và xóa quan hệ bạn bè nếu có.'}


@app.delete('/api/blocks/{user_id}')
async def unblock_user(user_id: str, client: Client = Depends(require_supabase), current_user: dict = Depends(get_current_user)) -> dict:
    client.table('blocks').delete().eq('blocker_id', current_user['id']).eq('blocked_id', user_id).execute()
    return {'success': True, 'message': 'Đã bỏ chặn user.'}


@app.get('/api/me/privacy')
async def get_privacy_settings(client: Client = Depends(require_supabase), current_user: dict = Depends(get_current_user)) -> dict:
    try:
        row = (client.table('users').select('privacy_settings').eq('id', current_user['id']).limit(1).execute().data or [{}])[0]
        settings = row.get('privacy_settings') or {}
    except Exception:
        settings = {}
    return {'settings': {**{'allow_friend_requests': 'everyone', 'allow_direct_messages': 'friends', 'show_online_status': True, 'show_current_room': False}, **settings}}


@app.patch('/api/me/privacy')
async def update_privacy_settings(request: PrivacySettingsRequest, client: Client = Depends(require_supabase), current_user: dict = Depends(get_current_user)) -> dict:
    settings = request.model_dump()
    try:
        client.table('users').update({'privacy_settings': settings, 'updated_at': datetime.now(ZoneInfo('Asia/Ho_Chi_Minh')).isoformat()}).eq('id', current_user['id']).execute()
    except Exception as error:
        raise HTTPException(status_code=503, detail='Privacy settings chưa được bật. Admin cần chạy supabase/user_profiles.sql trước.') from error
    return {'success': True, 'settings': settings, 'message': 'Đã lưu quyền riêng tư.'}


@app.get('/api/chat/conversations')
async def list_chat_conversations(client: Client = Depends(require_supabase), current_user: dict = Depends(get_current_user)) -> dict:
    try:
        memberships = client.table('conversation_members').select('conversation_id,last_read_at').eq('user_id', current_user['id']).limit(100).execute().data or []
        conversation_ids = [row.get('conversation_id') for row in memberships if row.get('conversation_id')]
        if not conversation_ids:
            return {'items': []}
        rows = client.table('conversations').select('id,kind,room_id,direct_key,created_by,created_at,updated_at').in_('id', conversation_ids).order('updated_at', desc=True).limit(100).execute().data or []
        visible_rows = []
        for row in rows:
            try:
                assert_chat_access(client, str(row.get('id')), str(current_user['id']))
                visible_rows.append(row)
            except HTTPException as access_error:
                if access_error.status_code in {403, 404, 410}:
                    continue
                raise
        rows = visible_rows
        room_ids = [row.get('room_id') for row in rows if row.get('room_id')]
        rooms_by_id = {}
        if room_ids:
            rooms = client.table('listening_rooms').select('id,name,invite_code,status').in_('id', room_ids).limit(50).execute().data or []
            rooms_by_id = {str(row.get('id')): row for row in rooms}
        direct_user_ids = []
        for row in rows:
            if row.get('kind') == 'direct' and row.get('direct_key'):
                direct_user_ids.extend(str(value) for value in str(row['direct_key']).split(':') if value and value != str(current_user['id']))
        users_by_id = social_users_map(client, list(set(direct_user_ids))) if direct_user_ids else {}
        items = []
        for row in rows:
            item = {**row, 'room': rooms_by_id.get(str(row.get('room_id')))}
            if row.get('kind') == 'direct' and row.get('direct_key'):
                other_id = next((value for value in str(row['direct_key']).split(':') if value != str(current_user['id'])), '')
                item['other_user'] = users_by_id.get(other_id)
            items.append(item)
        return {'items': items}
    except HTTPException:
        raise
    except Exception as error:
        if any(is_missing_table_error(error, table) for table in ('conversations', 'chat_messages', 'conversation_members', 'friendships', 'blocks', 'listening_rooms', 'room_members')):
            raise HTTPException(status_code=503, detail='Tính năng chat hoặc social chưa được bật đầy đủ. Admin cần chạy các migration social, room và chat trước.') from error
        print(f'⚠️ Chat conversation list failed: {error}')
        raise HTTPException(status_code=502, detail='Không thể tải cuộc trò chuyện lúc này.') from error


@app.post('/api/chat/conversations/direct', status_code=status.HTTP_201_CREATED)
async def create_direct_chat(request: ChatTargetRequest, client: Client = Depends(require_supabase), current_user: dict = Depends(get_current_user)) -> dict:
    target_id = str(request.user_id)
    if target_id == str(current_user['id']):
        raise HTTPException(status_code=400, detail='Bạn không thể nhắn tin với chính mình.')
    target = (client.table('users').select('id,username,role,display_name,avatar_url,bio').eq('id', target_id).limit(1).execute().data or [None])[0]
    if not target:
        raise HTTPException(status_code=404, detail='Không tìm thấy user này.')
    if chat_is_blocked(client, str(current_user['id']), target_id):
        raise HTTPException(status_code=403, detail='Không thể mở chat vì một trong hai tài khoản đang chặn nhau.')
    if not chat_are_friends(client, str(current_user['id']), target_id):
        raise HTTPException(status_code=403, detail='Chỉ có thể nhắn tin trực tiếp với bạn bè đã chấp nhận.')
    privacy = chat_privacy(client, target_id)
    if privacy.get('allow_direct_messages', 'friends') == 'nobody':
        raise HTTPException(status_code=403, detail='User này hiện không nhận tin nhắn trực tiếp.')
    direct_key = ':'.join(sorted([str(current_user['id']), target_id]))
    existing = (client.table('conversations').select('*').eq('direct_key', direct_key).limit(1).execute().data or [None])[0]
    if existing:
        conversation = existing
    else:
        conversation = (client.table('conversations').insert({'kind': 'direct', 'direct_key': direct_key, 'created_by': current_user['id']}).select('*').execute().data or [None])[0]
        if not conversation:
            raise HTTPException(status_code=502, detail='Không thể tạo cuộc trò chuyện.')
    client.table('conversation_members').upsert([{'conversation_id': conversation['id'], 'user_id': current_user['id']}, {'conversation_id': conversation['id'], 'user_id': target_id}], on_conflict='conversation_id,user_id').execute()
    return {'success': True, 'conversation': conversation, 'other_user': public_user_payload(target), 'message': 'Đã mở cuộc trò chuyện.'}


@app.post('/api/chat/conversations/room/{room_id}', status_code=status.HTTP_201_CREATED)
async def create_room_chat(room_id: str, client: Client = Depends(require_supabase), current_user: dict = Depends(get_current_user)) -> dict:
    room = get_room(client, room_id)
    member = get_room_member(client, room_id, str(current_user['id']))
    if not member:
        raise HTTPException(status_code=403, detail='Bạn chưa tham gia phòng nghe này.')
    existing = (client.table('conversations').select('*').eq('room_id', room_id).limit(1).execute().data or [None])[0]
    if existing:
        conversation = existing
    else:
        conversation = (client.table('conversations').insert({'kind': 'room', 'room_id': room_id, 'created_by': room.get('host_id')}).select('*').execute().data or [None])[0]
        if not conversation:
            raise HTTPException(status_code=502, detail='Không thể tạo chat phòng.')
    members = client.table('room_members').select('user_id').eq('room_id', room_id).limit(50).execute().data or []
    rows = [{'conversation_id': conversation['id'], 'user_id': row['user_id']} for row in members if row.get('user_id')]
    if rows:
        client.table('conversation_members').upsert(rows, on_conflict='conversation_id,user_id').execute()
    return {'success': True, 'conversation': conversation, 'message': 'Đã mở chat phòng.'}


@app.get('/api/chat/conversations/{conversation_id}/messages')
async def list_chat_messages(conversation_id: str, limit: int = Query(default=100, ge=1, le=100), client: Client = Depends(require_supabase), current_user: dict = Depends(get_current_user)) -> dict:
    try:
        assert_chat_access(client, conversation_id, str(current_user['id']))
        now = datetime.now(ZoneInfo('UTC')).isoformat()
        rows = client.table('chat_messages').select('id,conversation_id,sender_id,body,created_at,expires_at,attachment_url,attachment_public_id,attachment_resource_type,attachment_name,attachment_mime,attachment_size_bytes').eq('conversation_id', conversation_id).gt('expires_at', now).is_('deleted_at', 'null').order('created_at', desc=False).limit(limit).execute().data or []
        sender_ids = list({str(row.get('sender_id')) for row in rows if row.get('sender_id')})
        users = social_users_map(client, sender_ids)
        return {'items': [chat_message_payload(row, users) for row in rows], 'expires_after_minutes': 60}
    except HTTPException:
        raise
    except Exception as error:
        if any(is_missing_table_error(error, table) for table in ('chat_messages', 'conversation_members', 'conversations', 'friendships', 'blocks', 'listening_rooms', 'room_members')):
            raise HTTPException(status_code=503, detail='Tính năng chat hoặc social chưa được bật đầy đủ. Admin cần chạy các migration social, room và chat trước.') from error
        print(f'⚠️ Chat message list failed: {error}')
        raise HTTPException(status_code=502, detail='Không thể tải tin nhắn lúc này.') from error


@app.post('/api/chat/conversations/{conversation_id}/messages', status_code=status.HTTP_201_CREATED)
async def send_chat_message(conversation_id: str, request: ChatMessageRequest, client: Client = Depends(require_supabase), current_user: dict = Depends(get_current_user)) -> dict:
    try:
        assert_chat_access(client, conversation_id, str(current_user['id']))
        enforce_chat_send_rate_limit(str(current_user['id']))
        expires_at = (datetime.now(ZoneInfo('UTC')) + timedelta(minutes=60)).isoformat()
        row = (client.table('chat_messages').insert({'conversation_id': conversation_id, 'sender_id': current_user['id'], 'body': request.body, 'expires_at': expires_at}).select('id,conversation_id,sender_id,body,created_at,expires_at').execute().data or [None])[0]
        if not row:
            raise HTTPException(status_code=502, detail='Không thể gửi tin nhắn.')
        client.table('conversations').update({'updated_at': datetime.now(ZoneInfo('Asia/Ho_Chi_Minh')).isoformat()}).eq('id', conversation_id).execute()
        message = chat_message_payload(row, {str(current_user['id']): public_user_payload(current_user)})
        await broadcast_chat_event(conversation_id, {'event': 'message_created', 'message': message})
        return {'success': True, 'message': message}
    except HTTPException:
        raise
    except Exception as error:
        if any(is_missing_table_error(error, table) for table in ('chat_messages', 'conversation_members', 'conversations', 'friendships', 'blocks', 'listening_rooms', 'room_members')):
            raise HTTPException(status_code=503, detail='Tính năng chat hoặc social chưa được bật đầy đủ. Admin cần chạy các migration social, room và chat trước.') from error
        print(f'⚠️ Chat send failed: {error}')
        raise HTTPException(status_code=502, detail='Không thể gửi tin nhắn lúc này.') from error


@app.post('/api/chat/conversations/{conversation_id}/attachments', status_code=status.HTTP_201_CREATED)
async def send_chat_attachment(conversation_id: str, file: UploadFile = File(...), body: str = Form(default=''), client: Client = Depends(require_supabase), current_user: dict = Depends(get_current_user)) -> dict:
    assert_chat_access(client, conversation_id, str(current_user['id']))
    enforce_chat_send_rate_limit(str(current_user['id']))
    caption = (body or '').strip()
    if len(caption) > 2000:
        raise HTTPException(status_code=422, detail='Chú thích tệp không được vượt quá 2000 ký tự.')
    temp_path = None
    uploaded = None
    attachment_public_id = ''
    resource_type = 'raw'
    try:
        temp_path, filename, mime, size, kind = await read_chat_upload(file)
        resource_type = 'image' if kind == 'image' else 'raw'
        extension = Path(filename).suffix.lower() if resource_type == 'raw' else ''
        public_id = f'lunu_chat/{conversation_id}/{uuid.uuid4().hex}{extension}'
        uploaded = await asyncio.to_thread(upload_chat_attachment, temp_path, public_id, resource_type)
        secure_url = uploaded.get('secure_url') or uploaded.get('url')
        attachment_public_id = uploaded.get('public_id') or public_id
        if not secure_url:
            raise RuntimeError('Cloudinary không trả về URL attachment.')
        expires_at = (datetime.now(ZoneInfo('UTC')) + timedelta(minutes=60)).isoformat()
        row = (client.table('chat_messages').insert({
            'conversation_id': conversation_id,
            'sender_id': current_user['id'],
            'body': caption or filename,
            'expires_at': expires_at,
            'attachment_url': secure_url,
            'attachment_public_id': attachment_public_id,
            'attachment_resource_type': resource_type,
            'attachment_name': filename,
            'attachment_mime': mime,
            'attachment_size_bytes': size,
        }).select('id,conversation_id,sender_id,body,created_at,expires_at,attachment_url,attachment_public_id,attachment_resource_type,attachment_name,attachment_mime,attachment_size_bytes').execute().data or [None])[0]
        if not row:
            raise RuntimeError('Supabase không trả về attachment message.')
        client.table('conversations').update({'updated_at': datetime.now(ZoneInfo('Asia/Ho_Chi_Minh')).isoformat()}).eq('id', conversation_id).execute()
        message = chat_message_payload(row, {str(current_user['id']): public_user_payload(current_user)})
        await broadcast_chat_event(conversation_id, {'event': 'message_created', 'message': message})
        return {'success': True, 'message': message}
    except HTTPException:
        if attachment_public_id:
            try:
                await asyncio.to_thread(delete_chat_attachment, attachment_public_id, resource_type)
            except Exception as cleanup_error:
                print(f'⚠️ Không thể rollback attachment chat: {cleanup_error}')
        raise
    except Exception as error:
        if attachment_public_id:
            try:
                await asyncio.to_thread(delete_chat_attachment, attachment_public_id, resource_type)
            except Exception as cleanup_error:
                print(f'⚠️ Không thể rollback attachment chat: {cleanup_error}')
        print(f'⚠️ Chat attachment send failed: {error}')
        if any(is_missing_table_error(error, table) for table in ('chat_messages', 'conversations', 'conversation_members')):
            raise HTTPException(status_code=503, detail='Chat attachment chưa được bật. Admin cần chạy supabase/chat_messages.sql và supabase/chat_attachments.sql.') from error
        raise HTTPException(status_code=502, detail='Không thể gửi tệp chat lúc này.') from error
    finally:
        if temp_path:
            temp_path.unlink(missing_ok=True)


@app.delete('/api/chat/messages/{message_id}')
async def delete_chat_message(message_id: str, client: Client = Depends(require_supabase), current_user: dict = Depends(get_current_user)) -> dict:
    try:
        row = (client.table('chat_messages').select('id,conversation_id,sender_id,attachment_public_id,attachment_resource_type').eq('id', message_id).limit(1).execute().data or [None])[0]
        if not row:
            raise HTTPException(status_code=404, detail='Không tìm thấy tin nhắn.')
        assert_chat_access(client, str(row['conversation_id']), str(current_user['id']))
        if str(row.get('sender_id')) != str(current_user['id']) and current_user.get('role') != 'admin':
            raise HTTPException(status_code=403, detail='Bạn không có quyền xóa tin nhắn này.')
        if row.get('attachment_public_id'):
            await asyncio.to_thread(delete_chat_attachment, row['attachment_public_id'], row.get('attachment_resource_type') or 'raw')
        client.table('chat_messages').delete().eq('id', message_id).execute()
        await broadcast_chat_event(row['conversation_id'], {'event': 'message_deleted', 'message_id': message_id})
        return {'success': True, 'message': 'Đã xóa tin nhắn cho mọi người.'}
    except HTTPException:
        raise
    except Exception as error:
        if any(is_missing_table_error(error, table) for table in ('chat_messages', 'conversation_members', 'conversations', 'friendships', 'blocks', 'listening_rooms', 'room_members')):
            raise HTTPException(status_code=503, detail='Tính năng chat hoặc social chưa được bật đầy đủ. Admin cần chạy các migration social, room và chat trước.') from error
        print(f'⚠️ Chat delete failed: {error}')
        raise HTTPException(status_code=502, detail='Không thể xóa tin nhắn lúc này.') from error


@app.post('/api/chat/messages/{message_id}/report', status_code=status.HTTP_201_CREATED)
async def report_chat_message(message_id: str, request: ChatReportRequest, client: Client = Depends(require_supabase), current_user: dict = Depends(get_current_user)) -> dict:
    row = (client.table('chat_messages').select('id,conversation_id').eq('id', message_id).limit(1).execute().data or [None])[0]
    if not row:
        raise HTTPException(status_code=404, detail='Không tìm thấy tin nhắn trong cuộc trò chuyện của bạn.')
    assert_chat_access(client, str(row['conversation_id']), str(current_user['id']))
    try:
        client.table('chat_reports').insert({'message_id': message_id, 'reporter_id': current_user['id'], 'reason': request.reason}).execute()
    except Exception as error:
        if 'duplicate' in str(error).lower() or 'unique' in str(error).lower():
            raise HTTPException(status_code=409, detail='Bạn đã report tin nhắn này rồi.') from error
        print(f'⚠️ Chat report failed: {error}')
        raise HTTPException(status_code=502, detail='Không thể report tin nhắn lúc này.') from error
    return {'success': True, 'message': 'Đã gửi report cho moderator.'}


@app.delete('/api/chat/cleanup')
async def cleanup_chat_messages(client: Client = Depends(require_supabase), _: dict = Depends(require_admin)) -> dict:
    try:
        deleted = await asyncio.to_thread(cleanup_expired_chat_messages, client)
        return {'success': True, 'deleted_count': deleted, 'message': f'Đã xóa {deleted} tin nhắn hết hạn.'}
    except Exception as error:
        print(f'⚠️ Chat cleanup failed: {error}')
        raise HTTPException(status_code=502, detail='Không thể cleanup chat lúc này.') from error


@app.websocket('/api/chat/ws')
async def chat_websocket(websocket: WebSocket):
    conversation_id = str(websocket.query_params.get('conversation_id') or '')
    origin = (websocket.headers.get('origin') or '').rstrip('/')
    connection = websocket
    if origin and origin not in allowed_origins:
        await websocket.close(code=4403)
        return
    if not conversation_id:
        await websocket.close(code=4400)
        return
    await websocket.accept()
    try:
        auth_text = await asyncio.wait_for(websocket.receive_text(), timeout=10)
        auth_packet = json.loads(auth_text)
        token = str(auth_packet.get('token') or '') if isinstance(auth_packet, dict) else ''
        try:
            payload = decode_token(token)
        except Exception:
            await websocket.close(code=4403)
            return
        client = require_supabase()
        user_row = (client.table('users').select('id,username,role,display_name,avatar_url,bio').eq('id', payload.get('sub')).limit(1).execute().data or [None])[0]
        if not user_row:
            await websocket.close(code=4403)
            return
        assert_chat_access(client, conversation_id, str(user_row['id']))
        chat_connections.setdefault(conversation_id, set()).add(connection)
        chat_connection_users[connection] = str(user_row['id'])
        await websocket.send_json({'event': 'ready', 'conversation_id': conversation_id})
        while True:
            try:
                packet = await asyncio.wait_for(websocket.receive_text(), timeout=35)
            except asyncio.TimeoutError:
                assert_chat_access(client, conversation_id, str(user_row['id']))
                await websocket.send_json({'event': 'ping'})
                continue
            if packet == 'ping' or packet == '{"type":"ping"}':
                await websocket.send_json({'event': 'pong'})
            elif packet == 'pong' or packet == '{"type":"pong"}':
                continue
    except WebSocketDisconnect:
        pass
    except HTTPException:
        try:
            await websocket.close(code=4403)
        except Exception:
            pass
    except Exception:
        try:
            await websocket.close(code=1011)
        except Exception:
            pass
    finally:
        chat_connections.get(conversation_id, set()).discard(connection)
        chat_connection_users.pop(connection, None)


@app.get('/api/rooms')
async def list_listening_rooms(client: Client = Depends(require_supabase), current_user: dict = Depends(get_current_user)) -> list:
    try:
        memberships = client.table('room_members').select('room_id').eq('user_id', current_user['id']).limit(50).execute().data or []
        member_room_ids = {str(row.get('room_id')) for row in memberships if row.get('room_id')}
        rooms = client.table('listening_rooms').select('*').eq('status', 'active').order('updated_at', desc=True).limit(50).execute().data or []
        visible = [room for room in rooms if room.get('visibility') == 'public' or str(room.get('id')) in member_room_ids]
        return [room_snapshot(client, room) for room in visible]
    except Exception as error:
        raise HTTPException(status_code=503, detail='Listening Room chưa được bật. Admin cần chạy supabase/listening_rooms.sql trước.') from error


@app.post('/api/rooms', status_code=status.HTTP_201_CREATED)
async def create_listening_room(request: CreateRoomRequest, client: Client = Depends(require_supabase), current_user: dict = Depends(get_current_user)) -> dict:
    try:
        invite_code = ''
        for _ in range(5):
            candidate = make_invite_code()
            duplicate = client.table('listening_rooms').select('id').eq('invite_code', candidate).limit(1).execute().data or []
            if not duplicate:
                invite_code = candidate
                break
        if not invite_code:
            raise RuntimeError('Không thể tạo mã mời duy nhất.')
        inserted = client.table('listening_rooms').insert({
            'name': request.name, 'invite_code': invite_code, 'host_id': current_user['id'],
            'visibility': request.visibility, 'max_members': request.max_members,
        }).select('*').execute()
        room = (inserted.data or [None])[0]
        if not room:
            raise RuntimeError('Supabase không trả về phòng vừa tạo.')
        client.table('room_members').insert({'room_id': room['id'], 'user_id': current_user['id'], 'role': 'host'}).execute()
        return {'success': True, 'room': room_snapshot(client, room), 'message': f'Đã tạo phòng “{request.name}”.'}
    except HTTPException:
        raise
    except Exception as error:
        raise HTTPException(status_code=503, detail=f'Không thể tạo phòng nghe: {error}') from error


@app.post('/api/rooms/join')
async def join_listening_room(request: JoinRoomRequest, client: Client = Depends(require_supabase), current_user: dict = Depends(get_current_user)) -> dict:
    try:
        response = client.table('listening_rooms').select('*').eq('invite_code', request.invite_code).eq('status', 'active').limit(1).execute()
        room = (response.data or [None])[0]
        if not room:
            raise HTTPException(status_code=404, detail='Mã mời không hợp lệ hoặc phòng đã đóng.')
        member = get_room_member(client, room['id'], str(current_user['id']))
        if not member:
            members = client.table('room_members').select('id').eq('room_id', room['id']).limit(51).execute().data or []
            if len(members) >= int(room.get('max_members') or 8):
                raise HTTPException(status_code=409, detail='Phòng đã đủ số thành viên.')
            client.table('room_members').insert({'room_id': room['id'], 'user_id': current_user['id'], 'role': 'member'}).execute()
        else:
            client.table('room_members').update({'last_seen_at': datetime.now(ZoneInfo('Asia/Ho_Chi_Minh')).isoformat()}).eq('id', member['id']).execute()
        return {'success': True, 'room': room_snapshot(client, room), 'message': f'Đã vào phòng “{room.get("name", "") }”.'}
    except HTTPException:
        raise
    except Exception as error:
        raise HTTPException(status_code=503, detail=f'Không thể vào phòng nghe: {error}') from error


@app.get('/api/rooms/{room_id}')
async def get_listening_room(room_id: str, client: Client = Depends(require_supabase), current_user: dict = Depends(get_current_user)) -> dict:
    room = get_room(client, room_id)
    member = get_room_member(client, room_id, str(current_user['id']))
    if not member:
        raise HTTPException(status_code=403, detail='Bạn chưa tham gia phòng nghe này.')
    client.table('room_members').update({'last_seen_at': datetime.now(ZoneInfo('Asia/Ho_Chi_Minh')).isoformat()}).eq('id', member['id']).execute()
    return room_snapshot(client, room)


@app.patch('/api/rooms/{room_id}/state')
async def update_listening_room_state(room_id: str, request: RoomStateRequest, client: Client = Depends(require_supabase), current_user: dict = Depends(get_current_user)) -> dict:
    room = get_room(client, room_id)
    member = get_room_member(client, room_id, str(current_user['id']))
    if not member:
        raise HTTPException(status_code=403, detail='Bạn chưa tham gia phòng nghe này.')
    if member.get('role') not in {'host', 'co_host'}:
        raise HTTPException(status_code=403, detail='Chỉ host hoặc co-host được điều khiển phòng.')
    current_song = normalize_room_media(request.current_song)
    queue = [item for item in (normalize_room_media(item) for item in request.queue) if item]
    next_version = int(room.get('state_version') or 0) + 1
    payload = {'current_song': current_song, 'queue': queue, 'is_playing': request.is_playing, 'position_seconds': request.position_seconds, 'state_version': next_version, 'updated_at': datetime.now(ZoneInfo('Asia/Ho_Chi_Minh')).isoformat()}
    query = client.table('listening_rooms').update(payload).eq('id', room_id).eq('status', 'active')
    if request.expected_version is not None:
        query = query.eq('state_version', request.expected_version)
    updated = query.select('*').execute().data or []
    if not updated:
        raise HTTPException(status_code=409, detail='Trạng thái phòng vừa thay đổi. Hãy đồng bộ lại trước khi điều khiển tiếp.')
    return {'success': True, 'room': room_snapshot(client, updated[0]), 'message': 'Đã đồng bộ trạng thái phòng.'}


@app.patch('/api/rooms/{room_id}')
async def update_listening_room(room_id: str, request: RoomSettingsRequest, client: Client = Depends(require_supabase), current_user: dict = Depends(get_current_user)) -> dict:
    room = get_room(client, room_id)
    if str(room.get('host_id')) != str(current_user['id']):
        raise HTTPException(status_code=403, detail='Chỉ host được chỉnh cài đặt phòng.')
    updated = client.table('listening_rooms').update({'name': request.name, 'visibility': request.visibility, 'max_members': request.max_members, 'updated_at': datetime.now(ZoneInfo('Asia/Ho_Chi_Minh')).isoformat()}).eq('id', room_id).select('*').execute().data or []
    if not updated:
        raise HTTPException(status_code=404, detail='Không tìm thấy phòng nghe.')
    return {'success': True, 'room': room_snapshot(client, updated[0]), 'message': 'Đã cập nhật cài đặt phòng.'}


@app.post('/api/rooms/{room_id}/leave')
async def leave_listening_room(room_id: str, client: Client = Depends(require_supabase), current_user: dict = Depends(get_current_user)) -> dict:
    room = get_room(client, room_id)
    member = get_room_member(client, room_id, str(current_user['id']))
    if not member:
        raise HTTPException(status_code=403, detail='Bạn chưa tham gia phòng nghe này.')
    client.table('room_members').delete().eq('id', member['id']).execute()
    if str(room.get('host_id')) == str(current_user['id']):
        remaining = client.table('room_members').select('id,user_id').eq('room_id', room_id).order('joined_at').limit(1).execute().data or []
        if remaining:
            next_host = remaining[0]
            client.table('room_members').update({'role': 'host'}).eq('id', next_host['id']).execute()
            client.table('listening_rooms').update({'host_id': next_host['user_id'], 'updated_at': datetime.now(ZoneInfo('Asia/Ho_Chi_Minh')).isoformat()}).eq('id', room_id).execute()
        else:
            client.table('listening_rooms').update({'status': 'closed', 'updated_at': datetime.now(ZoneInfo('Asia/Ho_Chi_Minh')).isoformat()}).eq('id', room_id).execute()
    return {'success': True, 'message': 'Đã rời phòng nghe.'}


@app.post('/api/rooms/{room_id}/close')
async def close_listening_room(room_id: str, client: Client = Depends(require_supabase), current_user: dict = Depends(get_current_user)) -> dict:
    room = get_room(client, room_id)
    if str(room.get('host_id')) != str(current_user['id']) and current_user.get('role') != 'admin':
        raise HTTPException(status_code=403, detail='Chỉ host hoặc admin được đóng phòng.')
    client.table('listening_rooms').update({'status': 'closed', 'updated_at': datetime.now(ZoneInfo('Asia/Ho_Chi_Minh')).isoformat()}).eq('id', room_id).execute()
    return {'success': True, 'message': 'Đã đóng phòng nghe.'}


@app.post('/api/media-proposals', status_code=status.HTTP_201_CREATED)
async def create_media_proposal(request: MediaProposalRequest, client: Client = Depends(require_supabase), current_user: dict = Depends(get_current_user)) -> dict:
    if request.kind == 'song' and not request.artist:
        raise HTTPException(status_code=422, detail='Bài hát cần có tên ca sĩ trước khi gửi duyệt.')
    try:
        duplicate = client.table('media_proposals').select('id,status').eq('source_id', request.source_id).in_('status', ['pending', 'processing']).limit(1).execute()
        if duplicate.data:
            raise HTTPException(status_code=409, detail='Media này đã có một đề xuất đang chờ xử lý.')
        payload = {
            'kind': request.kind, 'source_id': request.source_id, 'title': request.title,
            'artist': request.artist, 'uploader': request.uploader or 'YouTube',
            'cover': request.cover, 'description': request.description,
            'requested_by': current_user['id'], 'requested_by_username': current_user.get('username', 'user'),
            'status': 'pending',
        }
        inserted = client.table('media_proposals').insert(payload).select('*').execute()
        proposal = (inserted.data or [None])[0]
        if not proposal:
            raise HTTPException(status_code=502, detail='Supabase không trả về proposal vừa tạo.')
        admins = client.table('users').select('id').eq('role', 'admin').limit(100).execute().data or []
        media_label = 'bài hát' if request.kind == 'song' else 'video'
        notify_users(client, [row.get('id') for row in admins], 'Có đề xuất media mới', f'{current_user.get("username", "Một user")} muốn thêm {media_label} “{request.title}”.', 'proposal-new', f'proposal:{proposal["id"]}')
        return {'success': True, 'proposal': proposal, 'message': 'Đã gửi đề xuất. Admin sẽ xem xét trước khi hệ thống tải media.'}
    except HTTPException:
        raise
    except Exception as error:
        if is_missing_table_error(error, 'media_proposals'):
            raise HTTPException(status_code=503, detail='Tính năng đề xuất chưa được bật. Admin cần chạy supabase/media_requests_notifications.sql trước.') from error
        raise HTTPException(status_code=502, detail=f'Không thể gửi đề xuất media: {error}')


@app.get('/api/media-proposals/mine')
async def get_my_media_proposals(client: Client = Depends(require_supabase), current_user: dict = Depends(get_current_user)) -> list:
    try:
        response = client.table('media_proposals').select('*').eq('requested_by', current_user['id']).order('created_at', desc=True).limit(100).execute()
        return response.data or []
    except Exception as error:
        if is_missing_table_error(error, 'media_proposals'):
            return []
        raise HTTPException(status_code=502, detail=f'Không thể tải đề xuất của bạn: {error}')


@app.get('/api/media-proposals')
async def get_media_proposals(status_filter: Optional[str] = Query(default=None, alias='status'), client: Client = Depends(require_supabase), _: dict = Depends(require_admin)) -> list:
    try:
        query = client.table('media_proposals').select('*').order('created_at', desc=True).limit(100)
        if status_filter in {'pending', 'processing', 'approved', 'rejected', 'failed'}:
            query = query.eq('status', status_filter)
        return query.execute().data or []
    except Exception as error:
        if is_missing_table_error(error, 'media_proposals'):
            return []
        raise HTTPException(status_code=502, detail=f'Không thể tải danh sách đề xuất: {error}')


@app.delete('/api/media-proposals/cleanup')
async def cleanup_media_proposals(before_days: int = Query(default=30, ge=1, le=3650), client: Client = Depends(require_supabase), _: dict = Depends(require_admin)) -> dict:
    cutoff = (datetime.now(ZoneInfo('Asia/Ho_Chi_Minh')) - timedelta(days=before_days)).isoformat()
    try:
        response = client.table('media_proposals').delete().in_('status', ['rejected', 'failed']).lt('created_at', cutoff).execute()
        return {'success': True, 'deleted_count': len(response.data or []), 'message': f'Đã dọn các đề xuất lỗi/từ chối cũ hơn {before_days} ngày.'}
    except Exception as error:
        if is_missing_table_error(error, 'media_proposals'):
            return {'success': True, 'deleted_count': 0, 'available': False, 'message': 'Bảng đề xuất chưa được tạo.'}
        raise HTTPException(status_code=502, detail=f'Không thể dọn đề xuất: {error}')


@app.delete('/api/media-proposals/{proposal_id}')
async def delete_media_proposal(proposal_id: str, client: Client = Depends(require_supabase), current_user: dict = Depends(get_current_user)) -> dict:
    try:
        response = client.table('media_proposals').select('id,requested_by,status').eq('id', proposal_id).limit(1).execute()
        proposal = (response.data or [None])[0]
        if not proposal:
            raise HTTPException(status_code=404, detail='Không tìm thấy đề xuất media.')
        if proposal.get('status') == 'processing':
            raise HTTPException(status_code=409, detail='Không thể xóa đề xuất đang được xử lý.')
        if current_user.get('role') != 'admin' and str(proposal.get('requested_by')) != str(current_user.get('id')):
            raise HTTPException(status_code=403, detail='Bạn không có quyền xóa đề xuất này.')
        client.table('media_proposals').delete().eq('id', proposal_id).execute()
        return {'success': True, 'message': 'Đã xóa đề xuất. Media đã được duyệt không bị xóa khỏi kho.'}
    except HTTPException:
        raise
    except Exception as error:
        if is_missing_table_error(error, 'media_proposals'):
            return {'success': True, 'deleted_count': 0, 'available': False, 'message': 'Bảng đề xuất chưa được tạo.'}
        raise HTTPException(status_code=502, detail=f'Không thể xóa đề xuất: {error}')


@app.post('/api/media-proposals/{proposal_id}/approve', status_code=status.HTTP_202_ACCEPTED)
async def approve_media_proposal(proposal_id: str, background_tasks: BackgroundTasks, client: Client = Depends(require_supabase), reviewer: dict = Depends(require_admin)) -> dict:
    try:
        response = client.table('media_proposals').select('*').eq('id', proposal_id).limit(1).execute()
        proposal = (response.data or [None])[0]
        if not proposal:
            raise HTTPException(status_code=404, detail='Không tìm thấy đề xuất media.')
        if proposal.get('status') != 'pending':
            raise HTTPException(status_code=409, detail='Đề xuất này đã được xử lý trước đó.')
        if proposal.get('kind') == 'song' and not proposal.get('artist'):
            raise HTTPException(status_code=422, detail='Bổ sung ca sĩ trước khi duyệt bài hát.')
        job_id = str(uuid.uuid4())
        client.table('media_proposals').update({'status': 'processing', 'job_id': job_id, 'reviewed_by': reviewer['id'], 'reviewed_at': datetime.now(ZoneInfo('Asia/Ho_Chi_Minh')).isoformat()}).eq('id', proposal_id).execute()
        request_data = {
            'video_id': proposal['source_id'], 'title': proposal['title'], 'artist': proposal.get('artist', ''),
            'uploader': proposal.get('uploader') or 'YouTube', 'cover': proposal.get('cover', ''),
            'description': proposal.get('description', ''), 'proposal_id': proposal_id,
            'requested_by': proposal.get('requested_by'), 'proposal': proposal,
        }
        kind = proposal.get('kind')
        import_jobs[job_id] = {'job_id': job_id, 'kind': f'proposal-{kind}', 'proposal_id': proposal_id, 'status': 'queued', 'message': 'Đã duyệt đề xuất. Đang xếp hàng tải media.'}
        background_tasks.add_task(process_and_upload_song if kind == 'song' else process_and_upload_video, job_id, request_data)
        return {'success': True, 'job_id': job_id, 'proposal_id': proposal_id, 'message': 'Đã duyệt. Hệ thống bắt đầu tải và upload media.'}
    except HTTPException:
        raise
    except Exception as error:
        raise HTTPException(status_code=502, detail=f'Không thể duyệt đề xuất: {error}')


@app.post('/api/media-proposals/{proposal_id}/reject')
async def reject_media_proposal(proposal_id: str, decision: ProposalDecision, client: Client = Depends(require_supabase), reviewer: dict = Depends(require_admin)) -> dict:
    try:
        response = client.table('media_proposals').select('*').eq('id', proposal_id).limit(1).execute()
        proposal = (response.data or [None])[0]
        if not proposal:
            raise HTTPException(status_code=404, detail='Không tìm thấy đề xuất media.')
        if proposal.get('status') != 'pending':
            raise HTTPException(status_code=409, detail='Đề xuất này đã được xử lý trước đó.')
        reason = decision.reason.strip() or 'Admin chưa phê duyệt đề xuất này.'
        client.table('media_proposals').update({'status': 'rejected', 'reviewed_by': reviewer['id'], 'reviewed_at': datetime.now(ZoneInfo('Asia/Ho_Chi_Minh')).isoformat(), 'rejection_reason': reason}).eq('id', proposal_id).execute()
        notify_proposal_status(client, proposal, 'Đề xuất media đã được xử lý', f'Đề xuất “{proposal.get("title", "")}" chưa được duyệt. Lý do: {reason}', 'proposal-rejected')
        return {'success': True, 'message': 'Đã từ chối đề xuất và gửi thông báo cho user.'}
    except HTTPException:
        raise
    except Exception as error:
        raise HTTPException(status_code=502, detail=f'Không thể từ chối đề xuất: {error}')


@app.get('/api/notifications')
async def get_notifications(client: Client = Depends(require_supabase), current_user: dict = Depends(get_current_user)) -> dict:
    try:
        rows = client.table('notifications').select('id,title,body,kind,link,is_read,created_at').eq('user_id', current_user['id']).order('created_at', desc=True).limit(50).execute().data or []
        return {'items': rows, 'unread_count': sum(1 for row in rows if not row.get('is_read'))}
    except Exception as error:
        if is_missing_table_error(error, 'notifications'):
            return {'items': [], 'unread_count': 0, 'available': False}
        raise HTTPException(status_code=502, detail=f'Không thể tải thông báo: {error}')


@app.delete('/api/notifications/cleanup')
async def cleanup_notifications(before_days: int = Query(default=30, ge=1, le=3650), client: Client = Depends(require_supabase), _: dict = Depends(require_admin)) -> dict:
    cutoff = (datetime.now(ZoneInfo('Asia/Ho_Chi_Minh')) - timedelta(days=before_days)).isoformat()
    try:
        response = client.table('notifications').delete().eq('is_read', True).lt('created_at', cutoff).execute()
        return {'success': True, 'deleted_count': len(response.data or []), 'message': f'Đã dọn thông báo đã đọc cũ hơn {before_days} ngày.'}
    except Exception as error:
        if is_missing_table_error(error, 'notifications'):
            return {'success': True, 'deleted_count': 0, 'available': False, 'message': 'Bảng thông báo chưa được tạo.'}
        raise HTTPException(status_code=502, detail=f'Không thể dọn thông báo: {error}')


@app.delete('/api/notifications/clear-read')
async def clear_read_notifications(client: Client = Depends(require_supabase), current_user: dict = Depends(get_current_user)) -> dict:
    try:
        response = client.table('notifications').delete().eq('user_id', current_user['id']).eq('is_read', True).execute()
        return {'success': True, 'deleted_count': len(response.data or [])}
    except Exception as error:
        if is_missing_table_error(error, 'notifications'):
            return {'success': True, 'deleted_count': 0, 'available': False}
        raise HTTPException(status_code=502, detail=f'Không thể xóa thông báo đã đọc: {error}')


@app.delete('/api/notifications/{notification_id}')
async def delete_notification(notification_id: str, client: Client = Depends(require_supabase), current_user: dict = Depends(get_current_user)) -> dict:
    try:
        client.table('notifications').delete().eq('id', notification_id).eq('user_id', current_user['id']).execute()
        return {'success': True}
    except Exception as error:
        if is_missing_table_error(error, 'notifications'):
            return {'success': True, 'deleted_count': 0, 'available': False}
        raise HTTPException(status_code=502, detail=f'Không thể xóa thông báo: {error}')


@app.patch('/api/notifications/{notification_id}/read')
async def mark_notification_read(notification_id: str, client: Client = Depends(require_supabase), current_user: dict = Depends(get_current_user)) -> dict:
    try:
        client.table('notifications').update({'is_read': True}).eq('id', notification_id).eq('user_id', current_user['id']).execute()
        return {'success': True}
    except Exception as error:
        raise HTTPException(status_code=502, detail=f'Không thể cập nhật thông báo: {error}')


@app.patch('/api/notifications/read-all')
async def mark_all_notifications_read(client: Client = Depends(require_supabase), current_user: dict = Depends(get_current_user)) -> dict:
    try:
        client.table('notifications').update({'is_read': True}).eq('user_id', current_user['id']).execute()
        return {'success': True}
    except Exception as error:
        raise HTTPException(status_code=502, detail=f'Không thể đánh dấu thông báo: {error}')


@app.get('/api/songs')
async def get_songs(client: Client = Depends(require_supabase)) -> list:
    try:
        response = client.table('songs').select('*').order('title').execute()
        return response.data or []
    except Exception as error:
        raise HTTPException(status_code=502, detail=f'Không thể tải thư viện nhạc: {error}')


@app.get('/api/songs/{song_id}/lyrics/search')
async def search_song_lyrics(song_id: str, client: Client = Depends(require_supabase), _: dict = Depends(require_admin)) -> dict:
    try:
        response = client.table('songs').select('id,title,artist').eq('id', song_id).limit(1).execute()
        song = (response.data or [None])[0]
        if not song:
            raise HTTPException(status_code=404, detail='Không tìm thấy bài hát trong Supabase.')
        title = str(song.get('title') or '').strip()
        artist = str(song.get('artist') or '').strip()
        if not title or not artist:
            raise HTTPException(status_code=422, detail='Bài hát cần có cả tên bài và nghệ sĩ trước khi tìm lyrics.')
        try:
            results = search_lrclib(title, artist)
        except RuntimeError as error:
            raise HTTPException(status_code=502, detail=str(error)) from error
        return {
            'success': True,
            'song': {'id': song_id, 'title': title, 'artist': artist},
            'provider': 'LRCLIB',
            'results': results,
            'message': 'Không tìm thấy lyrics phù hợp.' if not results else f'Tìm thấy {len(results)} kết quả; hãy kiểm tra trước khi lưu.',
        }
    except HTTPException:
        raise
    except Exception as error:
        raise HTTPException(status_code=502, detail=f'Không thể tìm lyrics: {error}') from error


def load_legacy_catalog() -> list[dict]:
    catalog_path = Path(__file__).with_name('legacy_catalog.json')
    if not catalog_path.exists():
        raise HTTPException(status_code=503, detail='Chưa có file catalog legacy trên server.')
    try:
        catalog = json.loads(catalog_path.read_text(encoding='utf-8'))
    except (OSError, json.JSONDecodeError) as error:
        raise HTTPException(status_code=500, detail=f'Không đọc được catalog legacy: {error}')
    if not isinstance(catalog, list) or len(catalog) != 188:
        raise HTTPException(status_code=500, detail='Catalog legacy phải có đúng 188 bài hát.')
    return catalog


@app.post('/api/songs/import-legacy')
async def import_legacy_songs(client: Client = Depends(require_supabase), _: dict = Depends(require_admin)) -> dict:
    catalog = load_legacy_catalog()
    try:
        existing_response = client.table('songs').select('url').execute()
        existing_urls = {str(row.get('url')) for row in (existing_response.data or []) if row.get('url')}
        pending = [strip_legacy_song_fields(song) for song in catalog if song.get('url') not in existing_urls]
        if pending:
            try:
                client.table('songs').insert(pending).execute()
            except Exception as uuid_column_error:
                print('⚠️ Không insert được id UUID; thử để Supabase tự sinh id:', uuid_column_error)
                client.table('songs').insert([{key: value for key, value in song.items() if key != 'id'} for song in pending]).execute()
        return {'success': True, 'imported': len(pending), 'skipped': len(catalog) - len(pending), 'total': len(catalog), 'message': f'Đã khôi phục {len(pending)} bài, bỏ qua {len(catalog) - len(pending)} bài đã có.'}
    except Exception as error:
        raise HTTPException(status_code=502, detail=f'Không thể import catalog vào Supabase: {error}')


@app.get('/api/songs/search_youtube')
async def search_youtube(query: str = Query(min_length=2, max_length=120)) -> dict:
    normalized_query = query.strip()
    errors = []
    variants = search_query_variants(normalized_query)
    best_results = []
    try:
        api_results = rank_search_results(search_youtube_data_api(normalized_query), normalized_query)
        if api_results:
            return {'success': True, 'results': api_results[:10], 'source': 'youtube-data-api'}
    except Exception as error:
        errors.append(f'youtube-data-api: {error}')
    for client in (['android', 'web'], ['web'], ['tv']):
        client_results = []
        for variant in variants:
            try:
                options = get_ydl_opts(False)
                options['extractor_args'] = {'youtube': {'player_client': client}}
                with yt_dlp.YoutubeDL(options) as ydl:
                    info = ydl.extract_info(f'ytsearch10:{variant}', download=False)
                client_results.extend(normalize_search_entries(info.get('entries') or []))
            except Exception as error:
                errors.append(f'yt-dlp {client}/{variant}: {error}')
        ranked = rank_search_results(client_results, normalized_query)
        if ranked:
            best_results = ranked
            if has_relevant_result(ranked, normalized_query):
                return {'success': True, 'results': ranked[:10], 'source': f'yt-dlp:{",".join(client)}'}
    try:
        music_results = []
        for variant_index, variant in enumerate(music_search_query_variants(normalized_query)):
            attempts = 3 if variant_index < 3 else 1
            for _ in range(attempts):
                music_results.extend(search_youtube_music(variant))
                ranked = rank_search_results(music_results, normalized_query)
                if ranked and has_relevant_result(ranked, normalized_query):
                    return {'success': True, 'results': ranked[:10], 'source': 'youtube-music'}
        ranked = rank_search_results(music_results, normalized_query)
        if ranked:
            best_results = ranked
    except Exception as error:
        errors.append(f'youtube-music: {error}')
    try:
        internal_results = []
        for variant_index, variant in enumerate(variants):
            attempts = 3 if variant_index == 0 else 1
            for _ in range(attempts):
                internal_results.extend(search_youtube_internal(variant))
        ranked = rank_search_results(internal_results, normalized_query)
        if ranked:
            best_results = ranked
            if has_relevant_result(ranked, normalized_query):
                return {'success': True, 'results': ranked[:10], 'source': 'youtube-internal'}
    except Exception as error:
        errors.append(f'youtube-internal: {error}')
    try:
        html_results = []
        for variant in variants:
            html_results.extend(search_youtube_html(variant))
        ranked = rank_search_results(html_results, normalized_query)
        if ranked:
            best_results = ranked
            if has_relevant_result(ranked, normalized_query):
                return {'success': True, 'results': ranked[:10], 'source': 'youtube-html'}
    except Exception as error:
        errors.append(f'youtube-html: {error}')
    if best_results:
        return {'success': True, 'results': best_results[:10], 'source': 'youtube-fallback'}
    print(f'❌ Không có kết quả YouTube cho {normalized_query!r}: {" | ".join(errors[-3:])}')
    return {'success': False, 'results': [], 'message': 'YouTube không trả kết quả ổn định. Hãy thêm YOUTUBE_API_KEY trên Render hoặc thử thêm tên ca sĩ vào từ khóa.'}


@app.post('/api/songs/add', status_code=status.HTTP_202_ACCEPTED)
async def add_song(request: AddSongRequest, background_tasks: BackgroundTasks, _: dict = Depends(require_admin)) -> dict:
    job_id = str(uuid.uuid4())
    import_jobs[job_id] = {'job_id': job_id, 'status': 'queued', 'message': 'Đã nhận yêu cầu import.'}
    background_tasks.add_task(process_and_upload_song, job_id, request.model_dump())
    return {'success': True, 'job_id': job_id, 'status': 'queued', 'message': 'Đã nhận video. Bắt đầu tải MP3 và upload Cloudinary.'}


@app.get('/api/songs/import-jobs/{job_id}')
async def get_import_job(job_id: str, _: dict = Depends(require_admin)) -> dict:
    job = import_jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail='Không tìm thấy job import hoặc job đã hết hạn.')
    return {'success': True, **job}


@app.patch('/api/songs/lyrics/bulk')
async def update_song_lyrics_bulk(request: BulkLyricsRequest, client: Client = Depends(require_supabase), _: dict = Depends(require_admin)) -> dict:
    updated = []
    failed = []
    seen_ids = set()
    for item in request.items:
        if item.id in seen_ids:
            failed.append({'id': item.id, 'message': 'ID bị lặp trong danh sách import.'})
            continue
        seen_ids.add(item.id)
        try:
            response = client.table('songs').update({'lyrics': item.lyrics}).eq('id', item.id).select('id,title,artist,url,lyrics').execute()
            if response.data:
                updated.append(response.data[0])
            else:
                failed.append({'id': item.id, 'message': 'Không tìm thấy bài hát.'})
        except Exception as error:
            failed.append({'id': item.id, 'message': str(error)})
    return {
        'success': not failed,
        'updated_count': len(updated),
        'failed_count': len(failed),
        'updated': updated,
        'failed': failed,
        'message': f'Đã cập nhật {len(updated)} bài; link audio Cloudinary không thay đổi.' if not failed else f'Đã cập nhật {len(updated)} bài, có {len(failed)} mục lỗi.',
    }


@app.patch('/api/songs/{song_id}')
async def update_song(song_id: str, request: UpdateSongRequest, client: Client = Depends(require_supabase), _: dict = Depends(require_admin)) -> dict:
    try:
        response = client.table('songs').update(request.model_dump()).eq('id', song_id).select('*').execute()
        if not response.data:
            raise HTTPException(status_code=404, detail='Không tìm thấy bài hát để cập nhật.')
        return {'success': True, 'song': response.data[0], 'message': 'Đã cập nhật metadata; link Cloudinary giữ nguyên.'}
    except HTTPException:
        raise
    except Exception as error:
        raise HTTPException(status_code=502, detail=f'Không thể cập nhật bài hát: {error}')


@app.delete('/api/songs/{song_id}')
async def delete_song(song_id: str, client: Client = Depends(require_supabase), _: dict = Depends(require_admin)) -> dict:
    try:
        response = client.table('songs').select('id,url').eq('id', song_id).limit(1).execute()
        row = (response.data or [None])[0]
        if not row:
            raise HTTPException(status_code=404, detail='Không tìm thấy bài hát.')
        if row.get('url') or row.get('cloudinary_public_id'):
            try:
                delete_cloudinary_asset(row.get('url') or row.get('cloudinary_public_id'))
            except Exception as cloudinary_error:
                raise HTTPException(status_code=502, detail=f'Không thể xóa file âm thanh trên Cloudinary: {cloudinary_error}')
        client.table('songs').delete().eq('id', song_id).execute()
        return {'success': True, 'message': 'Đã xóa bài hát và file âm thanh trên Cloudinary.'}
    except HTTPException:
        raise
    except Exception as error:
        raise HTTPException(status_code=502, detail=f'Không thể xóa bài hát: {error}')


@app.get('/api/cinema/videos')
async def get_cinema_videos(client: Client = Depends(require_supabase), _: dict = Depends(get_current_user)) -> list:
    try:
        try:
            cleanup_expired_cinema_videos(client)
        except Exception as cleanup_error:
            print(f'⚠️ Bỏ qua cleanup Cinema trong lúc tải danh sách: {cleanup_error}')
        response = client.table('cinema_videos').select('*').order('created_at', desc=True).execute()
        return response.data or []
    except Exception as error:
        raise HTTPException(status_code=502, detail=f'Không thể tải kho LuNu Cinema. Hãy chạy migration Supabase: {error}')


@app.post('/api/cinema/videos/cleanup-expired')
async def cleanup_expired_cinema_videos_endpoint(client: Client = Depends(require_supabase), _: dict = Depends(require_admin)) -> dict:
    try:
        result = cleanup_expired_cinema_videos(client)
        return {'success': True, **result, 'message': f'Đã dọn {result["deleted_count"]} video tạm hết hạn.'}
    except Exception as error:
        raise HTTPException(status_code=502, detail=f'Không thể dọn video tạm: {error}')


@app.get('/api/cinema/search_youtube')
async def search_cinema_youtube(query: str = Query(min_length=2, max_length=120), mode: str = Query(default='video', pattern=r'^(video|channel)$')) -> dict:
    if mode == 'channel':
        try:
            results = search_youtube_channel_api(query)
            return {'success': True, 'results': results, 'source': 'youtube-data-api-channel', 'message': f'Tìm thấy {len(results)} video mới nhất từ kênh phù hợp.' if results else 'Không tìm thấy kênh hoặc kênh chưa có video công khai.'}
        except Exception as error:
            return {'success': False, 'results': [], 'source': 'youtube-data-api-channel', 'message': f'Không thể tìm theo kênh: {error}'}
    return await search_youtube(query)


@app.post('/api/cinema/videos/add', status_code=status.HTTP_202_ACCEPTED)
async def add_cinema_video(request: AddVideoRequest, background_tasks: BackgroundTasks, _: dict = Depends(require_admin)) -> dict:
    job_id = str(uuid.uuid4())
    import_jobs[job_id] = {'job_id': job_id, 'kind': 'video', 'status': 'queued', 'message': 'Đã nhận yêu cầu tải video.'}
    background_tasks.add_task(process_and_upload_video, job_id, request.model_dump())
    return {'success': True, 'job_id': job_id, 'status': 'queued', 'message': 'Đã nhận video. Bắt đầu tải và upload LuNu Cinema.'}


@app.delete('/api/cinema/videos/{video_id}')
async def delete_cinema_video(video_id: str, client: Client = Depends(require_supabase), _: dict = Depends(require_admin)) -> dict:
    try:
        response = client.table('cinema_videos').select('id,url,cloudinary_public_id').eq('id', video_id).limit(1).execute()
        row = (response.data or [None])[0]
        if not row:
            raise HTTPException(status_code=404, detail='Không tìm thấy video trong LuNu Cinema.')
        if row.get('url') or row.get('cloudinary_public_id'):
            try:
                delete_cloudinary_asset(row.get('url') or row.get('cloudinary_public_id'))
            except Exception as cloudinary_error:
                raise HTTPException(status_code=502, detail=f'Không thể xóa video trên Cloudinary: {cloudinary_error}')
        client.table('cinema_videos').delete().eq('id', video_id).execute()
        return {'success': True, 'message': 'Đã xóa video và file trên Cloudinary.'}
    except HTTPException:
        raise
    except Exception as error:
        raise HTTPException(status_code=502, detail=f'Không thể xóa video: {error}')


@app.post('/api/login')
async def login(req: LoginRequest, client: Client = Depends(require_supabase)) -> dict:
    try:
        result = client.table('users').select('*').eq('username', req.username.strip().lower()).limit(1).execute()
        if not result.data:
            return {'success': False, 'message': 'Sai tên tài khoản hoặc mật khẩu.'}
        record = result.data[0]
        stored_password = record.get('password_hash') or record.get('password') or ''
        if not verify_password(req.password, stored_password):
            return {'success': False, 'message': 'Sai tên tài khoản hoặc mật khẩu.'}
        if record.get('password') and not record.get('password_hash'):
            try:
                client.table('users').update({'password_hash': password_hash(req.password)}).eq('id', record['id']).execute()
            except Exception as migration_error:
                print('⚠️ Không thể ghi password_hash; tiếp tục tương thích schema cũ:', migration_error)
        user = public_user_payload(record)
        return {'success': True, 'user': user, 'access_token': issue_token(str(user['id']), user['role'])}
    except HTTPException:
        raise
    except Exception as error:
        raise HTTPException(status_code=502, detail=f'Lỗi đăng nhập: {error}')


@app.get('/api/me')
async def get_my_profile(client: Client = Depends(require_supabase), current_user: dict = Depends(get_current_user)) -> dict:
    return {'user': public_user_payload(get_profile_record(client, str(current_user['id'])))}


@app.patch('/api/me/profile')
async def update_my_profile(request: ProfileUpdateRequest, client: Client = Depends(require_supabase), current_user: dict = Depends(get_current_user)) -> dict:
    record = update_profile_record(client, str(current_user['id']), {
        'display_name': request.display_name or current_user.get('username', ''),
        'bio': request.bio,
        'updated_at': datetime.now(ZoneInfo('Asia/Ho_Chi_Minh')).isoformat(),
    })
    return {'success': True, 'user': public_user_payload(record), 'message': 'Đã cập nhật hồ sơ cá nhân.'}


@app.post('/api/me/password')
async def change_my_password(request: PasswordChangeRequest, client: Client = Depends(require_supabase), current_user: dict = Depends(get_current_user)) -> dict:
    try:
        response = client.table('users').select('id,password_hash,password').eq('id', current_user['id']).limit(1).execute()
    except Exception:
        response = client.table('users').select('id,password').eq('id', current_user['id']).limit(1).execute()
    record = (response.data or [None])[0]
    if not record:
        raise HTTPException(status_code=404, detail='Không tìm thấy tài khoản.')
    stored = record.get('password_hash') or record.get('password') or ''
    if not verify_password(request.current_password, stored):
        raise HTTPException(status_code=400, detail='Mật khẩu hiện tại không chính xác.')
    if request.current_password == request.new_password:
        raise HTTPException(status_code=400, detail='Mật khẩu mới phải khác mật khẩu hiện tại.')
    hashed = password_hash(request.new_password)
    try:
        client.table('users').update({'password_hash': hashed, 'updated_at': datetime.now(ZoneInfo('Asia/Ho_Chi_Minh')).isoformat()}).eq('id', current_user['id']).execute()
    except Exception:
        client.table('users').update({'password': hashed}).eq('id', current_user['id']).execute()
    return {'success': True, 'message': 'Đã đổi mật khẩu. Các phiên đăng nhập cũ vẫn còn hiệu lực trong thời gian token.'}


@app.post('/api/me/avatar')
async def upload_my_avatar(file: UploadFile = File(...), client: Client = Depends(require_supabase), current_user: dict = Depends(get_current_user)) -> dict:
    if not file.content_type or not file.content_type.startswith('image/'):
        raise HTTPException(status_code=415, detail='Avatar phải là file hình ảnh.')
    contents = await file.read(5 * 1024 * 1024 + 1)
    if len(contents) > 5 * 1024 * 1024:
        raise HTTPException(status_code=413, detail='Avatar không được lớn hơn 5 MiB.')
    if not all(os.getenv(key, '').strip() for key in ('CLOUDINARY_CLOUD_NAME', 'CLOUDINARY_API_KEY', 'CLOUDINARY_API_SECRET')):
        raise HTTPException(status_code=503, detail='Cloudinary chưa được cấu hình trên server.')
    try:
        result = cloudinary.uploader.upload(
            contents,
            resource_type='image',
            folder='lunu_avatars',
            public_id=f'user_{current_user["id"]}',
            overwrite=True,
            invalidate=True,
        )
        avatar_url = result.get('secure_url')
        if not avatar_url:
            raise RuntimeError('Cloudinary không trả về secure_url cho avatar.')
        record = update_profile_record(client, str(current_user['id']), {
            'avatar_url': avatar_url,
            'updated_at': datetime.now(ZoneInfo('Asia/Ho_Chi_Minh')).isoformat(),
        })
        return {'success': True, 'user': public_user_payload(record), 'message': 'Đã cập nhật ảnh đại diện.'}
    except HTTPException:
        raise
    except Exception as error:
        raise HTTPException(status_code=502, detail=f'Không thể cập nhật avatar: {error}') from error


@app.get('/api/users')
async def get_users(client: Client = Depends(require_supabase), _: dict = Depends(require_admin)) -> list:
    try:
        records = (client.table('users').select(PROFILE_COLUMNS).order('username').execute()).data or []
    except Exception:
        try:
            records = (client.table('users').select('id, username, role').order('username').execute()).data or []
        except Exception as error:
            raise HTTPException(status_code=502, detail=f'Không thể tải users: {error}')
    return [public_user_payload(record) for record in records]


@app.patch('/api/users/{user_id}/profile')
async def update_user_profile(user_id: str, request: AdminUserProfileRequest, client: Client = Depends(require_supabase), _: dict = Depends(require_admin)) -> dict:
    record = update_profile_record(client, user_id, {
        'display_name': request.display_name,
        'avatar_url': request.avatar_url,
        'bio': request.bio,
        'role': request.role,
        'updated_at': datetime.now(ZoneInfo('Asia/Ho_Chi_Minh')).isoformat(),
    })
    return {'success': True, 'user': public_user_payload(record), 'message': 'Đã cập nhật hồ sơ tài khoản.'}


@app.post('/api/users/add')
async def add_user(req: UserRequest, client: Client = Depends(require_supabase), _: dict = Depends(require_admin)) -> dict:
    try:
        hashed = password_hash(req.password)
        try:
            client.table('users').insert({'username': req.username, 'password_hash': hashed, 'role': req.role}).execute()
        except Exception as hash_column_error:
            print('⚠️ Schema chưa có password_hash, dùng cột password để lưu hash:', hash_column_error)
            client.table('users').insert({'username': req.username, 'password': hashed, 'role': req.role}).execute()
        return {'success': True, 'message': 'Đã cấp tài khoản thành công.'}
    except Exception as error:
        raise HTTPException(status_code=409, detail=f'Không thể tạo tài khoản: {error}')


@app.delete('/api/users/{user_id}')
async def delete_user(user_id: str, client: Client = Depends(require_supabase), _: dict = Depends(require_admin)) -> dict:
    try:
        client.table('users').delete().eq('id', user_id).execute()
        return {'success': True, 'message': 'Đã thu hồi tài khoản.'}
    except Exception as error:
        raise HTTPException(status_code=502, detail=f'Không thể xóa tài khoản: {error}')
