import { computed, ref, watch } from 'vue';
import {
  createFallbackMessage,
  getLyricsInventory,
  getLyricsMode,
  getStoredLyrics,
  hasLyrics,
  isTimedLyrics,
  parseLyrics,
  resolveLyrics,
  saveLyrics,
} from '../services/lyricsService.js';

const statusCopy = {
  loading: 'Đang tìm lyrics',
  saving: 'Đang lưu lyrics',
  metadata: 'Lyrics từ metadata',
  manual: 'Lyrics đã lưu trên máy',
  found: 'Lyrics đã tìm thấy',
  unavailable: 'Chưa kết nối nguồn lyrics',
  'not-found': 'Chưa tìm thấy lyrics',
  error: 'Nguồn lyrics tạm thời lỗi',
  missing: 'Chưa có lyrics',
};

export const useLyrics = (songRef, options = {}) => {
  const record = ref({ content: '', source: 'none', offsetMs: 0, status: 'missing', mode: 'missing' });
  const isLoading = ref(false);
  const isSaving = ref(false);
  const error = ref('');
  let requestToken = 0;

  const content = computed(() => record.value.content || '');
  const mode = computed(() => record.value.mode || getLyricsMode(content.value));
  const offsetMs = computed(() => Number(record.value.offsetMs || 0));
  const lines = computed(() => parseLyrics(content.value, offsetMs.value));
  const isSynced = computed(() => mode.value === 'synced' || isTimedLyrics(content.value));
  const isPlain = computed(() => mode.value === 'plain');
  const isMissing = computed(() => !hasLyrics(content.value));
  const statusText = computed(() => statusCopy[record.value.status] || 'Lyrics');
  const fallbackMessage = computed(() => createFallbackMessage(songRef?.value));

  const load = async (song = songRef?.value, loadOptions = {}) => {
    if (!song) {
      record.value = { content: '', source: 'none', offsetMs: 0, status: 'missing', mode: 'missing' };
      return record.value;
    }
    const token = ++requestToken;
    isLoading.value = true;
    error.value = '';
    try {
      const result = await resolveLyrics(song, { allowProvider: loadOptions.allowProvider ?? options.allowProvider ?? false, signal: loadOptions.signal });
      if (token === requestToken) record.value = result;
    } catch (err) {
      if (token === requestToken && err?.name !== 'AbortError') {
        error.value = 'Không thể đọc lyrics lúc này.';
        record.value = { content: '', source: 'error', offsetMs: 0, status: 'error', mode: 'missing' };
      }
    } finally {
      if (token === requestToken) isLoading.value = false;
    }
    return record.value;
  };

  const save = async (lyrics, source = 'manual') => {
    const song = songRef?.value;
    if (!song) return null;
    isSaving.value = true;
    try {
      const next = saveLyrics(song.id, { content: lyrics, source, offsetMs: offsetMs.value });
      record.value = { ...next, status: source === 'manual' ? 'manual' : 'found', mode: getLyricsMode(next.content) };
      return record.value;
    } finally {
      isSaving.value = false;
    }
  };

  const setOffset = (nextOffset) => {
    const song = songRef?.value;
    if (!song) return;
    const safeOffset = Math.max(-5000, Math.min(5000, Math.round(Number(nextOffset) || 0)));
    const next = saveLyrics(song.id, { content: record.value.content, source: record.value.source || 'manual', offsetMs: safeOffset });
    record.value = { ...record.value, ...next, mode: getLyricsMode(next.content) };
  };
  const resetOffset = () => setOffset(0);
  const stepOffset = (delta) => setOffset(offsetMs.value + delta);
  const refreshStored = () => {
    const stored = getStoredLyrics(songRef?.value?.id);
    if (stored?.content) record.value = { ...stored, status: 'manual', mode: getLyricsMode(stored.content) };
  };

  watch(songRef, (song) => { load(song); }, { immediate: true });
  return { record, content, mode, offsetMs, lines, isSynced, isPlain, isMissing, statusText, fallbackMessage, isLoading, isSaving, error, load, save, setOffset, resetOffset, stepOffset, refreshStored };
};

export const getLibraryLyricsInventory = (songs) => getLyricsInventory(songs);
