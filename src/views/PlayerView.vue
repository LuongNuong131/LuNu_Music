<!-- src/views/PlayerView.vue -->
<template>
  <div class="player-layout">
    <!-- Nút mở menu — chỉ hiện trên mobile -->
    <button class="mobile-menu-btn" @click="sidebarOpen = true" aria-label="Mở menu">
      <span></span><span></span><span></span>
    </button>

    <!-- Lớp phủ tối khi mở drawer sidebar trên mobile -->
    <div v-if="sidebarOpen" class="sidebar-backdrop" @click="sidebarOpen = false"></div>

    <Sidebar
      class="sidebar-area"
      :open="sidebarOpen"
      :active-view="activeView"
      :active-playlist-id="activePlaylistId"
      @navigate="handleNavigate"
      @close="sidebarOpen = false"
    />
    <MainView
      class="main-area"
      :mode="activeView"
      :playlist-id="activePlaylistId"
      :current-song="currentSong"
      :is-playing="isPlaying"
      @play-song="handlePlaySong"
      @add-to-queue="handleAddToQueue"
    />
    <PlayerBar
      class="player-bar-area"
      :current-song="currentSong"
      :is-shuffle="isShuffle"
      :repeat-mode="repeatMode"
      @next="playNext"
      @prev="playPrev"
      @toggle-shuffle="toggleShuffle"
      @toggle-repeat="toggleRepeat"
      @toggle-queue="showQueue = !showQueue"
      @update:is-playing="value => (isPlaying = value)"
    />

    <QueuePanel
      :visible="showQueue"
      :current-song="currentSong"
      :queue="queue"
      @close="showQueue = false"
      @remove="removeFromQueue"
      @clear="queue = []"
    />
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue';
import Sidebar from '../components/Sidebar.vue';
import MainView from '../components/MainView.vue';
import PlayerBar from '../components/PlayerBar.vue';
import QueuePanel from '../components/QueuePanel.vue';
import CommandPalette from '../components/CommandPalette.vue';
import { songs } from '../data/songs.js';
import { usePlaylists } from '../composables/usePlaylists.js';

const { playlists } = usePlaylists();

const sidebarOpen = ref(false); // Trạng thái mở/đóng drawer sidebar trên mobile

const currentSong = ref(null);
const isPlaying = ref(false); // Trạng thái phát nhạc, dùng để hiển thị equalizer ở MainView
const isShuffle = ref(false); // Trạng thái Shuffle
const repeatMode = ref('off'); // 'off' | 'all' | 'one' — điều khiển hành vi khi hết bài / hết danh sách

const toggleRepeat = () => {
  repeatMode.value =
    repeatMode.value === 'off' ? 'all' : repeatMode.value === 'all' ? 'one' : 'off';
};

// Điều hướng nội bộ: Trang chủ / Tìm kiếm / 1 Playlist cụ thể
const activeView = ref('home'); // 'home' | 'search' | 'playlist'
const activePlaylistId = ref(null);

// Hàng đợi phát tiếp theo — người dùng chủ động thêm từ menu ⋯ trên mỗi bài hát.
// Có độ ưu tiên cao hơn logic shuffle/tuần tự khi bấm Next.
const queue = ref([]);
const showQueue = ref(false);

const playedTracks = ref([]); // Danh sách ID các bài đã phát (dùng cho shuffle)
const unplayedTracks = ref([]); // Danh sách ID các bài chưa phát (dùng cho shuffle)

// ===== Command Palette (Ctrl/Cmd + K) =====
const showCommandPalette = ref(false);

const handleGlobalKeydown = (e) => {
  const isCmdK = (e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k';
  if (isCmdK) {
    e.preventDefault(); // tránh trình duyệt mở ô tìm kiếm riêng của nó
    showCommandPalette.value = !showCommandPalette.value;
  } else if (e.key === 'Escape' && showCommandPalette.value) {
    showCommandPalette.value = false;
  }
};

onMounted(() => window.addEventListener('keydown', handleGlobalKeydown));
onUnmounted(() => window.removeEventListener('keydown', handleGlobalKeydown));

const handlePaletteAction = (action) => {
  if (action === 'home') handleNavigate({ view: 'home' });
  else if (action === 'search') handleNavigate({ view: 'search' });
  else if (action === 'toggle-shuffle') toggleShuffle();
  else if (action === 'toggle-queue') showQueue.value = !showQueue.value;
};

const handlePaletteOpenPlaylist = (playlist) => {
  handleNavigate({ view: 'playlist', playlistId: playlist.id });
};

const reorderQueue = ({ from, to }) => {
  const item = queue.value.splice(from, 1)[0];
  if (item) queue.value.splice(to, 0, item);
};

const handleNavigate = ({ view, playlistId = null }) => {
  activeView.value = view;
  activePlaylistId.value = playlistId;
  sidebarOpen.value = false; // Đóng drawer trên mobile sau khi chọn mục
};

const handleAddToQueue = (song) => {
  queue.value.push(song);
};

const removeFromQueue = (index) => {
  queue.value.splice(index, 1);
};

// Thuật toán xáo trộn mảng (Fisher-Yates)
const shuffleArray = (array) => {
  for (let i = array.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [array[i], array[j]] = [array[j], array[i]];
  }
};

// Khi người dùng chủ động chọn 1 bài hát bất kỳ từ danh sách
const handlePlaySong = (song) => {
  currentSong.value = song;
  if (isShuffle.value) {
    // Tái tạo lại danh sách xáo trộn (loại bỏ bài vừa chọn)
    unplayedTracks.value = songs.map(s => s.id).filter(id => id !== song.id);
    shuffleArray(unplayedTracks.value);
    playedTracks.value = []; // Reset lịch sử
  }
};

// Khi bật/tắt nút Shuffle
const toggleShuffle = () => {
  isShuffle.value = !isShuffle.value;
  if (isShuffle.value && currentSong.value) {
    // Lấy toàn bộ bài hát trừ bài đang hát và xáo trộn
    unplayedTracks.value = songs.map(s => s.id).filter(id => id !== currentSong.value.id);
    shuffleArray(unplayedTracks.value);
    playedTracks.value = [];
  } else {
    // Dọn dẹp mảng khi tắt
    unplayedTracks.value = [];
    playedTracks.value = [];
  }
};

const playNext = () => {
  if (!currentSong.value) return;

  // Hàng đợi thủ công luôn được ưu tiên phát trước
  if (queue.value.length > 0) {
    const nextSong = queue.value.shift();
    currentSong.value = nextSong;
    return;
  }

  if (isShuffle.value) {
    // Nếu đã phát hết bài chưa phát, xáo trộn lại một vòng mới
    if (unplayedTracks.value.length === 0) {
      unplayedTracks.value = songs.map(s => s.id).filter(id => id !== currentSong.value.id);
      shuffleArray(unplayedTracks.value);
      playedTracks.value = [];
    }

    // Rút 1 bài ngẫu nhiên để phát
    const nextId = unplayedTracks.value.pop();
    // Đưa bài hiện tại vào lịch sử
    playedTracks.value.push(currentSong.value.id);
    currentSong.value = songs.find(s => s.id === nextId);
  } else {
    // Logic tuần tự
    const currentIndex = songs.findIndex(s => s.id === currentSong.value.id);
    if (currentIndex < songs.length - 1) {
      currentSong.value = songs[currentIndex + 1];
    } else if (repeatMode.value !== 'off') {
      // Hết danh sách: chỉ quay lại bài đầu nếu đang bật Lặp lại (tất cả/1 bài)
      currentSong.value = songs[0];
    }
    // Nếu repeatMode === 'off' và đã ở bài cuối, không làm gì cả — audio đã tự dừng sau khi kết thúc
  }
};

const playPrev = () => {
  if (!currentSong.value) return;

  if (isShuffle.value) {
    // Lấy bài cũ nhất trong lịch sử ra nghe lại
    if (playedTracks.value.length > 0) {
      // Đẩy bài hiện tại về lại danh sách chưa phát
      unplayedTracks.value.push(currentSong.value.id);
      // Lấy bài vừa nghe ở quá khứ ra
      const prevId = playedTracks.value.pop();
      currentSong.value = songs.find(s => s.id === prevId);
    }
  } else {
    // Logic tuần tự
    const currentIndex = songs.findIndex(s => s.id === currentSong.value.id);
    currentSong.value = currentIndex > 0 ? songs[currentIndex - 1] : songs[songs.length - 1];
  }
};
</script>

<style scoped>
.player-layout {
  display: grid;
  grid-template-columns: 240px 1fr;
  grid-template-rows: calc(100vh - 90px) 90px;
  grid-template-areas: "sidebar main" "player player";
  background-color: var(--bg-color);
  color: var(--text-main);
}
.sidebar-area {
  grid-area: sidebar;
  background-color: #0a0908;
}
.main-area {
  grid-area: main;
  background:
    radial-gradient(120% 60% at 50% 0%, rgba(232, 184, 109, 0.06) 0%, transparent 55%),
    linear-gradient(180deg, #17140f 0%, var(--bg-color) 45%);
  overflow-y: auto;
  min-width: 0;
}
.player-bar-area {
  grid-area: player;
  background-color: var(--panel-bg);
  border-top: 1px solid var(--hairline);
  min-width: 0;
}

/* Nút hamburger mở drawer sidebar — mặc định ẩn, chỉ hiện ở mobile */
.mobile-menu-btn {
  display: none;
}

.sidebar-backdrop {
  display: none;
}

/* ===== Tablet: sidebar co lại thành dải icon ===== */
@media (max-width: 900px) {
  .player-layout {
    grid-template-columns: 76px 1fr;
  }
}

/* ===== Mobile: sidebar biến thành drawer trượt, main chiếm toàn bộ chiều rộng ===== */
@media (max-width: 640px) {
  .player-layout {
    grid-template-columns: 1fr;
    grid-template-rows: calc(100vh - 76px) 76px;
    grid-template-areas: "main" "player";
  }

  .mobile-menu-btn {
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    gap: 4px;
    position: fixed;
    top: 14px;
    left: 14px;
    z-index: 210;
    width: 38px;
    height: 38px;
    border-radius: 10px;
    border: 1px solid var(--hairline);
    background: rgba(23, 20, 15, 0.85);
    backdrop-filter: blur(6px);
    cursor: pointer;
  }

  .mobile-menu-btn span {
    display: block;
    width: 16px;
    height: 2px;
    border-radius: 1px;
    background: var(--text-main);
  }

  .sidebar-backdrop {
    display: block;
    position: fixed;
    inset: 0;
    z-index: 250;
    background: rgba(5, 4, 3, 0.55);
  }
}
</style>