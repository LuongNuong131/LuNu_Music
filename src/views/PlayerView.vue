<template>
  <div class="player-layout">
    <Sidebar class="sidebar-area" />

    <MainView class="main-area" @play-song="handlePlaySong" />

    <PlayerBar 
      class="player-bar-area" 
      :current-song="currentSong" 
      @next="playNext"
      @prev="playPrev"
    />
  </div>
</template>

<script setup>
import { ref } from 'vue';
import Sidebar from '../components/Sidebar.vue';
import MainView from '../components/MainView.vue';
import PlayerBar from '../components/PlayerBar.vue';
import { songs } from '../data/songs.js'; // Import data để lấy index chuyển bài

// State lưu trữ bài hát đang phát
const currentSong = ref(null);

// Hàm nhận sự kiện play nhạc từ MainView
const handlePlaySong = (song) => {
  currentSong.value = song;
};

// Hàm xử lý chuyển bài tiếp theo (Next)
const playNext = () => {
  if (!currentSong.value) return;
  
  const currentIndex = songs.findIndex(s => s.id === currentSong.value.id);
  
  // Nếu chưa phải bài cuối cùng thì nhảy sang bài kế tiếp
  if (currentIndex < songs.length - 1) {
    currentSong.value = songs[currentIndex + 1];
  } else {
    // Nếu là bài cuối cùng thì vòng lại bài đầu tiên
    currentSong.value = songs[0];
  }
};

// Hàm xử lý lùi bài (Prev)
const playPrev = () => {
  if (!currentSong.value) return;
  
  const currentIndex = songs.findIndex(s => s.id === currentSong.value.id);
  
  // Nếu chưa phải bài đầu tiên thì lùi lại 1 bài
  if (currentIndex > 0) {
    currentSong.value = songs[currentIndex - 1];
  } else {
    // Nếu đang ở bài đầu mà bấm lùi thì nhảy xuống bài cuối cùng
    currentSong.value = songs[songs.length - 1];
  }
};
</script>

<style scoped>
.player-layout {
  display: grid;
  grid-template-columns: 240px 1fr; 
  grid-template-rows: calc(100vh - 90px) 90px; 
  grid-template-areas:
    "sidebar main"
    "player player";
  background-color: #121212;
  color: #fff;
}

.sidebar-area {
  grid-area: sidebar;
  background-color: #000000;
}

.main-area {
  grid-area: main;
  background: linear-gradient(180deg, #2a2a2a 0%, #121212 100%);
  overflow-y: auto;
}

.player-bar-area {
  grid-area: player;
  background-color: #181818;
  border-top: 1px solid #282828;
}
</style>