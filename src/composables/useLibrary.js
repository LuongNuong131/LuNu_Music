import { computed, ref } from 'vue';

const LIKES_KEY = 'lunu_liked_songs_v1';
const HISTORY_KEY = 'lunu_history_v1';
const read = (key, fallback) => {
  try { const value = JSON.parse(localStorage.getItem(key)); return Array.isArray(value) ? value : fallback; }
  catch (error) { localStorage.removeItem(key); return fallback; }
};

const likedIds = ref(read(LIKES_KEY, []));
const history = ref(read(HISTORY_KEY, []));
const lastRecorded = new Map();

const save = () => {
  localStorage.setItem(LIKES_KEY, JSON.stringify(likedIds.value));
  localStorage.setItem(HISTORY_KEY, JSON.stringify(history.value.slice(0, 100)));
};

export function useLibrary() {
  const isLiked = (songId) => likedIds.value.some((id) => String(id) === String(songId));
  const toggleLike = (song) => {
    if (!song) return false;
    const index = likedIds.value.findIndex((id) => String(id) === String(song.id));
    if (index >= 0) likedIds.value.splice(index, 1);
    else likedIds.value.unshift(song.id);
    save();
    return index < 0;
  };
  const recordPlay = (song, durationPlayed = 0, completionRate = 0) => {
    if (!song) return;
    const now = Date.now();
    const key = String(song.id);
    if (now - (lastRecorded.get(key) || 0) < 30_000) return;
    lastRecorded.set(key, now);
    history.value = [{ id: `${key}-${now}`, songId: song.id, song, playedAt: new Date(now).toISOString(), durationPlayed, completionRate }, ...history.value.filter((item) => String(item.songId) !== key)].slice(0, 100);
    save();
  };
  const removeHistory = (id) => { history.value = history.value.filter((item) => item.id !== id); save(); };
  const clearHistory = () => { history.value = []; save(); };
  return { likedIds, history, isLiked, toggleLike, recordPlay, removeHistory, clearHistory, likedCount: computed(() => likedIds.value.length) };
}
