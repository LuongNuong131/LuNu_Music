import { reactive } from 'vue';
import { getSongs } from '../services/api';

const songs = reactive([]);

export const loadSongs = async () => {
  try {
    const data = await getSongs();
    songs.splice(0, songs.length, ...data);
  } catch (error) {
    console.error("Lỗi khi load danh sách nhạc từ API:", error);
  }
};

export default songs;