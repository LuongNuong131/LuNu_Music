<!-- src/components/Sidebar.vue -->
<template>
  <div class="sidebar" :class="{ open }">
    <div class="logo">
      <span class="logo-mark">LN</span>
      <h2 class="premium-text">LuNu Music</h2>
      <button class="sidebar-close" @click="emit('close')" aria-label="Đóng menu">✕</button>
    </div>

    <nav class="nav-links">
      <a href="#" title="Trang chủ" :class="{ active: activeView === 'home' }" @click.prevent="emit('navigate', { view: 'home' })">
        <span class="icon">⌂</span> Trang chủ
      </a>
      <a href="#" title="Tìm kiếm" :class="{ active: activeView === 'search' }" @click.prevent="emit('navigate', { view: 'search' })">
        <span class="icon">⌕</span> Tìm kiếm
      </a>
      <a href="#" title="Thư viện">
        <span class="icon">▤</span> Thư viện
      </a>
    </nav>

    <div class="divider"></div>

    <div class="playlist-block">
      <div class="playlist-head">
        <p class="section-label">Playlist &middot; {{ playlists.length }}</p>
        <button class="add-btn" @click="showCreateModal = true" title="Tạo playlist mới">＋</button>
      </div>

      <div class="playlist-list" v-if="playlists.length">
        <div
          v-for="pl in playlists"
          :key="pl.id"
          class="playlist-row"
          :class="{ active: activeView === 'playlist' && activePlaylistId === pl.id }"
          @click="emit('navigate', { view: 'playlist', playlistId: pl.id })"
        >
          <span class="pl-name">{{ pl.name }}</span>
          <span class="pl-count">{{ pl.songIds.length }}</span>
          <span class="pl-actions">
            <button @click.stop="openRename(pl)" title="Đổi tên">✎</button>
            <button @click.stop="openDelete(pl)" title="Xoá playlist">✕</button>
          </span>
        </div>
      </div>
      <p v-else class="empty-hint">Chưa có playlist nào. Bấm ＋ để tạo playlist đầu tiên.</p>
    </div>

    <div class="divider"></div>

    <nav class="nav-links secondary">
      <a href="#">
        <span class="icon">♥</span> Bài hát đã thích
      </a>
    </nav>

    <div class="sidebar-footer">
      <p class="footer-label">LABEL</p>
      <p class="footer-value">Donald Gold &middot; Andree Right Hand</p>
    </div>

    <!-- Tạo playlist mới -->
    <ConfirmModal
      :visible="showCreateModal"
      mode="prompt"
      title="Playlist mới"
      placeholder="VD: Nhạc cày view, Đi cà phê..."
      confirm-label="Tạo"
      @confirm="handleCreate"
      @cancel="showCreateModal = false"
    />

    <!-- Đổi tên playlist -->
    <ConfirmModal
      :visible="!!renameTarget"
      mode="prompt"
      title="Đổi tên playlist"
      :initial-value="renameTarget?.name || ''"
      confirm-label="Lưu"
      @confirm="handleRename"
      @cancel="renameTarget = null"
    />

    <!-- Xoá playlist -->
    <ConfirmModal
      :visible="!!deleteTarget"
      mode="confirm"
      title="Xoá playlist?"
      :message="`'${deleteTarget?.name}' sẽ bị xoá vĩnh viễn khỏi máy này.`"
      confirm-label="Xoá"
      danger
      @confirm="handleDelete"
      @cancel="deleteTarget = null"
    />
  </div>
</template>

<script setup>
import { ref } from 'vue';
import { usePlaylists } from '../composables/usePlaylists.js';
import { useToast } from '../composables/useToast.js';
import ConfirmModal from './ConfirmModal.vue';

defineProps({
  activeView: { type: String, default: 'home' },
  activePlaylistId: { type: String, default: null },
  open: { type: Boolean, default: false } // Trạng thái mở drawer trên mobile
});

const emit = defineEmits(['navigate', 'close']);

const { playlists, createPlaylist, deletePlaylist, renamePlaylist } = usePlaylists();
const { showToast } = useToast();

const showCreateModal = ref(false);
const renameTarget = ref(null);
const deleteTarget = ref(null);

const handleCreate = (name) => {
  const playlist = createPlaylist(name);
  showCreateModal.value = false;
  showToast(`Đã tạo playlist "${playlist.name}"`, { type: 'success' });
  emit('navigate', { view: 'playlist', playlistId: playlist.id });
};

const openRename = (pl) => (renameTarget.value = pl);
const handleRename = (name) => {
  renamePlaylist(renameTarget.value.id, name);
  renameTarget.value = null;
  showToast('Đã lưu tên playlist mới', { type: 'success' });
};

const openDelete = (pl) => (deleteTarget.value = pl);
const handleDelete = () => {
  const name = deleteTarget.value?.name;
  deletePlaylist(deleteTarget.value.id);
  deleteTarget.value = null;
  showToast(`Đã xoá playlist "${name}"`);
  emit('navigate', { view: 'home' });
};
</script>

<style scoped>
.sidebar {
  height: 100%;
  padding: 22px 12px 18px;
  display: flex;
  flex-direction: column;
  gap: 14px;
  border-right: 1px solid var(--hairline-soft);
  overflow-y: auto;
}

.logo {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 0 10px;
  margin-bottom: 6px;
}

.sidebar-close {
  display: none;
}

.logo-mark {
  width: 30px;
  height: 30px;
  border-radius: 50%;
  flex-shrink: 0;
  background: linear-gradient(135deg, var(--gold-bright), var(--gold-dim));
  color: #100d08;
  font-family: var(--font-display);
  font-size: 13px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.premium-text {
  font-family: var(--font-display);
  font-size: 22px;
  letter-spacing: 0.5px;
  font-weight: 400;
  color: var(--text-main);
}

.nav-links {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.nav-links a {
  display: flex;
  align-items: center;
  gap: 12px;
  text-decoration: none;
  color: var(--text-sub);
  font-weight: 600;
  font-size: 13.5px;
  padding: 10px 12px;
  border-radius: 8px;
  border-left: 2px solid transparent;
  transition: all 0.2s ease;
  cursor: pointer;
}

.icon {
  width: 16px;
  text-align: center;
  font-size: 14px;
  opacity: 0.8;
}

.nav-links a:hover {
  color: var(--text-main);
  background-color: rgba(255, 255, 255, 0.04);
}

.nav-links a.active {
  background-color: rgba(232, 184, 109, 0.09);
  color: var(--gold-bright);
  border-left-color: var(--gold);
}

.divider {
  height: 1px;
  background-color: var(--hairline-soft);
  margin: 2px 12px;
  flex-shrink: 0;
}

.secondary a {
  font-weight: 500;
}

.playlist-block {
  padding: 0 4px;
  min-height: 0;
  display: flex;
  flex-direction: column;
}

.playlist-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 8px;
  margin-bottom: 8px;
}

.section-label {
  font-family: var(--font-mono);
  font-size: 10px;
  letter-spacing: 1.5px;
  text-transform: uppercase;
  color: var(--gold-dim);
}

.add-btn {
  background: none;
  border: 1px solid var(--hairline);
  color: var(--gold);
  width: 20px;
  height: 20px;
  border-radius: 5px;
  font-size: 12px;
  line-height: 1;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background 0.15s ease;
}

.add-btn:hover {
  background: rgba(232, 184, 109, 0.1);
}

.playlist-list {
  display: flex;
  flex-direction: column;
  gap: 2px;
  overflow-y: auto;
}

.playlist-row {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 8px;
  border-radius: 7px;
  cursor: pointer;
  font-size: 13px;
  color: var(--text-sub);
  transition: background-color 0.2s ease;
}

.playlist-row:hover {
  background-color: rgba(255, 255, 255, 0.04);
}

.playlist-row.active {
  background-color: rgba(232, 184, 109, 0.09);
  color: var(--gold-bright);
}

.pl-name {
  flex: 1;
  min-width: 0;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.pl-count {
  font-family: var(--font-mono);
  font-size: 10.5px;
  color: var(--text-faint);
  flex-shrink: 0;
}

.pl-actions {
  display: none;
  flex-shrink: 0;
  gap: 4px;
}

.playlist-row:hover .pl-actions {
  display: flex;
}

.pl-actions button {
  background: none;
  border: none;
  color: var(--text-faint);
  font-size: 11px;
  cursor: pointer;
  padding: 2px 3px;
}

.pl-actions button:hover {
  color: var(--text-main);
}

.empty-hint {
  padding: 4px 8px;
  font-size: 11.5px;
  color: var(--text-faint);
  line-height: 1.5;
}

.sidebar-footer {
  margin-top: auto;
  padding: 14px 12px 4px;
  border-top: 1px solid var(--hairline-soft);
  flex-shrink: 0;
}

.footer-label {
  font-family: var(--font-mono);
  font-size: 9px;
  letter-spacing: 1.5px;
  color: var(--gold-dim);
  margin-bottom: 4px;
}

.footer-value {
  font-size: 11px;
  color: var(--text-faint);
  line-height: 1.4;
}
</style>