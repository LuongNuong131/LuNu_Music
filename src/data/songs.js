import { reactive, ref } from 'vue';
import { getSongs } from '../services/api';

const songs = reactive([]);
export const songsLoading = ref(false);
export const songsError = ref('');

export const loadSongs = async () => {
  songsLoading.value = true;
  songsError.value = '';
  try {
    const data = await getSongs();
    songs.splice(0, songs.length, ...(Array.isArray(data) ? data : []));
    return songs;
  } catch (error) {
    songsError.value = error.message || 'Không thể tải thư viện nhạc.';
    console.error('Lỗi khi load danh sách nhạc từ API:', error);
    return songs;
  } finally {
    songsLoading.value = false;
  }
};

export default songs;
