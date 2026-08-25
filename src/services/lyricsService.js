const STORAGE_KEY = 'lunu_lyrics_v1';

const isBrowser = typeof window !== 'undefined';
const PLACEHOLDER_VALUES = new Set(['đang cập nhật...', 'đang cập nhật', 'chưa có lời', 'no lyrics']);
let provider = null;

const readStore = () => {
  if (!isBrowser) return {};
  try {
    const value = JSON.parse(window.localStorage.getItem(STORAGE_KEY) || '{}');
    return value && typeof value === 'object' ? value : {};
  } catch {
    return {};
  }
};

const writeStore = (store) => {
  if (!isBrowser) return;
  try {
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(store));
  } catch {
    // Storage may be unavailable in private browsing; the UI still works in-memory.
  }
};

export const normalizeLyrics = (value) => {
  if (typeof value !== 'string') return '';
  const clean = value.replace(/^\uFEFF/, '').replace(/\r\n/g, '\n').trim();
  const plain = clean.replace(/\[\d{1,3}:\d{2}(?:\.\d{1,3})?\]\s*/g, '').replace(/\n{3,}/g, '\n\n').trim();
  return PLACEHOLDER_VALUES.has(plain.toLowerCase()) ? '' : plain;
};

export const hasLyrics = (value) => normalizeLyrics(value).length > 0;
export const isTimedLyrics = () => false;

export const parseLyrics = (value, offsetMs = 0) => {
  const raw = normalizeLyrics(value);
  if (!raw) return [];
  const lines = [];
  const linePattern = /\[(\d{1,3}):(\d{2}(?:\.\d{1,3})?)\]/g;
  raw.split('\n').forEach((line, sourceIndex) => {
    const matches = [...line.matchAll(linePattern)];
    if (!matches.length) return;
    const text = line.replace(linePattern, '').trim();
    if (!text) return;
    matches.forEach((match) => {
      const time = Math.max(0, Number(match[1]) * 60 + Number(match[2]) + offsetMs / 1000);
      lines.push({ time, text, sourceIndex });
    });
  });
  return lines.sort((a, b) => a.time - b.time);
};

export const getLyricsMode = (value) => (isTimedLyrics(value) ? 'synced' : hasLyrics(value) ? 'plain' : 'missing');

export const getStoredLyrics = (songId) => readStore()[String(songId)] || null;

export const saveLyrics = (songId, payload) => {
  const content = normalizeLyrics(payload?.content ?? payload?.lyrics ?? '');
  const existing = getStoredLyrics(songId) || {};
  const record = {
    content,
    source: payload?.source || 'manual',
    offsetMs: Number.isFinite(Number(payload?.offsetMs)) ? Number(payload.offsetMs) : Number(existing.offsetMs || 0),
    updatedAt: new Date().toISOString(),
  };
  const store = readStore();
  store[String(songId)] = record;
  writeStore(store);
  return record;
};

export const updateLyricsOffset = (songId, offsetMs) => saveLyrics(songId, { ...(getStoredLyrics(songId) || {}), offsetMs });
export const removeStoredLyrics = (songId) => {
  const store = readStore();
  delete store[String(songId)];
  writeStore(store);
};

export const getSongSearchTerms = (song) => ({
  artist: song?.artist || '',
  title: song?.title || '',
  album: song?.album || '',
  filename: (song?.url || '').split('/').pop()?.replace(/\.[^.]+$/, '') || '',
});

/**
 * Optional provider contract. A provider may be registered later without changing UI:
 * { find(song, { signal }): Promise<{ content, source } | null> }.
 * No provider is enabled by default, so the app never exposes an API key in the browser.
 */
export const setLyricsProvider = (nextProvider) => {
  provider = nextProvider && typeof nextProvider.find === 'function' ? nextProvider : null;
};

export const lookupLyrics = async (song, options = {}) => {
  if (!provider) return { status: 'unavailable', content: '', source: 'provider-unavailable', terms: getSongSearchTerms(song) };
  try {
    const result = await provider.find(song, options);
    const content = normalizeLyrics(result?.content ?? result?.lyrics ?? '');
    return content ? { status: 'found', content, source: result?.source || 'provider' } : { status: 'not-found', content: '', source: 'provider' };
  } catch (error) {
    if (error?.name === 'AbortError') throw error;
    return { status: 'error', content: '', source: 'provider-error', error };
  }
};

export const resolveLyrics = async (song, options = {}) => {
  const stored = getStoredLyrics(song?.id);
  if (stored?.content) return { ...stored, status: stored.source === 'manual' ? 'manual' : 'metadata', mode: 'plain' };

  const metadataLyrics = normalizeLyrics(song?.lyrics || song?.metadata?.lyrics || song?.metadata?.unsyncedLyrics || '');
  if (metadataLyrics) return { content: metadataLyrics, source: 'metadata', offsetMs: 0, status: 'metadata', mode: getLyricsMode(metadataLyrics) };

  if (options.allowProvider !== false) {
    const remote = await lookupLyrics(song, options);
    if (remote.content) {
      const saved = saveLyrics(song.id, remote);
      return { ...saved, status: 'found', mode: getLyricsMode(saved.content) };
    }
    return { content: '', source: remote.source, offsetMs: stored?.offsetMs || 0, status: remote.status, mode: 'missing' };
  }
  return { content: '', source: 'none', offsetMs: 0, status: 'missing', mode: 'missing' };
};

export const getLyricsInventory = (songs) => songs.reduce((summary, song) => {
  const stored = getStoredLyrics(song.id);
  const raw = stored?.content || song.lyrics || song.metadata?.lyrics || '';
  const mode = getLyricsMode(raw);
  summary.total += 1;
  summary[mode] += 1;
  if (stored?.content && stored.source === 'manual') summary.manual += 1;
  return summary;
}, { total: 0, synced: 0, plain: 0, missing: 0, manual: 0 });

export const createFallbackMessage = (song) => `Chưa có lời bài hát cho “${song?.title || 'bài hát này'}”.\n\nBạn có thể thêm lyrics thủ công; nội dung sẽ được đồng bộ vào Supabase.`;
