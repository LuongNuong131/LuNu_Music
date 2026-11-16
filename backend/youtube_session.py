"""Remember explicit cookie rejections without exposing credential contents."""
import hashlib
import logging
import threading

logger = logging.getLogger('lunu.youtube')


class CookieSessions:
    def __init__(self):
        self._lock = threading.Lock()
        self._rejected = set()

    def fingerprint(self, content: bytes) -> str:
        return hashlib.sha256(content.replace(b'\r\n', b'\n')).hexdigest()

    def rejected(self, fingerprint: str) -> bool:
        with self._lock:
            return fingerprint in self._rejected

    def reject(self, fingerprint: str):
        if not fingerprint:
            return
        with self._lock:
            if len(self._rejected) >= 16:
                self._rejected.clear()
            self._rejected.add(fingerprint)


cookie_sessions = CookieSessions()


class YoutubeLogger:
    def __init__(self, cookie_fingerprint: str = ''):
        self.cookie_fingerprint = cookie_fingerprint
        self.cookies_rejected = False

    def debug(self, message):
        if not str(message).startswith('[debug]'):
            logger.info('%s', message)

    def warning(self, message):
        text = str(message)
        lowered = text.lower()
        if self.cookie_fingerprint and any(marker in lowered for marker in (
            'cookies are no longer valid', 'cookies have expired', 'cookies are expired',
        )):
            self.cookies_rejected = True
            cookie_sessions.reject(self.cookie_fingerprint)
        logger.warning('%s', text)

    def error(self, message):
        logger.error('%s', message)
