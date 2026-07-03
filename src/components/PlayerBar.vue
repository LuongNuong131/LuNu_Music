<template>
  <div class="player-bar">
    <div class="song-info" v-if="currentSong">
      <img :src="currentSong.cover" :alt="currentSong.title" class="cover-img" />
      <div class="details">
        <div class="title">{{ currentSong.title }}</div>
        <div class="artist">{{ currentSong.artist }}</div>
      </div>
    </div>
    <div class="song-info" v-else>
      <div class="details">
        <div class="title">Chưa chọn bài hát</div>
      </div>
    </div>

    <div class="player-controls">
      <div class="buttons">
        <button class="control-btn" @click="emit('prev')" :disabled="!currentSong">⏮</button>
        <button class="play-btn" @click="togglePlay" :disabled="!currentSong">
          {{ isPlaying ? '⏸' : '▶' }}
        </button>
        <button class="control-btn" @click="emit('next')" :disabled="!currentSong">⏭</button>
      </div>
      
      <div class="progress-container">
        <span class="time">{{ formatTime(currentTime) }}</span>
        <input 
          type="range" 
          class="progress-bar" 
          min="0" 
          :max="duration || 0" 
          v-model="currentTime" 
          @input="seek"
          :disabled="!currentSong"
        />
        <span class="time">{{ formatTime(duration) }}</span>
      </div>
    </div>

    <div class="volume-control">
      <span class="volume-icon">🔊</span>
      <input 
        type="range" 
        class="volume-bar" 
        min="0" 
        max="1" 
        step="0.01" 
        v-model="volume" 
        @input="updateVolume"
      />
    </div>

    <audio 
      ref="audioRef" 
      :src="currentSong?.url" 
      @timeupdate="onTimeUpdate" 
      @loadedmetadata="onLoadedMetadata"
      @ended="onEnded"
    ></audio>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue';

const props = defineProps({
  currentSong: Object
});

// Khai báo emit để bắn tín hiệu Next/Prev lên PlayerView
const emit = defineEmits(['next', 'prev']);

const audioRef = ref(null);
const isPlaying = ref(false);
const currentTime = ref(0);
const duration = ref(0);
const volume = ref(1);

watch(() => props.currentSong, (newSong) => {
  if (newSong) {
    setTimeout(() => {
      audioRef.value.play();
      isPlaying.value = true;
    }, 50);
  }
});

const togglePlay = () => {
  if (!audioRef.value || !props.currentSong) return;
  
  if (isPlaying.value) {
    audioRef.value.pause();
  } else {
    audioRef.value.play();
  }
  isPlaying.value = !isPlaying.value;
};

const onTimeUpdate = () => {
  currentTime.value = audioRef.value.currentTime;
};

const onLoadedMetadata = () => {
  duration.value = audioRef.value.duration;
};

const seek = () => {
  audioRef.value.currentTime = currentTime.value;
};

const updateVolume = () => {
  if (audioRef.value) {
    audioRef.value.volume = volume.value;
  }
};

// Cập nhật lại sự kiện khi hết bài: reset thời gian và tự động Next
const onEnded = () => {
  isPlaying.value = false;
  currentTime.value = 0;
  emit('next'); 
};

const formatTime = (time) => {
  if (!time || isNaN(time)) return "0:00";
  const minutes = Math.floor(time / 60);
  const seconds = Math.floor(time % 60);
  return `${minutes}:${seconds < 10 ? '0' : ''}${seconds}`;
};
</script>

<style scoped>
.player-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 16px;
  height: 100%;
}

.song-info {
  display: flex;
  align-items: center;
  width: 30%;
  min-width: 180px;
}

.cover-img {
  width: 56px;
  height: 56px;
  border-radius: 4px;
  margin-right: 14px;
  object-fit: cover;
  box-shadow: 0 4px 6px rgba(0,0,0,0.3);
}

.details {
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.title {
  font-size: 14px;
  font-weight: 600;
  color: #fff;
  margin-bottom: 4px;
}

.artist {
  font-size: 12px;
  color: #b3b3b3;
}

.player-controls {
  display: flex;
  flex-direction: column;
  align-items: center;
  width: 40%;
  max-width: 722px;
}

.buttons {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 8px;
}

.control-btn {
  background: none;
  border: none;
  color: #b3b3b3;
  font-size: 16px;
  cursor: pointer;
  transition: color 0.2s;
}

.control-btn:hover:not(:disabled) {
  color: #fff;
}

.control-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.play-btn {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background-color: #fff;
  color: #000;
  border: none;
  display: flex;
  justify-content: center;
  align-items: center;
  font-size: 16px;
  cursor: pointer;
  transition: transform 0.1s ease;
}

.play-btn:hover:not(:disabled) {
  transform: scale(1.05);
}

.play-btn:disabled {
  background-color: #b3b3b3;
  cursor: not-allowed;
  transform: none;
}

.progress-container {
  display: flex;
  align-items: center;
  width: 100%;
  gap: 8px;
}

.time {
  font-size: 11px;
  color: #b3b3b3;
  min-width: 40px;
  text-align: center;
}

.volume-control {
  display: flex;
  align-items: center;
  width: 30%;
  justify-content: flex-end;
  gap: 8px;
}

.volume-icon {
  color: #b3b3b3;
  font-size: 14px;
}

input[type=range] {
  -webkit-appearance: none;
  background: #4d4d4d;
  height: 4px;
  border-radius: 2px;
  outline: none;
  transition: background 0.3s;
}

input[type=range]:hover:not(:disabled) {
  background: #1db954; 
}

input[type=range]::-webkit-slider-thumb {
  -webkit-appearance: none;
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background: #fff;
  cursor: pointer;
  opacity: 0; 
  transition: opacity 0.2s;
}

input[type=range]:hover:not(:disabled)::-webkit-slider-thumb {
  opacity: 1; 
}

input[type=range]:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.progress-bar {
  flex: 1;
}

.volume-bar {
  width: 100px;
}
</style>