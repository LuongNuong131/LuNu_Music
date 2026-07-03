<!-- src/components/PlayerBar.vue -->
<template>
  <div class="player-bar">
    <div class="song-info" v-if="currentSong">
      <img :src="currentSong.cover" class="cover-img" />
      <div class="details">
        <div class="title">{{ currentSong.title }}</div>
        <div class="artist">{{ currentSong.artist }}</div>
      </div>
    </div>

    <div class="player-controls">
      <div class="buttons">
        <!-- Nút Shuffle -->
        <button 
          class="control-btn" 
          :class="{ 'active': isShuffle }" 
          @click="emit('toggle-shuffle')"
        >🔀</button>
        <button class="control-btn" @click="emit('prev')" :disabled="!currentSong">⏮</button>
        <button class="play-btn" @click="togglePlay" :disabled="!currentSong">
          {{ isPlaying ? '⏸' : '▶' }}
        </button>
        <button class="control-btn" @click="emit('next')" :disabled="!currentSong">⏭</button>
      </div>
      
      <div class="progress-container">
        <span class="time">{{ formatTime(currentTime) }}</span>
        <input type="range" class="progress-bar" min="0" :max="duration || 0" v-model="currentTime" @input="seek" :disabled="!currentSong" />
        <span class="time">{{ formatTime(duration) }}</span>
      </div>
    </div>

    <div class="volume-control">
      <span>🔊</span>
      <input type="range" class="volume-bar" min="0" max="1" step="0.01" v-model="volume" @input="updateVolume" />
    </div>

    <audio ref="audioRef" :src="currentSong?.url" @timeupdate="onTimeUpdate" @loadedmetadata="onLoadedMetadata" @ended="onEnded"></audio>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue';

const props = defineProps({
  currentSong: Object,
  isShuffle: Boolean
});

const emit = defineEmits(['next', 'prev', 'toggle-shuffle']);
const audioRef = ref(null);
const isPlaying = ref(false);
const currentTime = ref(0);
const duration = ref(0);
const volume = ref(1);

watch(() => props.currentSong, () => {
  setTimeout(() => {
    audioRef.value.play();
    isPlaying.value = true;
  }, 50);
});

const togglePlay = () => {
  if (isPlaying.value) audioRef.value.pause();
  else audioRef.value.play();
  isPlaying.value = !isPlaying.value;
};

const onTimeUpdate = () => currentTime.value = audioRef.value.currentTime;
const onLoadedMetadata = () => duration.value = audioRef.value.duration;
const seek = () => audioRef.value.currentTime = currentTime.value;
const updateVolume = () => audioRef.value.volume = volume.value;
const onEnded = () => {
  isPlaying.value = false;
  emit('next'); 
};
const formatTime = (time) => {
  if (!time || isNaN(time)) return "0:00";
  const m = Math.floor(time / 60);
  const s = Math.floor(time % 60);
  return `${m}:${s < 10 ? '0' : ''}${s}`;
};
</script>

<style scoped>
.player-bar { display: flex; justify-content: space-between; align-items: center; padding: 0 16px; height: 100%; }
.song-info { display: flex; align-items: center; width: 30%; }
.cover-img { width: 50px; height: 50px; border-radius: 4px; margin-right: 15px; }
.player-controls { display: flex; flex-direction: column; align-items: center; width: 40%; }
.buttons { display: flex; align-items: center; gap: 20px; margin-bottom: 5px; }
.control-btn { background: none; border: none; color: #b3b3b3; font-size: 18px; cursor: pointer; }
.control-btn.active { color: #1db954; } /* Màu xanh khi bật shuffle */
.play-btn { width: 32px; height: 32px; border-radius: 50%; border: none; cursor: pointer; }
.progress-container { display: flex; align-items: center; width: 100%; gap: 10px; }
.time { font-size: 12px; color: #b3b3b3; }
.volume-control { width: 30%; display: flex; justify-content: flex-end; }
</style>