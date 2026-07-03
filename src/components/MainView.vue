<!-- src/components/MainView.vue -->
<template>
  <div class="main-view">
    <div class="header">
      <h1>Danh sách bài hát</h1>
    </div>
    
    <div class="song-list">
      <div 
        class="song-item" 
        v-for="song in songs" 
        :key="song.id"
        @click="playSong(song)"
      >
        <div class="song-cover">
          <img :src="song.cover" :alt="song.title" />
          <div class="play-overlay">
            <span class="play-icon">▶</span>
          </div>
        </div>
        <div class="song-info">
          <h3>{{ song.title }}</h3>
          <p>{{ song.artist }}</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { songs } from '../data/songs.js';

// Khai báo sự kiện để bắn tín hiệu lên component cha (PlayerView)
const emit = defineEmits(['play-song']);

// Hàm xử lý khi click vào 1 bài hát
const playSong = (song) => {
  emit('play-song', song);
};
</script>

<style scoped>
.main-view {
  padding: 30px;
}

.header h1 {
  font-size: 28px;
  margin-bottom: 24px;
  font-weight: 800;
}

.song-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.song-item {
  display: flex;
  align-items: center;
  padding: 12px;
  border-radius: 8px;
  cursor: pointer;
  transition: background-color 0.3s ease;
}

.song-item:hover {
  background-color: rgba(255, 255, 255, 0.1);
}

.song-item:hover .play-overlay {
  opacity: 1;
}

.song-cover {
  position: relative;
  width: 50px;
  height: 50px;
  margin-right: 16px;
  border-radius: 6px;
  overflow: hidden;
  box-shadow: 0 4px 10px rgba(0,0,0,0.3);
}

.song-cover img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.play-overlay {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.6);
  display: flex;
  justify-content: center;
  align-items: center;
  opacity: 0;
  transition: opacity 0.3s ease;
}

.play-icon {
  color: white;
  font-size: 18px;
}

.song-info {
  flex: 1;
}

.song-info h3 {
  font-size: 16px;
  margin-bottom: 4px;
  color: #fff;
  font-weight: 600;
}

.song-info p {
  font-size: 14px;
  color: #b3b3b3;
}
</style>