import { ref, watch } from 'vue';
import { authState } from '../store/appState';
import { createPlaylist as createRemotePlaylist, deletePlaylist as deleteRemotePlaylist, getPlaylists, updatePlaylist as updateRemotePlaylist } from '../services/api';

const PLAYLISTS_KEY = 'lunu_playlists_v2';
const legacyKey = 'lunu_playlists_v1';
const MIGRATION_KEY = 'lunu_playlists_db_migrated';

const normalizePlaylist = (playlist) => ({
  id: playlist.id,
  name: String(playlist.name || 'Playlist mới').trim(),
  description: String(playlist.description || '').trim(),
  songIds: Array.isArray(playlist.songIds) ? [...new Set(playlist.songIds)] : [],
  createdAt: playlist.createdAt || new Date().toISOString(),
  updatedAt: playlist.updatedAt || playlist.createdAt || new Date().toISOString(),
});

const readLocalPlaylists = () => {
  try {
    const current = JSON.parse(localStorage.getItem(PLAYLISTS_KEY));
    if (Array.isArray(current)) return current.map(normalizePlaylist);
    const legacy = JSON.parse(localStorage.getItem(legacyKey));
    return Array.isArray(legacy) ? legacy.map(normalizePlaylist) : [];
  } catch {
    localStorage.removeItem(PLAYLISTS_KEY);
    return [];
  }
};

const playlists = ref(readLocalPlaylists());
const activePlaylistId = ref(null);
const isLoading = ref(false);
const syncError = ref('');
let loadedForUserId = null;
let loadPromise = null;

const cachePlaylists = () => localStorage.setItem(PLAYLISTS_KEY, JSON.stringify(playlists.value));
watch(playlists, cachePlaylists, { deep: true });

const toRemotePayload = (playlist) => ({
  name: playlist.name,
  description: playlist.description || '',
  song_ids: playlist.songIds || [],
});

const replaceWithRemote = (items) => {
  playlists.value = (Array.isArray(items) ? items : []).map(normalizePlaylist);
  if (activePlaylistId.value && !playlists.value.some((item) => String(item.id) === String(activePlaylistId.value))) activePlaylistId.value = null;
};

const loadPlaylists = async (force = false) => {
  const userId = authState.user?.id;
  if (!userId || !authState.token) return;
  if (!force && loadedForUserId === String(userId)) return;
  if (loadPromise && !force) return loadPromise;
  isLoading.value = true;
  syncError.value = '';
  loadPromise = (async () => {
    try {
      const remote = await getPlaylists();
      const local = readLocalPlaylists();
      const shouldMigrate = local.length > 0 && localStorage.getItem(`${MIGRATION_KEY}:${userId}`) !== 'true';
      if (shouldMigrate) {
        const existingIds = new Set((remote || []).map((item) => String(item.id)));
        for (const playlist of local) {
          if (!existingIds.has(String(playlist.id))) {
            await createRemotePlaylist(toRemotePayload(playlist), playlist.id);
          }
        }
        localStorage.setItem(`${MIGRATION_KEY}:${userId}`, 'true');
        replaceWithRemote(await getPlaylists());
      } else {
        replaceWithRemote(remote);
      }
      loadedForUserId = String(userId);
    } catch (error) {
      syncError.value = error.message || 'Không thể đồng bộ playlist với máy chủ.';
      // Keep the cached list usable while the backend is unavailable.
    } finally {
      isLoading.value = false;
      loadPromise = null;
    }
  })();
  return loadPromise;
};

const runSync = async (operation) => {
  try {
    syncError.value = '';
    await operation();
  } catch (error) {
    syncError.value = error.message || 'Không thể lưu playlist lên máy chủ.';
  }
};

watch(() => authState.user?.id, (userId, previousUserId) => {
  if (String(userId || '') === String(previousUserId || '')) return;
  loadedForUserId = null;
  if (userId && authState.token) loadPlaylists(true);
  else replaceWithRemote([]);
});

export function usePlaylists() {
  if (authState.user?.id && loadedForUserId !== String(authState.user.id)) loadPlaylists();

  const createPlaylist = (name, description = '') => {
    const cleanName = String(name || '').trim();
    if (!cleanName) return null;
    const now = new Date().toISOString();
    const playlist = normalizePlaylist({ id: crypto.randomUUID?.() || `${Date.now()}`, name: cleanName, description, songIds: [], createdAt: now, updatedAt: now });
    playlists.value.unshift(playlist);
    if (authState.token) runSync(() => createRemotePlaylist(toRemotePayload(playlist), playlist.id).then((saved) => { if (saved) Object.assign(playlist, normalizePlaylist(saved)); }));
    return playlist;
  };

  const renamePlaylist = (id, name, description) => {
    const playlist = playlists.value.find((item) => String(item.id) === String(id));
    const cleanName = String(name || '').trim();
    if (!playlist || !cleanName) return false;
    playlist.name = cleanName;
    if (description !== undefined) playlist.description = String(description || '').trim();
    playlist.updatedAt = new Date().toISOString();
    if (authState.token) runSync(() => updateRemotePlaylist(playlist.id, toRemotePayload(playlist)));
    return true;
  };

  const deletePlaylist = (id) => {
    const index = playlists.value.findIndex((item) => String(item.id) === String(id));
    if (index < 0) return false;
    playlists.value.splice(index, 1);
    if (authState.token) runSync(() => deleteRemotePlaylist(id));
    return true;
  };

  const hasSong = (playlist, songId) => Boolean(playlist?.songIds?.some((id) => String(id) === String(songId)));
  const addSong = (playlistId, songId) => {
    const playlist = playlists.value.find((item) => String(item.id) === String(playlistId));
    if (!playlist || songId === undefined || hasSong(playlist, songId)) return false;
    playlist.songIds.push(songId);
    playlist.updatedAt = new Date().toISOString();
    if (authState.token) runSync(() => updateRemotePlaylist(playlist.id, toRemotePayload(playlist)));
    return true;
  };
  const removeSong = (playlistId, songId) => {
    const playlist = playlists.value.find((item) => String(item.id) === String(playlistId));
    if (!playlist) return false;
    const index = playlist.songIds.findIndex((id) => String(id) === String(songId));
    if (index < 0) return false;
    playlist.songIds.splice(index, 1);
    playlist.updatedAt = new Date().toISOString();
    if (authState.token) runSync(() => updateRemotePlaylist(playlist.id, toRemotePayload(playlist)));
    return true;
  };
  const getSongs = (playlist, library) => {
    const index = new Map((Array.isArray(library) ? library : []).map((song) => [String(song.id), song]));
    return (playlist?.songIds || []).map((id) => index.get(String(id))).filter(Boolean);
  };
  const selectPlaylist = (id) => { activePlaylistId.value = id || null; };
  return { playlists, activePlaylistId, isLoading, syncError, loadPlaylists, selectPlaylist, createPlaylist, renamePlaylist, deletePlaylist, addSong, removeSong, hasSong, getSongs };
}
