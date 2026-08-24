<template>
  <div class="main-view glass-panel">
    <h1 class="page-title">Khám Phá Âm Nhạc</h1>
    
    <div class="songs-grid">
      <div v-for="song in songs" :key="song.id" class="song-card">
        <div class="cover-wrapper">
          <img :src="song.cover" alt="Cover" class="song-cover" />
          <button class="play-btn" @click="handlePlay(song)">▶</button>
        </div>
        <div class="song-info">
          <h3 class="song-title">{{ song.title }}</h3>
          <p class="song-artist">{{ song.artist }}</p>
        </div>
      </div>
    </div>

    <div v-if="songs.length === 0" class="empty-state">
      <p>Hệ thống chưa có bài hát nào, hãy nhờ Admin tải thêm nhé!</p>
    </div>
  </div>
</template>

<script setup>
// ĐÃ FIX: Xóa bỏ ngoặc nhọn {} ở chữ songs
import songs from '../data/songs';

// Logic phát nhạc (Ông có thể link hàm này với Player store của ông)
const handlePlay = (song) => {
  console.log("Đang phát bài:", song.title);
  // Ví dụ: playSong(song);
};
</script>

<style scoped>
.main-view {
  padding: 24px;
  height: 100%;
  overflow-y: auto;
  box-sizing: border-box;
}

.glass-panel {
  background: rgba(255, 255, 255, 0.02);
  border-radius: 16px;
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.05);
}

.page-title {
  font-size: 2rem;
  margin-bottom: 24px;
  color: #fff;
  font-weight: 700;
  text-shadow: 0 2px 10px rgba(0,0,0,0.5);
}

.songs-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: 24px;
}

.song-card {
  background: rgba(0, 0, 0, 0.2);
  border-radius: 12px;
  padding: 16px;
  transition: all 0.3s ease;
  border: 1px solid rgba(255, 255, 255, 0.05);
}

.song-card:hover {
  background: rgba(255, 255, 255, 0.1);
  transform: translateY(-5px);
  box-shadow: 0 10px 20px rgba(0, 0, 0, 0.3);
}

.cover-wrapper {
  position: relative;
  width: 100%;
  aspect-ratio: 1 / 1;
  border-radius: 8px;
  overflow: hidden;
  margin-bottom: 16px;
  box-shadow: 0 4px 10px rgba(0,0,0,0.3);
}

.song-cover {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.play-btn {
  position: absolute;
  bottom: 10px;
  right: 10px;
  width: 45px;
  height: 45px;
  border-radius: 50%;
  background: #1db954;
  color: black;
  border: none;
  font-size: 1.2rem;
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0;
  transform: translateY(10px);
  transition: all 0.3s ease;
  cursor: pointer;
  box-shadow: 0 4px 10px rgba(0,0,0,0.3);
}

.song-card:hover .play-btn {
  opacity: 1;
  transform: translateY(0);
}

.play-btn:hover {
  transform: scale(1.05);
  background: #1ed760;
}

.song-title {
  color: #fff;
  font-size: 1rem;
  font-weight: 600;
  margin: 0 0 8px 0;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.song-artist {
  color: #b3b3b3;
  font-size: 0.875rem;
  margin: 0;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.empty-state {
  text-align: center;
  padding: 40px;
  color: #b3b3b3;
  font-size: 1.1rem;
}
</style>