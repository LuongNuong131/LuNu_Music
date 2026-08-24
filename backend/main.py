import base64
import hashlib
import html
import hmac
import json
import os
import re
import secrets
import shutil
import tempfile
import time
import uuid
import unicodedata
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Optional

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
    allow_methods=['GET', 'POST', 'DELETE', 'OPTIONS'],
    allow_headers=['Authorization', 'Content-Type'],
)

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
    result = client.table('users').select('id, username, role').eq('id', payload.get('sub')).limit(1).execute()
    if not result.data:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Tài khoản không còn tồn tại.')
    return result.data[0]


async def require_admin(current_user: dict = Depends(get_current_user)) -> dict:
    if current_user.get('role') != 'admin':
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Bạn không có quyền quản trị.')
    return current_user


def get_ydl_opts(is_download: bool = False, temp_dir: Optional[str] = None) -> dict:
    opts = {
        'extractor_args': {'youtube': {'player_client': ['android', 'web']}},
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36'
        },
    }
    if is_download:
        cookie_path = Path.cwd() / 'cookies.txt'
        if cookie_path.exists():
            opts['cookiefile'] = str(cookie_path)
        if temp_dir:
            opts.update({
                'format': 'bestaudio/best',
                'noplaylist': True,
                'outtmpl': str(Path(temp_dir) / '%(id)s.%(ext)s'),
                'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '192'}],
            })
    else:
        opts.update({'extract_flat': True, 'quiet': True, 'skip_download': True})
    return opts


def _decode_json_text(value: str) -> str:
    try:
        return json.loads(f'"{value}"')
    except json.JSONDecodeError:
        return html.unescape(value).replace('\\"', '"')


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
    return list(dict.fromkeys([ascii_query, f'{ascii_query} music', f'{ascii_query} official', query]))


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


def process_and_upload_song(job_id: str, request_data: dict) -> None:
    video_id = request_data['video_id']
    client = None
    temp_dir = tempfile.mkdtemp(prefix='lunu-')
    file_path: Optional[Path] = None
    set_import_job(job_id, status='processing', message='Đang tải audio từ YouTube...')
    try:
        client = require_supabase()
        if not all(os.getenv(key, '').strip() for key in ('CLOUDINARY_CLOUD_NAME', 'CLOUDINARY_API_KEY', 'CLOUDINARY_API_SECRET')):
            raise RuntimeError('Cloudinary chưa được cấu hình trên Render.')
        url = f'https://www.youtube.com/watch?v={video_id}'
        with yt_dlp.YoutubeDL(get_ydl_opts(True, temp_dir)) as ydl:
            ydl.extract_info(url, download=True)
        candidates = sorted(Path(temp_dir).glob(f'{video_id}*.mp3'))
        if not candidates:
            raise FileNotFoundError('FFmpeg/yt-dlp không tạo được file MP3. Kiểm tra FFmpeg trên Render.')
        file_path = candidates[0]
        set_import_job(job_id, message='Đã tải MP3, đang upload lên Cloudinary...')
        result = cloudinary.uploader.upload(
            str(file_path), resource_type='video', public_id=f'lunu_music/{video_id}',
            overwrite=True, unique_filename=False,
        )
        secure_url = result.get('secure_url')
        if not secure_url:
            raise RuntimeError('Cloudinary không trả về secure_url.')
        song_data = {
            'id': str(uuid.uuid4()),
            'title': request_data['title'],
            'artist': request_data['artist'],
            'url': secure_url,
            'cover': request_data.get('cover') or f'https://i.ytimg.com/vi/{video_id}/hqdefault.jpg',
            'lyrics': request_data.get('lyrics', ''),
        }
        set_import_job(job_id, message='Đã upload Cloudinary, đang ghi metadata vào Supabase...')
        existing = client.table('songs').select('id').eq('url', secure_url).limit(1).execute()
        if existing.data:
            client.table('songs').update({key: value for key, value in song_data.items() if key != 'id'}).eq('id', existing.data[0]['id']).execute()
            song_data['id'] = existing.data[0]['id']
            set_import_job(job_id, status='completed', message='Đã cập nhật metadata bài hát trong thư viện.', song=song_data)
        else:
            client.table('songs').insert(song_data).execute()
            set_import_job(job_id, status='completed', message='Đã thêm bài hát vào thư viện.', song=song_data)
        print(f'✅ Đã thêm bài hát: {song_data["title"]}')
    except Exception as error:
        set_import_job(job_id, status='failed', message=str(error))
        print(f'❌ Lỗi xử lý video {video_id}: {error}')
    finally:
        if file_path and file_path.exists():
            file_path.unlink(missing_ok=True)
        shutil.rmtree(temp_dir, ignore_errors=True)


@app.get('/api/health')
async def health() -> dict:
    return {'ok': True, 'supabase_configured': supabase is not None}


@app.get('/api/songs')
async def get_songs(client: Client = Depends(require_supabase)) -> list:
    try:
        response = client.table('songs').select('*').order('title').execute()
        return response.data or []
    except Exception as error:
        raise HTTPException(status_code=502, detail=f'Không thể tải thư viện nhạc: {error}')


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
        pending = [song for song in catalog if song.get('url') not in existing_urls]
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
            attempts = 2 if variant_index < 3 else 1
            for _ in range(attempts):
                music_results.extend(search_youtube_music(variant))
        ranked = rank_search_results(music_results, normalized_query)
        if ranked:
            best_results = ranked
            if has_relevant_result(ranked, normalized_query):
                return {'success': True, 'results': ranked[:10], 'source': 'youtube-music'}
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
    return {'success': False, 'results': [], 'message': 'YouTube không trả kết quả cho từ khóa này. Thử gõ ngắn hơn hoặc bỏ ký tự đặc biệt.'}


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


@app.delete('/api/songs/{song_id}')
async def delete_song(song_id: str, client: Client = Depends(require_supabase), _: dict = Depends(require_admin)) -> dict:
    try:
        client.table('songs').delete().eq('id', song_id).execute()
        return {'success': True, 'message': 'Đã xóa bài hát khỏi hệ thống.'}
    except Exception as error:
        raise HTTPException(status_code=502, detail=f'Không thể xóa bài hát: {error}')


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
