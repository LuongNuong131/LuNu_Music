<!-- src/views/PlayerView.vue -->
<template>
  <div class="player-layout">
    <Sidebar class="sidebar-area" />
    <MainView class="main-area" @play-song="handlePlaySong" />
    <PlayerBar 
      class="player-bar-area" 
      :current-song="currentSong" 
      :is-shuffle="isShuffle"
      @next="playNext"
      @prev="playPrev"
      @toggle-shuffle="isShuffle = !isShuffle"
    />
  </div>
</template>

<script setup>
import { ref } from 'vue';
import Sidebar from '../components/Sidebar.vue';
import MainView from '../components/MainView.vue';
import PlayerBar from '../components/PlayerBar.vue';
import { songs } from '../data/songs.js';

const currentSong = ref(null);
const isShuffle = ref(false); // Trạng thái Shuffle

const handlePlaySong = (song) => {
  currentSong.value = song;
};

const playNext = () => {
  if (!currentSong.value) return;
  
  if (isShuffle.value) {
    // Phát ngẫu nhiên: Chọn 1 bài bất kỳ khác bài hiện tại
    let nextIndex;
    do {
      nextIndex = Math.floor(Math.random() * songs.length);
    } while (songs[nextIndex].id === currentSong.value.id && songs.length > 1);
    currentSong.value = songs[nextIndex];
  } else {
    // Phát theo thứ tự
    const currentIndex = songs.findIndex(s => s.id === currentSong.value.id);
    currentSong.value = currentIndex < songs.length - 1 ? songs[currentIndex + 1] : songs[0];
  }
};

const playPrev = () => {
  if (!currentSong.value) return;
  
  const currentIndex = songs.findIndex(s => s.id === currentSong.value.id);
  currentSong.value = currentIndex > 0 ? songs[currentIndex - 1] : songs[songs.length - 1];
};
</script>

<style scoped>
.player-layout {
  display: grid;
  grid-template-columns: 240px 1fr; 
  grid-template-rows: calc(100vh - 90px) 90px; 
  grid-template-areas: "sidebar main" "player player";
  background-color: #121212;
  color: #fff;
}
.sidebar-area { grid-area: sidebar; background-color: #000; }
.main-area { grid-area: main; background: linear-gradient(180deg, #2a2a2a 0%, #121212 100%); overflow-y: auto; }
.player-bar-area { grid-area: player; background-color: #181818; border-top: 1px solid #282828; }
</style>