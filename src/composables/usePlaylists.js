import { ref, computed } from 'vue';
import songs from '../data/songs';

export function usePlaylists() {
  const playlists = ref([]);
  const currentPlaylist = ref(songs);

  return {
    playlists,
    currentPlaylist
  };
}