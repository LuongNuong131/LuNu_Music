"""Run on your own machine/VPS, independently of Render's egress IP.

uvicorn media_worker:app --host 127.0.0.1 --port 8010 --workers 1
Expose behind an HTTPS reverse proxy; use the same 32+ character token on Render.
"""
import hmac
import os
import shutil
import tempfile
import threading
from typing import Literal

from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from starlette.background import BackgroundTask

from media_gateway import MediaDownloadError
from main import _download_youtube_locally

app = FastAPI(title='LuNu private media worker', docs_url=None, redoc_url=None, openapi_url=None)
slot = threading.BoundedSemaphore(1)


class MediaRequest(BaseModel):
    video_id: str = Field(pattern=r'^[A-Za-z0-9_-]{11}$')
    mode: Literal['song', 'video'] = 'song'


def require_worker_token(authorization: str = Header(default='')):
    token = os.getenv('LUNU_MEDIA_WORKER_TOKEN', '').strip()
    if len(token) < 32:
        raise HTTPException(503, detail={'code': 'WORKER_CONFIG', 'message': 'Worker token is not configured.'})
    if not hmac.compare_digest(authorization.encode(), f'Bearer {token}'.encode()):
        raise HTTPException(401, detail={'code': 'WORKER_AUTH', 'message': 'Unauthorized.'})


@app.get('/health')
def health():
    return {'ok': len(os.getenv('LUNU_MEDIA_WORKER_TOKEN', '').strip()) >= 32, 'ffmpeg': bool(shutil.which('ffmpeg')), 'node': bool(shutil.which('node'))}


@app.post('/v1/media', dependencies=[Depends(require_worker_token)])
def download(request: MediaRequest):
    if not slot.acquire(blocking=False):
        raise HTTPException(429, detail={'code': 'WORKER_BUSY', 'message': 'A download is already running.'}, headers={'Retry-After': '30'})
    temp_dir = tempfile.mkdtemp(prefix='lunu-worker-')
    def cleanup():
        shutil.rmtree(temp_dir, ignore_errors=True)
        slot.release()
    try:
        path = _download_youtube_locally(request.video_id, temp_dir, request.mode)
        return FileResponse(path, media_type='audio/mpeg' if request.mode == 'song' else 'video/mp4', filename=path.name, background=BackgroundTask(cleanup))
    except MediaDownloadError as error:
        cleanup()
        raise HTTPException(503, detail={'code': error.code, 'message': str(error)}, headers={'Retry-After': str(error.retry_after or 30)}) from None
    except Exception:
        cleanup()
        raise HTTPException(502, detail={'code': 'DOWNLOAD_FAILED', 'message': 'The source could not be downloaded.'}) from None
