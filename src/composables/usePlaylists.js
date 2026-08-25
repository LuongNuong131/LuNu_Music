import { ref, watch } from 'vue';

const PLAYLISTS_KEY = 'lunu_playlists_v2';
const legacyKey = 'lunu_playlists_v1';

const readPlaylists = () => {
  try {
    const current = JSON.parse(localStorage.getItem(PLAYLISTS_KEY));
    if (Array.isArray(current)) return current;
    const legacy = JSON.parse(localStorage.getItem(legacyKey));
    return Array.isArray(legacy) ? legacy : [];
  } catch (error) {
    localStorage.removeItem(PLAYLISTS_KEY);
    return [];
  }
};

const playlists = ref(readPlaylists().map((playlist) => ({
  id: playlist.id,
  name: String(playlist.name || 'Playlist mới').trim(),
  description: String(playlist.description || ''),
  songIds: Array.isArray(playlist.songIds) ? [...new Set(playlist.songIds)] : [],
  createdAt: playlist.createdAt || new Date().toISOString(),
  updatedAt: playlist.updatedAt || playlist.createdAt || new Date().toISOString(),
})));

watch(playlists, (value) => localStorage.setItem(PLAYLISTS_KEY, JSON.stringify(value)), { deep: true });
const activePlaylistId = ref(null);

const touch = (playlist) => { playlist.updatedAt = new Date().toISOString(); };

export function usePlaylists() {
  const createPlaylist = (name, description = '') => {
    const cleanName = String(name || '').trim();
    if (!cleanName) return null;
    const now = new Date().toISOString();
    const playlist = { id: crypto.randomUUID?.() || `${Date.now()}`, name: cleanName, description: String(description || '').trim(), songIds: [], createdAt: now, updatedAt: now };
    playlists.value.unshift(playlist);
    return playlist;
  };

  const renamePlaylist = (id, name, description) => {
    const playlist = playlists.value.find((item) => String(item.id) === String(id));
    const cleanName = String(name || '').trim();
    if (!playlist || !cleanName) return false;
    playlist.name = cleanName;
    if (description !== undefined) playlist.description = String(description || '').trim();
    touch(playlist);
    return true;
  };

  const deletePlaylist = (id) => {
    const index = playlists.value.findIndex((item) => String(item.id) === String(id));
    if (index < 0) return false;
    playlists.value.splice(index, 1);
    return true;
  };

  const hasSong = (playlist, songId) => Boolean(playlist?.songIds?.some((id) => String(id) === String(songId)));
  const addSong = (playlistId, songId) => {
    const playlist = playlists.value.find((item) => String(item.id) === String(playlistId));
    if (!playlist || songId === undefined || hasSong(playlist, songId)) return false;
    playlist.songIds.push(songId);
    touch(playlist);
    return true;
  };
  const removeSong = (playlistId, songId) => {
    const playlist = playlists.value.find((item) => String(item.id) === String(playlistId));
    if (!playlist) return false;
    const index = playlist.songIds.findIndex((id) => String(id) === String(songId));
    if (index < 0) return false;
    playlist.songIds.splice(index, 1);
    touch(playlist);
    return true;
  };
  const getSongs = (playlist, library) => {
    const source = Array.isArray(library) ? library : [];
    const index = new Map(source.map((song) => [String(song.id), song]));
    return (playlist?.songIds || []).map((id) => index.get(String(id))).filter(Boolean);
  };

  const selectPlaylist = (id) => { activePlaylistId.value = id || null; };
  return { playlists, activePlaylistId, selectPlaylist, createPlaylist, renamePlaylist, deletePlaylist, addSong, removeSong, hasSong, getSongs };
}
