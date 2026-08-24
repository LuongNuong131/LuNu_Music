import { ref, watch } from 'vue';
import songs from '../data/songs';

const PLAYLISTS_KEY = 'lunu_playlists_v1';
const readPlaylists = () => {
  try {
    const value = JSON.parse(localStorage.getItem(PLAYLISTS_KEY));
    return Array.isArray(value) ? value : [];
  } catch (error) {
    localStorage.removeItem(PLAYLISTS_KEY);
    return [];
  }
};

const playlists = ref(readPlaylists());
watch(playlists, (value) => localStorage.setItem(PLAYLISTS_KEY, JSON.stringify(value)), { deep: true });

export function usePlaylists() {
  const currentPlaylist = ref([...songs]);
  const createPlaylist = (name, description = '') => {
    const playlist = { id: crypto.randomUUID?.() || `${Date.now()}`, name: name.trim(), description, songIds: [], createdAt: new Date().toISOString() };
    playlists.value.push(playlist);
    return playlist;
  };
  return { playlists, currentPlaylist, createPlaylist };
}
