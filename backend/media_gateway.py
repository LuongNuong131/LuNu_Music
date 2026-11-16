"""Bounded, authenticated transport to an optional privately managed downloader."""
import json
import os
import re
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path


class MediaDownloadError(RuntimeError):
    def __init__(self, code: str, message: str, retry_after: int = 0):
        super().__init__(message)
        self.code = code
        self.retry_after = retry_after


class YoutubeCircuit:
    """Per-process cooldown; concurrent requests share the same blocked state."""
    def __init__(self):
        self._lock = threading.Lock()
        self._until = 0.0

    def remaining(self) -> int:
        with self._lock:
            return max(0, int(self._until - time.monotonic() + 0.999))

    def block(self, seconds: int):
        with self._lock:
            self._until = max(self._until, time.monotonic() + seconds)

    def check(self):
        remaining = self.remaining()
        if remaining:
            raise MediaDownloadError('YOUTUBE_COOLDOWN', f'Nguồn YouTube đang tạm nghỉ sau khi bị giới hạn. Thử lại sau {remaining} giây hoặc thêm file audio từ thiết bị.', remaining)


youtube_circuit = YoutubeCircuit()


def validate_media_request(video_id: str, mode: str):
    if not re.fullmatch(r'[A-Za-z0-9_-]{11}', video_id or ''):
        raise MediaDownloadError('INVALID_VIDEO_ID', 'Link YouTube không có mã video hợp lệ.')
    if mode not in {'song', 'video'}:
        raise MediaDownloadError('INVALID_MEDIA_MODE', 'Loại media không hợp lệ.')


def worker_config() -> tuple[str, str]:
    url = os.getenv('LUNU_MEDIA_WORKER_URL', '').strip().rstrip('/')
    token = os.getenv('LUNU_MEDIA_WORKER_TOKEN', '').strip()
    if not url:
        return '', ''
    parsed = urllib.parse.urlsplit(url)
    secure = parsed.scheme == 'https' or (parsed.scheme == 'http' and parsed.hostname in {'127.0.0.1', 'localhost', '::1'})
    if not secure or not parsed.hostname or parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise MediaDownloadError('WORKER_CONFIG', 'Địa chỉ máy tải nhạc phải dùng HTTPS (HTTP chỉ dành cho localhost).')
    if len(token) < 32:
        raise MediaDownloadError('WORKER_CONFIG', 'Khóa kết nối máy tải nhạc cần ít nhất 32 ký tự.')
    return url, token


def worker_status() -> dict:
    try:
        url, _ = worker_config()
        return {'configured': bool(url), 'configuration_valid': True}
    except MediaDownloadError:
        return {'configured': bool(os.getenv('LUNU_MEDIA_WORKER_URL', '').strip()), 'configuration_valid': False}


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, msg, headers, newurl):
        return None  # Never forward a worker credential to a redirected host.


def download_from_worker(video_id: str, mode: str, temp_dir: str, max_bytes: int) -> Path:
    validate_media_request(video_id, mode)
    url, token = worker_config()
    if not url:
        raise MediaDownloadError('WORKER_CONFIG', 'Chưa cấu hình máy tải nhạc.')
    timeout = max(5, min(1800, int(os.getenv('LUNU_MEDIA_WORKER_TIMEOUT_SECONDS', '600'))))
    request = urllib.request.Request(f'{url}/v1/media', data=json.dumps({'video_id': video_id, 'mode': mode}).encode(), headers={'Authorization': f'Bearer {token}', 'Content-Type': 'application/json', 'Accept': 'audio/mpeg' if mode == 'song' else 'video/mp4'}, method='POST')
    output = Path(temp_dir) / f'{video_id}.{ "mp3" if mode == "song" else "mp4"}'
    deadline = time.monotonic() + timeout
    completed = False
    try:
        opener = urllib.request.build_opener(NoRedirect())
        with opener.open(request, timeout=timeout) as response, output.open('wb') as handle:
            expected_type = 'audio/mpeg' if mode == 'song' else 'video/mp4'
            if response.headers.get_content_type() != expected_type:
                raise MediaDownloadError('WORKER_INVALID_RESPONSE', 'Máy tải nhạc trả về định dạng không hợp lệ.')
            length = int(response.headers.get('Content-Length', '0'))
            if length > max_bytes:
                raise MediaDownloadError('MEDIA_TOO_LARGE', 'File từ máy tải nhạc vượt giới hạn dung lượng.')
            total = 0
            while chunk := response.read(1024 * 1024):
                total += len(chunk)
                if total > max_bytes:
                    raise MediaDownloadError('MEDIA_TOO_LARGE', 'File từ máy tải nhạc vượt giới hạn dung lượng.')
                if time.monotonic() > deadline:
                    raise MediaDownloadError('WORKER_TIMEOUT', 'Máy tải nhạc xử lý quá lâu. Hãy thử file audio trực tiếp.')
                handle.write(chunk)
            if total < 1024 or (length and total != length):
                raise MediaDownloadError('WORKER_INCOMPLETE_FILE', 'File từ máy tải nhạc chưa được tải đầy đủ.')
        completed = True
        return output
    except urllib.error.HTTPError as error:
        # Deliberately avoid reflecting upstream HTML, URLs, headers or credentials.
        code = {401: 'WORKER_AUTH', 403: 'WORKER_AUTH', 429: 'WORKER_BUSY', 503: 'WORKER_UNAVAILABLE'}.get(error.code, 'WORKER_DOWNLOAD_FAILED')
        message = {'WORKER_AUTH': 'Khóa kết nối máy tải nhạc chưa đúng.', 'WORKER_BUSY': 'Máy tải nhạc đang bận. Hãy thử lại sau.', 'WORKER_UNAVAILABLE': 'Máy tải nhạc chưa sẵn sàng.'}.get(code, 'Máy tải nhạc chưa tải được video này. Kiểm tra trạng thái nguồn hoặc thêm file trực tiếp.')
        raise MediaDownloadError(code, message) from None
    except MediaDownloadError:
        raise
    except Exception:
        raise MediaDownloadError('WORKER_UNREACHABLE', 'Không kết nối được máy tải nhạc. Kiểm tra máy đang chạy và kết nối HTTPS.') from None
    finally:
        # Partial files must never be offered to the upload pipeline.
        if not completed:
            output.unlink(missing_ok=True)
