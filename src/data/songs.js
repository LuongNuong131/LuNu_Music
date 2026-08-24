import { reactive, ref } from 'vue';
import { getSongs } from '../services/api';
import legacyCatalog from './legacyCatalog.js';

const songs = reactive([]);
export const songsLoading = ref(false);
export const songsError = ref('');

export const loadSongs = async () => {
  songsLoading.value = true;
  songsError.value = '';
  try {
    const data = await getSongs();
    const remoteSongs = Array.isArray(data) ? data : [];
    const source = remoteSongs.length ? remoteSongs : legacyCatalog;
    songs.splice(0, songs.length, ...source);
    return songs;
  } catch (error) {
    songsError.value = error.message || 'Không thể tải thư viện nhạc từ máy chủ.';
    songs.splice(0, songs.length, ...legacyCatalog);
    console.error('Lỗi khi load danh sách nhạc từ API, dùng catalog dự phòng:', error);
    return songs;
  } finally {
    songsLoading.value = false;
  }
};

export default songs;
