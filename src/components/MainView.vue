<!-- src/components/MainView.vue -->
<template>
  <div class="main-view">
    <!-- ===================== HERO / HEADER theo từng mode ===================== -->
    <header class="hero" v-if="mode === 'home'">
      <p class="eyebrow">LuNu Music &middot; Bảng xếp hạng nội bộ</p>
      <h1 class="hero-title">Danh sách <span class="accent">bài hát</span></h1>
      <p class="hero-sub">{{ songs.length }} track &middot; tuyển chọn từ label</p>
    </header>

    <header class="hero" v-else-if="mode === 'search'">
      <p class="eyebrow">Tìm kiếm</p>
      <h1 class="hero-title">Tìm <span class="accent">bài hát</span></h1>
      <div class="search-box">
        <span class="search-icon">⌕</span>
        <input
          v-model="searchQuery"
          type="text"
          placeholder="Tìm theo tên bài hát hoặc nghệ sĩ..."
          autofocus
        />
        <button v-if="searchQuery" class="clear-search" @click="searchQuery = ''">✕</button>
      </div>
      <p class="hero-sub search-count">
        {{ searchQuery ? `${displayedSongs.length} kết quả cho "${searchQuery}"` : `${songs.length} track · gõ để lọc` }}
      </p>
    </header>

    <header class="hero" v-else-if="mode === 'playlist'">
      <p class="eyebrow">Playlist</p>
      <h1 class="hero-title">{{ activePlaylist ? activePlaylist.name : 'Playlist' }}</h1>
      <p class="hero-sub">{{ displayedSongs.length }} bài hát &middot; lưu trên máy này</p>
    </header>

    <!-- ===================== DANH SÁCH BÀI HÁT ===================== -->
    <div class="song-list" v-if="displayedSongs.length">
      <div class="list-head">
        <span class="col-index">#</span>
        <span class="col-title">Bài hát</span>
        <span class="col-artist">Nghệ sĩ</span>
        <span class="col-actions"></span>
      </div>

      <div
        v-for="(song, index) in displayedSongs"
        :key="song.id"
        class="song-item"
        :class="{ 'is-active': currentSong && currentSong.id === song.id }"
        @click="playSong(song)"
      >
        <div class="col-index">
          <span class="index-num">{{ String(index + 1).padStart(2, '0') }}</span>
          <span class="index-play">▶</span>
          <span class="eq" v-if="currentSong && currentSong.id === song.id && isPlaying">
            <i></i><i></i><i></i>
          </span>
        </div>

        <div class="col-title">
          <div class="song-cover">
            <img :src="song.cover" :alt="song.title" loading="lazy" />
          </div>
          <div class="song-info">
            <h3>{{ song.title }}</h3>
          </div>
        </div>

        <div class="col-artist">{{ song.artist }}</div>

        <div class="col-actions">
          <button
            class="menu-btn"
            :class="{ 'is-open': openMenuId === song.id }"
            @click.stop="toggleMenu(song.id)"
            title="Tuỳ chọn"
          >⋯</button>

          <div v-if="openMenuId === song.id" class="song-menu" @click.stop>
            <button class="menu-item" @click="handleAddToQueue(song)">
              <span class="mi-icon">▤</span> Thêm vào hàng đợi
            </button>

            <button
              v-if="mode === 'playlist'"
              class="menu-item danger"
              @click="handleRemoveFromPlaylist(song)"
            >
              <span class="mi-icon">✕</span> Xoá khỏi playlist này
            </button>

            <div class="menu-divider" v-if="playlists.length"></div>
            <p class="menu-label" v-if="playlists.length">Thêm vào playlist</p>

            <button
              v-for="pl in playlists"
              :key="pl.id"
              class="menu-item"
              @click="handleAddToPlaylist(pl, song)"
            >
              <span class="mi-icon">{{ isSongInPlaylist(pl.id, song.id) ? '✓' : '＋' }}</span>
              {{ pl.name }}
            </button>

            <div class="menu-divider"></div>
            <button class="menu-item accent" @click="handleCreateAndAdd(song)">
              <span class="mi-icon">＋</span> Playlist mới...
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- ===================== EMPTY STATES ===================== -->
    <div class="empty-state" v-else-if="mode === 'search'">
      <p class="empty-title">Không tìm thấy "{{ searchQuery }}"</p>
      <p class="empty-sub">Thử từ khoá khác xem sao.</p>
    </div>
    <div class="empty-state" v-else-if="mode === 'playlist'">
      <p class="empty-title">Playlist đang trống</p>
      <p class="empty-sub">Qua Trang chủ, bấm ⋯ trên một bài hát rồi chọn playlist này để thêm vào.</p>
    </div>
    <!-- Tạo playlist mới ngay từ menu ⋯ của 1 bài hát -->
    <ConfirmModal
      :visible="showCreateModal"
      mode="prompt"
      title="Playlist mới"
      :message="pendingSong ? `Sẽ thêm luôn '${pendingSong.title}' vào playlist này.` : ''"
      placeholder="VD: Nhạc cày view, Đi cà phê..."
      confirm-label="Tạo"
      @confirm="handleConfirmCreate"
      @cancel="closeCreateModal"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue';
import { songs } from '../data/songs.js';
import { usePlaylists } from '../composables/usePlaylists.js';
import { useToast } from '../composables/useToast.js';
import ConfirmModal from './ConfirmModal.vue';

const props = defineProps({
  mode: { type: String, default: 'home' }, // 'home' | 'search' | 'playlist'
  playlistId: { type: String, default: null },
  currentSong: { type: Object, default: null },
  isPlaying: { type: Boolean, default: false }
});

const emit = defineEmits(['play-song', 'add-to-queue']);

const { playlists, createPlaylist, addSongToPlaylist, removeSongFromPlaylist, isSongInPlaylist } = usePlaylists();
const { showToast } = useToast();

const searchQuery = ref('');
const openMenuId = ref(null);
const showCreateModal = ref(false);
const pendingSong = ref(null);

// Bỏ dấu tiếng Việt để tìm kiếm không cần gõ chính xác dấu
const normalize = (str) =>
  (str || '')
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .replace(/đ/gi, 'd')
    .toLowerCase();

const activePlaylist = computed(() => playlists.value.find((p) => p.id === props.playlistId) || null);

const displayedSongs = computed(() => {
  if (props.mode === 'search') {
    const q = normalize(searchQuery.value.trim());
    if (!q) return songs;
    return songs.filter((s) => normalize(s.title).includes(q) || normalize(s.artist).includes(q));
  }
  if (props.mode === 'playlist') {
    if (!activePlaylist.value) return [];
    return activePlaylist.value.songIds
      .map((id) => songs.find((s) => s.id === id))
      .filter(Boolean);
  }
  return songs;
});

const playSong = (song) => emit('play-song', song);

const toggleMenu = (songId) => {
  openMenuId.value = openMenuId.value === songId ? null : songId;
};

const handleAddToQueue = (song) => {
  emit('add-to-queue', song);
  openMenuId.value = null;
  showToast(`Đã thêm "${song.title}" vào hàng đợi`, { type: 'success' });
};

const handleAddToPlaylist = (playlist, song) => {
  addSongToPlaylist(playlist.id, song.id);
  openMenuId.value = null;
  showToast(`Đã thêm vào playlist "${playlist.name}"`, { type: 'success' });
};

const handleRemoveFromPlaylist = (song) => {
  if (props.playlistId) removeSongFromPlaylist(props.playlistId, song.id);
  openMenuId.value = null;
  showToast(`Đã xoá "${song.title}" khỏi playlist`);
};

const handleCreateAndAdd = (song) => {
  pendingSong.value = song;
  showCreateModal.value = true;
  openMenuId.value = null;
};

const handleConfirmCreate = (name) => {
  const playlist = createPlaylist(name);
  if (pendingSong.value) addSongToPlaylist(playlist.id, pendingSong.value.id);
  showToast(`Đã tạo playlist "${playlist.name}"`, { type: 'success' });
  closeCreateModal();
};

const closeCreateModal = () => {
  showCreateModal.value = false;
  pendingSong.value = null;
};

// Click ra ngoài (mọi click không bị .stop từ nút menu / bên trong menu) sẽ tự đóng menu đang mở
const closeMenuOnOutsideClick = () => {
  openMenuId.value = null;
};

onMounted(() => document.addEventListener('click', closeMenuOnOutsideClick));
onUnmounted(() => document.removeEventListener('click', closeMenuOnOutsideClick));
</script>

<style scoped>
.main-view {
  padding: 32px 36px 40px;
}

.hero {
  margin-bottom: 32px;
  padding-bottom: 24px;
  border-bottom: 1px solid var(--hairline-soft);
}

.eyebrow {
  font-family: var(--font-mono);
  font-size: 11px;
  letter-spacing: 2px;
  text-transform: uppercase;
  color: var(--gold-dim);
  margin-bottom: 10px;
}

.hero-title {
  font-family: var(--font-display);
  font-size: 44px;
  font-weight: 400;
  letter-spacing: 0.5px;
  line-height: 1;
  color: var(--text-main);
}

.hero-title .accent {
  background: linear-gradient(135deg, var(--gold-bright), var(--gold-dim));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.hero-sub {
  margin-top: 10px;
  font-size: 13px;
  color: var(--text-sub);
}

.search-box {
  margin-top: 18px;
  display: flex;
  align-items: center;
  gap: 10px;
  max-width: 420px;
  padding: 11px 14px;
  border-radius: 10px;
  border: 1px solid var(--hairline);
  background: rgba(255, 255, 255, 0.03);
}

.search-icon {
  color: var(--text-faint);
  font-size: 14px;
}

.search-box input {
  flex: 1;
  border: none;
  background: none;
  outline: none;
  color: var(--text-main);
  font-family: var(--font-body);
  font-size: 14px;
}

.search-box input::placeholder {
  color: var(--text-faint);
}

.clear-search {
  background: none;
  border: none;
  color: var(--text-faint);
  cursor: pointer;
  font-size: 12px;
}

.clear-search:hover {
  color: var(--text-main);
}

.song-list {
  display: flex;
  flex-direction: column;
}

.list-head {
  display: grid;
  grid-template-columns: 56px 1fr 220px 40px;
  padding: 0 12px 10px;
  border-bottom: 1px solid var(--hairline-soft);
  margin-bottom: 6px;
  font-family: var(--font-mono);
  font-size: 10px;
  letter-spacing: 1px;
  text-transform: uppercase;
  color: var(--text-faint);
}

.song-item {
  position: relative;
  display: grid;
  grid-template-columns: 56px 1fr 220px 40px;
  align-items: center;
  padding: 10px 12px;
  border-radius: 8px;
  cursor: pointer;
  transition: background-color 0.2s ease;
}

.song-item:hover {
  background-color: rgba(255, 255, 255, 0.04);
}

.song-item.is-active {
  background-color: rgba(232, 184, 109, 0.08);
}

.song-item.is-active .song-info h3,
.song-item.is-active .index-num {
  color: var(--gold-bright);
}

.col-index {
  position: relative;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.index-num {
  font-family: var(--font-mono);
  font-size: 13px;
  color: var(--text-faint);
}

.index-play {
  display: none;
  font-size: 12px;
  color: var(--text-main);
}

.song-item:hover .index-num {
  display: none;
}

.song-item:hover .index-play {
  display: block;
}

.song-item.is-active .eq {
  display: flex;
  align-items: flex-end;
  gap: 2px;
  height: 14px;
}

.song-item.is-active:hover .eq {
  display: none;
}

.song-item.is-active:hover .index-play {
  display: block;
}

.eq i {
  width: 3px;
  background: var(--gold);
  border-radius: 1px;
  animation: eq 0.9s ease-in-out infinite;
}

.eq i:nth-child(1) { height: 40%; animation-delay: -0.6s; }
.eq i:nth-child(2) { height: 100%; animation-delay: -0.3s; }
.eq i:nth-child(3) { height: 65%; animation-delay: 0s; }

@keyframes eq {
  0%, 100% { transform: scaleY(0.4); }
  50% { transform: scaleY(1); }
}

.col-title {
  display: flex;
  align-items: center;
  min-width: 0;
}

.song-cover {
  width: 44px;
  height: 44px;
  margin-right: 14px;
  border-radius: 6px;
  overflow: hidden;
  flex-shrink: 0;
  box-shadow: 0 4px 10px rgba(0,0,0,0.35);
}

.song-cover img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.song-info {
  min-width: 0;
}

.song-info h3 {
  font-size: 14.5px;
  font-weight: 600;
  color: var(--text-main);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.col-artist {
  font-size: 13px;
  color: var(--text-sub);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  padding-right: 8px;
}

.col-actions {
  position: relative;
  display: flex;
  justify-content: center;
}

.menu-btn {
  background: none;
  border: none;
  color: var(--text-faint);
  font-size: 16px;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: 6px;
  opacity: 0;
  transition: opacity 0.15s ease, color 0.15s ease, background 0.15s ease;
}

.song-item:hover .menu-btn,
.menu-btn.is-open {
  opacity: 1;
}

.menu-btn:hover {
  color: var(--text-main);
  background: rgba(255, 255, 255, 0.06);
}

.song-menu {
  position: absolute;
  top: 100%;
  right: 0;
  z-index: 20;
  width: 220px;
  max-height: 320px;
  overflow-y: auto;
  background: linear-gradient(180deg, var(--panel-bg) 0%, #100d08 100%);
  border: 1px solid var(--hairline);
  border-radius: 10px;
  padding: 6px;
  box-shadow: 0 20px 50px rgba(0, 0, 0, 0.5);
}

.menu-item {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 8px;
  background: none;
  border: none;
  color: var(--text-main);
  font-size: 12.5px;
  text-align: left;
  padding: 8px 8px;
  border-radius: 6px;
  cursor: pointer;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.menu-item:hover {
  background: rgba(255, 255, 255, 0.06);
}

.menu-item.danger {
  color: var(--crimson);
}

.menu-item.accent {
  color: var(--gold);
}

.mi-icon {
  width: 14px;
  flex-shrink: 0;
  text-align: center;
  font-size: 11px;
  opacity: 0.85;
}

.menu-divider {
  height: 1px;
  background: var(--hairline-soft);
  margin: 4px 4px;
}

.menu-label {
  font-family: var(--font-mono);
  font-size: 9px;
  letter-spacing: 1px;
  text-transform: uppercase;
  color: var(--text-faint);
  padding: 4px 8px 2px;
}

.empty-state {
  padding: 60px 20px;
  text-align: center;
}

.empty-title {
  font-family: var(--font-display);
  font-size: 24px;
  font-weight: 400;
  color: var(--text-main);
  margin-bottom: 8px;
}

.empty-sub {
  font-size: 13px;
  color: var(--text-faint);
}

@media (max-width: 720px) {
  .list-head,
  .song-item {
    grid-template-columns: 40px 1fr 40px;
  }
  .col-artist {
    display: none;
  }
}
</style>