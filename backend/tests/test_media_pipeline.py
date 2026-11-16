import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import main
import media_gateway as gateway
import media_worker

TOKEN = 'private-test-token-' + 'x' * 40
VIDEO = 'BaW_jenozKc'


@pytest.fixture(autouse=True)
def isolated_configuration(monkeypatch):
    for key in ['LUNU_MEDIA_WORKER_URL', 'LUNU_MEDIA_WORKER_TOKEN', 'YOUTUBE_COOKIES_B64', 'YOUTUBE_COOKIES_PATH']:
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setattr(main, 'youtube_circuit', gateway.YoutubeCircuit())


@pytest.fixture
def worker_server(monkeypatch):
    observed = []
    behavior = {'status': 200, 'body': b'media' * 400, 'content_type': 'audio/mpeg'}
    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            body = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
            observed.append({'path': self.path, 'auth': self.headers.get('Authorization'), 'body': body})
            self.send_response(behavior['status'])
            if behavior['status'] == 302:
                self.send_header('Location', '/capture')
            self.send_header('Content-Type', behavior['content_type'])
            self.send_header('Content-Length', str(len(behavior['body'])))
            self.end_headers()
            self.wfile.write(behavior['body'])
        def log_message(self, *_):
            pass
    server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    monkeypatch.setenv('LUNU_MEDIA_WORKER_URL', f'http://127.0.0.1:{server.server_port}')
    monkeypatch.setenv('LUNU_MEDIA_WORKER_TOKEN', TOKEN)
    yield behavior, observed
    server.shutdown()
    server.server_close()
    thread.join()


def test_worker_transport_downloads_exact_file_and_uses_server_only_token(worker_server, tmp_path):
    behavior, observed = worker_server
    output = gateway.download_from_worker(VIDEO, 'song', str(tmp_path), 10_000)
    assert output.read_bytes() == behavior['body']
    assert observed == [{'path': '/v1/media', 'auth': f'Bearer {TOKEN}', 'body': {'video_id': VIDEO, 'mode': 'song'}}]


@pytest.mark.parametrize('failure', ['oversize', 'wrong_type', 'redirect', 'unauthorized'])
def test_worker_failure_leaves_no_uploadable_file_or_secret(worker_server, tmp_path, failure):
    behavior, observed = worker_server
    limit = 10_000
    if failure == 'oversize':
        limit = 1024
    elif failure == 'wrong_type':
        behavior['content_type'] = 'text/html'
    elif failure == 'redirect':
        behavior['status'] = 302
    else:
        behavior['status'] = 401
    with pytest.raises(gateway.MediaDownloadError) as error:
        gateway.download_from_worker(VIDEO, 'song', str(tmp_path), limit)
    assert TOKEN not in str(error.value)
    assert not list(tmp_path.iterdir())
    assert len(observed) == 1  # A redirect must not receive another authenticated request.


def test_remote_worker_is_used_without_hitting_render_youtube(worker_server, tmp_path, monkeypatch):
    def forbidden_local(*_):
        pytest.fail('Render should not extract YouTube while a worker is configured')
    monkeypatch.setattr(main, '_download_youtube_locally', forbidden_local)
    assert main.download_media(VIDEO, str(tmp_path), 'song').read_bytes() == b'media' * 400


@pytest.mark.parametrize('video_id', ['../secrets', 'https://example.com/media', 'short', 'a'*12])
def test_download_rejects_non_video_ids_before_network(video_id, tmp_path):
    with pytest.raises(gateway.MediaDownloadError, match='mã video'):
        main.download_media(video_id, str(tmp_path), 'song')


@pytest.mark.parametrize('url', ['http://example.com', 'https://user:password@example.com', 'https://example.com?token=secret', 'file:///tmp/media'])
def test_worker_configuration_rejects_insecure_or_credential_bearing_urls(monkeypatch, url):
    monkeypatch.setenv('LUNU_MEDIA_WORKER_URL', url)
    monkeypatch.setenv('LUNU_MEDIA_WORKER_TOKEN', TOKEN)
    assert gateway.worker_status()['configuration_valid'] is False
    with pytest.raises(gateway.MediaDownloadError):
        gateway.worker_config()


def test_youtube_challenge_sets_cooldown_and_cleans_private_cookie(tmp_path, monkeypatch):
    calls = []
    cookie = tmp_path / 'private-cookie.txt'
    cookie.write_text('# Netscape HTTP Cookie File\n')
    monkeypatch.setattr(main, 'get_ydl_opts', lambda *args, **kwargs: {'cookiefile': str(cookie)})
    class BlockedDownloader:
        def __init__(self, options):
            calls.append(options)
        def __enter__(self):
            return self
        def __exit__(self, *_):
            pass
        def extract_info(self, *_args, **_kwargs):
            raise RuntimeError('HTTP Error 429: Too Many Requests')
    monkeypatch.setattr(main.yt_dlp, 'YoutubeDL', BlockedDownloader)
    with pytest.raises(gateway.MediaDownloadError) as first:
        main._download_youtube_locally(VIDEO, str(tmp_path), 'song')
    assert first.value.code == 'YOUTUBE_RATE_LIMITED'
    assert first.value.retry_after > 0
    assert not cookie.exists()
    with pytest.raises(gateway.MediaDownloadError) as second:
        main._download_youtube_locally(VIDEO, str(tmp_path), 'song')
    assert second.value.code == 'YOUTUBE_COOLDOWN'
    assert len(calls) == 1


def test_cooldown_expires_without_busy_retries(monkeypatch):
    now = [10.0]
    monkeypatch.setattr(gateway.time, 'monotonic', lambda: now[0])
    circuit = gateway.YoutubeCircuit()
    circuit.block(30)
    with pytest.raises(gateway.MediaDownloadError):
        circuit.check()
    now[0] = 41.0
    assert circuit.remaining() == 0
    circuit.check()


def test_worker_requires_authentication_and_rejects_arbitrary_urls(monkeypatch):
    monkeypatch.setenv('LUNU_MEDIA_WORKER_TOKEN', TOKEN)
    client = TestClient(media_worker.app)
    assert client.post('/v1/media', json={'video_id': VIDEO}).status_code == 401
    assert client.post('/v1/media', headers={'Authorization': 'Bearer wrong'}, json={'video_id': VIDEO}).status_code == 401
    assert client.post('/v1/media', headers={'Authorization': f'Bearer {TOKEN}'}, json={'video_id': 'https://example.com'}).status_code == 422


def test_worker_streams_then_removes_file_and_releases_capacity(monkeypatch):
    monkeypatch.setenv('LUNU_MEDIA_WORKER_TOKEN', TOKEN)
    paths = []
    def download(video_id, temp_dir, mode):
        path = Path(temp_dir) / f'{video_id}.mp3'
        path.write_bytes(b'audio' * 400)
        paths.append(path)
        return path
    monkeypatch.setattr(media_worker, '_download_youtube_locally', download)
    client = TestClient(media_worker.app)
    for _ in range(2):
        response = client.post('/v1/media', headers={'Authorization': f'Bearer {TOKEN}'}, json={'video_id': VIDEO})
        assert response.status_code == 200
        assert response.headers['content-type'].startswith('audio/mpeg')
        assert response.content == b'audio' * 400
    assert all(not path.parent.exists() for path in paths)


def test_worker_busy_response_is_bounded_and_retryable(monkeypatch):
    monkeypatch.setenv('LUNU_MEDIA_WORKER_TOKEN', TOKEN)
    assert media_worker.slot.acquire(blocking=False)
    try:
        response = TestClient(media_worker.app).post('/v1/media', headers={'Authorization': f'Bearer {TOKEN}'}, json={'video_id': VIDEO})
        assert response.status_code == 429
        assert response.headers['Retry-After'] == '30'
    finally:
        media_worker.slot.release()


def test_health_reports_configuration_without_credentials(monkeypatch):
    monkeypatch.setenv('LUNU_MEDIA_WORKER_URL', 'https://private-worker.example')
    monkeypatch.setenv('LUNU_MEDIA_WORKER_TOKEN', TOKEN)
    response = TestClient(main.app).get('/api/health')
    assert response.status_code == 200
    assert response.json()['media_worker'] == {'configured': True, 'configuration_valid': True}
    assert TOKEN not in response.text
    assert 'private-worker.example' not in response.text
