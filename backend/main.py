import base64
import hashlib
import hmac
import json
import os
import secrets
import shutil
import tempfile
import time
import uuid
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
            'User-Agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 Chrome/120 Mobile Safari/537.36'
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


def process_and_upload_song(video_id: str) -> None:
    client = require_supabase()
    if not all(os.getenv(key, '').strip() for key in ('CLOUDINARY_CLOUD_NAME', 'CLOUDINARY_API_KEY', 'CLOUDINARY_API_SECRET')):
        raise RuntimeError('Cloudinary chưa được cấu hình.')
    temp_dir = tempfile.mkdtemp(prefix='lunu-')
    file_path: Optional[Path] = None
    try:
        url = f'https://www.youtube.com/watch?v={video_id}'
        with yt_dlp.YoutubeDL(get_ydl_opts(True, temp_dir)) as ydl:
            info = ydl.extract_info(url, download=True)
        candidates = list(Path(temp_dir).glob(f'{video_id}*.mp3'))
        if not candidates:
            raise FileNotFoundError('yt-dlp không tạo được file mp3.')
        file_path = candidates[0]
        result = cloudinary.uploader.upload(
            str(file_path), resource_type='video', folder='lunu_music', use_filename=True,
            unique_filename=False, overwrite=True,
        )
        secure_url = result.get('secure_url')
        if not secure_url:
            raise RuntimeError('Cloudinary không trả về secure_url.')
        song_data = {
            'id': str(uuid.uuid4()),
            'title': info.get('title', 'Đang cập nhật'),
            'artist': info.get('uploader', 'Đang cập nhật'),
            'url': secure_url,
            'cover': info.get('thumbnail', f'https://i.ytimg.com/vi/{video_id}/hqdefault.jpg'),
            'lyrics': '',
        }
        client.table('songs').insert(song_data).execute()
        print(f'✅ Đã thêm bài hát: {song_data["title"]}')
    except Exception as error:
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
    try:
        with yt_dlp.YoutubeDL(get_ydl_opts(False)) as ydl:
            info = ydl.extract_info(f'ytsearch10:{query.strip()}', download=False)
        results = [
            {'id': entry.get('id'), 'title': entry.get('title'), 'uploader': entry.get('uploader', entry.get('channel', 'YouTube'))}
            for entry in info.get('entries', []) if entry and entry.get('id')
        ]
        return {'success': True, 'results': results}
    except Exception as error:
        print('❌ Lỗi tìm kiếm YouTube:', error)
        return {'success': False, 'results': [], 'message': 'YouTube tạm thời không phản hồi.'}


@app.post('/api/songs/add', status_code=status.HTTP_202_ACCEPTED)
async def add_song(request: AddSongRequest, background_tasks: BackgroundTasks, _: dict = Depends(require_admin)) -> dict:
    background_tasks.add_task(process_and_upload_song, request.video_id)
    return {'success': True, 'status': 'queued', 'message': 'Đã đưa bài hát vào hàng đợi xử lý.'}


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
