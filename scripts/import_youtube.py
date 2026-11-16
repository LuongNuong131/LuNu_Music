#!/usr/bin/env python3
"""Download on your own computer, then use LuNu's normal authenticated upload.

Install: python -m pip install 'yt-dlp[default]==2026.10.26' httpx
FFmpeg and Node must be on PATH. Passwords are prompted, never command arguments.
"""
import argparse
import getpass
import sys
import tempfile
import time
from pathlib import Path
from urllib.parse import urlsplit

import httpx
import yt_dlp


def run():
    parser = argparse.ArgumentParser(description='Import your permitted YouTube audio through your computer instead of Render.')
    parser.add_argument('url', help='A YouTube video URL you have permission to download')
    parser.add_argument('--api', required=True, help='Your API base URL, e.g. https://lunu-music.onrender.com/api')
    parser.add_argument('--username', required=True)
    parser.add_argument('--title')
    parser.add_argument('--artist')
    parser.add_argument('--cookies', type=Path, help='Optional private Netscape cookies file; never commit it')
    args = parser.parse_args()
    parsed = urlsplit(args.api)
    if parsed.username or parsed.password or parsed.query or parsed.fragment:
        parser.error('--api must not contain credentials, query parameters or fragments')
    if parsed.scheme != 'https' and not (parsed.scheme == 'http' and parsed.hostname in {'localhost','127.0.0.1'}):
        parser.error('--api must use HTTPS (except localhost)')
    if urlsplit(args.url).hostname not in {'youtube.com','www.youtube.com','m.youtube.com','youtu.be','music.youtube.com'}:
        parser.error('Only YouTube video URLs are supported')
    password = getpass.getpass('LuNu password: ')
    with httpx.Client(base_url=args.api.rstrip('/')+'/', timeout=httpx.Timeout(600,connect=20), follow_redirects=False) as client:
        response = client.post('login',json={'username':args.username,'password':password})
        del password
        response.raise_for_status()
        login = response.json()
        if login.get('user',{}).get('role') != 'admin' or not login.get('access_token'):
            raise RuntimeError('An administrator account is required.')
        client.headers['Authorization'] = 'Bearer '+login['access_token']
        with tempfile.TemporaryDirectory(prefix='lunu-local-') as directory:
            options = {'format':'bestaudio/best[acodec!=none]','noplaylist':True,'outtmpl':str(Path(directory)/'audio.%(ext)s'),'postprocessors':[{'key':'FFmpegExtractAudio','preferredcodec':'mp3','preferredquality':'192'}],'js_runtimes':{'node':{}},'socket_timeout':30,'retries':1,'max_filesize':200*1024*1024}
            if args.cookies:
                options['cookiefile'] = str(args.cookies)
            with yt_dlp.YoutubeDL(options) as downloader:
                info = downloader.extract_info(args.url,download=True)
            path = Path(directory)/'audio.mp3'
            if path.stat().st_size > 200*1024*1024:
                raise RuntimeError('Audio exceeds the 200 MiB upload limit.')
            with path.open('rb') as handle:
                response = client.post('songs/upload',files={'file':('audio.mp3',handle,'audio/mpeg')},data={'title':args.title or info.get('track') or info.get('title') or 'YouTube audio','artist':args.artist or info.get('artist') or info.get('uploader') or 'Unknown artist','cover':info.get('thumbnail') or ''})
            response.raise_for_status()
            job_id = response.json()['job_id']
        deadline = time.monotonic()+900
        while time.monotonic()<deadline:
            response = client.get('songs/import-jobs/'+job_id)
            response.raise_for_status()
            job = response.json()
            print(job.get('message') or job['status'])
            if job['status']=='completed':
                return
            if job['status']=='failed':
                raise RuntimeError(job.get('message') or 'Import failed')
            time.sleep(2)
        raise RuntimeError('Import is still pending after 15 minutes; check the admin interface.')


if __name__=='__main__':
    try:
        run()
    except (httpx.HTTPError,RuntimeError,OSError,KeyError,yt_dlp.utils.DownloadError) as error:
        # HTTP exception strings can contain request URLs; never print headers/tokens.
        print(f'Import did not finish: {error}',file=sys.stderr)
        sys.exit(1)
