import { ref, computed } from 'vue';
import { songs } from '../data/songs.js';

export function usePlaylists() {
  const allPlaylists = computed(() => {
    const artistMap = {};

    songs.forEach(song => {
      // Lấy tên ca sĩ, nếu không có thì để "Unknown Artist"
      const artistName = song.artist || 'Unknown Artist';
      
      // Nếu ca sĩ này chưa có playlist thì tạo mới
      if (!artistMap[artistName]) {
        artistMap[artistName] = {
          id: `playlist-${artistName.replace(/\s+/g, '-').toLowerCase()}`,
          name: `Tuyển tập: ${artistName}`,
          artist: artistName,
          cover: song.cover || '/images/ChoCiu.jpg', // Tự động lấy cover của bài hát đầu tiên
          songs: []
        };
      }
      
      // Đẩy bài hát vào đúng playlist của ca sĩ đó
      artistMap[artistName].songs.push(song);
    });

    // Trả về mảng các playlist
    return Object.values(artistMap);
  });

  return {
    allPlaylists,
  };
}