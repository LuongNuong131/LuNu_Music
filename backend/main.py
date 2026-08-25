import base64
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
from datetime import datetime
from zoneinfo import ZoneInfo
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Literal, Optional

import cloudinary
import cloudinary.uploader
import yt_dlp
from dotenv import load_dotenv
from fastapi import BackgroundTasks, Depends, FastAPI, Header, HTTPException, Query, status
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

SUPABASE_URL = os.getenv('SUPABASE_URL', '').strip()
SUPABASE_KEY = os.getenv('SUPABASE_KEY', '').strip()
AUTH_SECRET = os.getenv('LUNU_AUTH_SECRET', '').strip() or 'change-this-secret-in-production'
if AUTH_SECRET == 'change-this-secret-in-production':
    print('⚠️ LUNU_AUTH_SECRET chưa được cấu hình; hãy thay bằng secret dài trên Render.')

supabase: Optional[Client] = None
import_jobs: dict[str, dict] = {}

if SUPABASE_URL and SUPABASE_KEY:
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception as error:
        print('⚠️ Lỗi khởi tạo Supabase:', error)
else:
    print('⚠️ Thiếu SUPABASE_URL hoặc SUPABASE_KEY; API database sẽ trả lỗi cấu hình.')

if all(os.getenv(key, '').strip() for key in ('CLOUDINARY_CLOUD_NAME', 'CLOUDINARY_API_KEY', 'CLOUDINARY_API_SECRET')):
    cloudinary.config(
        cloud_name=os.getenv('CLOUDINARY_CLOUD_NAME'),
        api_key=os.getenv('CLOUDINARY_API_KEY'),
        api_secret=os.getenv('CLOUDINARY_API_SECRET'),
        secure=True,
    )
else:
    print('⚠️ Thiếu Cloudinary credentials; upload sẽ bị từ chối rõ ràng.')


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


def get_ydl_opts(is_download: bool = False, temp_dir: Optional[str] = None, *, client: str = 'web', format_selector: Optional[str] = None, output_template: Optional[str] = None, postprocessors: Optional[list[dict]] = None) -> dict:
    opts = {
        'extractor_args': {'youtube': {'player_client': [client]}},
        'js_runtimes': {'node': {}},
        'remote_components': ['ejs:github'],
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36'
        },
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
    else:
        opts.update({'extract_flat': True, 'quiet': True, 'skip_download': True})
    return opts


def today_stamp() -> str:
    return datetime.now(ZoneInfo('Asia/Ho_Chi_Minh')).strftime('%d%m%Y')


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


def is_missing_table_error(error: Exception, table_name: str) -> bool:
    detail = str(error)
    return table_name in detail and ('PGRST205' in detail or 'schema cache' in detail or 'Could not find the table' in detail)


def available_media_files(temp_dir: str, video_id: str) -> list[Path]:
    image_extensions = {'.jpg', '.jpeg', '.png', '.webp', '.gif', '.vtt', '.part', '.ytdl'}
    return [item for item in Path(temp_dir).glob(f'{video_id}*') if item.is_file() and item.suffix.lower() not in image_extensions]


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
        ('web', 'bestvideo[height<=1080]+bestaudio/best[ext=mp4][height<=1080]/best[ext=webm]/best'),
        ('tv', 'best[height<=1080]/best'),
        ('ios', 'best[height<=1080]/best'),
    ]
    errors = []
    for client, selector in profiles:
        try:
            options = get_ydl_opts(True, temp_dir, client=client, format_selector=selector, postprocessors=[] if mode == 'video' else None)
            with yt_dlp.YoutubeDL(options) as ydl:
                info = ydl.extract_info(url, download=False)
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
        except Exception as error:
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
        result = cloudinary.uploader.upload(str(file_path), resource_type='video', public_id=public_id, overwrite=False, unique_filename=False)
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
        result = cloudinary.uploader.upload(str(file_path), resource_type='video', public_id=public_id, overwrite=False, unique_filename=False)
        secure_url = result.get('secure_url')
        if not secure_url:
            raise RuntimeError('Cloudinary không trả về secure_url cho video.')
        video_data = {
            'id': str(uuid.uuid4()), 'media_key': media_key, 'source_id': video_id,
            'cloudinary_public_id': public_id, 'title': request_data['title'], 'uploader': request_data.get('uploader') or 'YouTube',
            'url': secure_url, 'cover': DEFAULT_COVER,
            'description': request_data.get('description', ''),
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


@app.get('/api/health')
async def health() -> dict:
    return {'ok': True, 'supabase_configured': supabase is not None}


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
        response = client.table('cinema_videos').select('*').order('created_at', desc=True).execute()
        return response.data or []
    except Exception as error:
        raise HTTPException(status_code=502, detail=f'Không thể tải kho LuNu Cinema. Hãy chạy migration Supabase: {error}')


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
        user = {'id': record['id'], 'username': record['username'], 'role': record.get('role', 'user')}
        return {'success': True, 'user': user, 'access_token': issue_token(str(user['id']), user['role'])}
    except HTTPException:
        raise
    except Exception as error:
        raise HTTPException(status_code=502, detail=f'Lỗi đăng nhập: {error}')


@app.get('/api/users')
async def get_users(client: Client = Depends(require_supabase), _: dict = Depends(require_admin)) -> list:
    try:
        return (client.table('users').select('id, username, role').order('username').execute()).data or []
    except Exception as error:
        raise HTTPException(status_code=502, detail=f'Không thể tải users: {error}')


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
