<template>
  <div class="player-view-container">
    <div class="glass-player-box">
      <!-- Khu vực hiển thị đĩa than / ảnh bìa -->
      <div class="vinyl-wrapper" :class="{ 'is-playing': isPlaying }">
        <div class="vinyl-record">
          <img 
            :src="currentSong.cover || '/images/ChoCiu.jpg'" 
            alt="Album Art" 
            class="cover-image" 
          />
          <div class="vinyl-hole"></div>
        </div>
      </div>

      <!-- Thông tin bài hát -->
      <div class="song-info">
        <h2 class="song-title">{{ currentSong.title || 'Chưa có bài hát nào' }}</h2>
        <p class="song-artist">{{ currentSong.artist || 'Đang cập nhật...' }}</p>
      </div>

      <!-- Bảng điều khiển -->
      <div class="controls-wrapper">
        <button class="control-btn side-btn" @click="prevSong" :disabled="songsList.length === 0">
          <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="19 20 9 12 19 4 19 20"></polygon><line x1="5" y1="19" x2="5" y2="5"></line></svg>
        </button>
        
        <button class="control-btn play-btn" @click="togglePlay" :disabled="songsList.length === 0">
          <svg v-if="!isPlaying" xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="5 3 19 12 5 21 5 3"></polygon></svg>
          <svg v-else xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="6" y="4" width="4" height="16"></rect><rect x="14" y="4" width="4" height="16"></rect></svg>
        </button>
        
        <button class="control-btn side-btn" @click="nextSong" :disabled="songsList.length === 0">
          <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="5 4 15 12 5 20 5 4"></polygon><line x1="19" y1="5" x2="19" y2="19"></line></svg>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue';

// ĐÃ FIX DỨT ĐIỂM: Xóa dấu ngoặc nhọn {} ở chữ songs
import songs from '../data/songs'; 

// State giả lập cho UI (Nếu ông dùng Store chung thì map state vào đây)
const songsList = computed(() => songs);
const isPlaying = ref(false);
const currentIndex = ref(0);

const currentSong = computed(() => {
  return songsList.value.length > 0 ? songsList.value[currentIndex.value] : {};
});

// Các hàm điều khiển cơ bản
const togglePlay = () => {
  if (songsList.value.length === 0) return;
  isPlaying.value = !isPlaying.value;
  // TODO: Thêm logic play/pause thẻ <audio> thực tế của ông vào đây
};

const prevSong = () => {
  if (songsList.value.length === 0) return;
  currentIndex.value = (currentIndex.value - 1 + songsList.value.length) % songsList.value.length;
  isPlaying.value = true;
};

const nextSong = () => {
  if (songsList.value.length === 0) return;
  currentIndex.value = (currentIndex.value + 1) % songsList.value.length;
  isPlaying.value = true;
};
</script>

<style scoped>
.player-view-container {
  display: flex;
  justify-content: center;
  align-items: center;
  width: 100%;
  height: 100%;
  padding: 20px;
  box-sizing: border-box;
}

.glass-player-box {
  width: 100%;
  max-width: 450px;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 30px;
  padding: 40px 30px;
  backdrop-filter: blur(25px);
  -webkit-backdrop-filter: blur(25px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  box-shadow: 0 20px 50px rgba(0, 0, 0, 0.5);
  display: flex;
  flex-direction: column;
  align-items: center;
}

/* Vinyl Record Animation */
.vinyl-wrapper {
  width: 220px;
  height: 220px;
  margin-bottom: 30px;
  border-radius: 50%;
  padding: 10px;
  background: linear-gradient(145deg, rgba(255,255,255,0.1), rgba(0,0,0,0.4));
  box-shadow: 0 10px 30px rgba(0,0,0,0.5), inset 0 2px 5px rgba(255,255,255,0.2);
  transition: transform 0.3s ease;
}

.vinyl-record {
  width: 100%;
  height: 100%;
  border-radius: 50%;
  background: #111;
  position: relative;
  display: flex;
  justify-content: center;
  align-items: center;
  overflow: hidden;
  box-shadow: inset 0 0 20px rgba(255,255,255,0.2);
}

/* Rãnh đĩa than */
.vinyl-record::before {
  content: '';
  position: absolute;
  width: 180px;
  height: 180px;
  border-radius: 50%;
  border: 1px solid rgba(255,255,255,0.05);
}

.vinyl-record::after {
  content: '';
  position: absolute;
  width: 140px;
  height: 140px;
  border-radius: 50%;
  border: 1px solid rgba(255,255,255,0.05);
}

.cover-image {
  width: 90px;
  height: 90px;
  border-radius: 50%;
  object-fit: cover;
  z-index: 2;
  box-shadow: 0 0 15px rgba(0,0,0,0.8);
}

.vinyl-hole {
  position: absolute;
  width: 15px;
  height: 15px;
  background: #0a0a0a;
  border-radius: 50%;
  z-index: 3;
  border: 2px solid rgba(255,255,255,0.2);
}

/* Quay đĩa khi đang Play */
@keyframes spin {
  100% { transform: rotate(360deg); }
}

.is-playing .vinyl-record {
  animation: spin 6s linear infinite;
}

/* Info */
.song-info {
  text-align: center;
  margin-bottom: 30px;
  width: 100%;
}

.song-title {
  font-size: 1.5rem;
  font-weight: 700;
  color: #fff;
  margin: 0 0 8px 0;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  text-shadow: 0 2px 4px rgba(0,0,0,0.5);
}

.song-artist {
  font-size: 1rem;
  color: #1db954;
  margin: 0;
  opacity: 0.9;
}

/* Controls */
.controls-wrapper {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 25px;
  width: 100%;
}

.control-btn {
  background: transparent;
  border: none;
  cursor: pointer;
  display: flex;
  justify-content: center;
  align-items: center;
  transition: all 0.3s ease;
}

.control-btn:disabled {
  opacity: 0.3;
  cursor: not-allowed;
}

.side-btn {
  color: rgba(255,255,255,0.7);
}

.side-btn:hover:not(:disabled) {
  color: #fff;
  transform: scale(1.1);
}

.play-btn {
  width: 70px;
  height: 70px;
  border-radius: 50%;
  background: #1db954;
  color: #000;
  box-shadow: 0 5px 20px rgba(29, 185, 84, 0.4);
}

.play-btn:hover:not(:disabled) {
  background: #1ed760;
  transform: scale(1.05);
  box-shadow: 0 8px 25px rgba(29, 185, 84, 0.6);
}
</style>