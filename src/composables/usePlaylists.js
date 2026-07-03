// src/composables/usePlaylists.js
// Quản lý Playlist của người dùng, lưu trực tiếp vào localStorage.
// Dùng state ở module-level (singleton) để mọi component dùng chung 1 nguồn dữ liệu,
// không cần cài thêm Pinia/Vuex cho một app nhỏ như thế này.

import { ref, watch } from 'vue';

const STORAGE_KEY = 'lunu_playlists_v1';

function loadPlaylists() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    const parsed = raw ? JSON.parse(raw) : [];
    return Array.isArray(parsed) ? parsed : [];
  } catch (err) {
    console.warn('Không đọc được playlist từ localStorage, dùng danh sách rỗng.', err);
    return [];
  }
}

const playlists = ref(loadPlaylists());

// Mỗi lần playlists đổi (thêm/xoá/sửa) -> tự động ghi lại vào localStorage
watch(
  playlists,
  (value) => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(value));
    } catch (err) {
      console.warn('Không lưu được playlist vào localStorage.', err);
    }
  },
  { deep: true }
);

const genId = () => `${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 7)}`;

function createPlaylist(name) {
  const trimmed = (name || '').trim();
  const playlist = {
    id: genId(),
    name: trimmed || `Playlist ${playlists.value.length + 1}`,
    songIds: [],
    createdAt: Date.now()
  };
  playlists.value.push(playlist);
  return playlist;
}

function deletePlaylist(playlistId) {
  playlists.value = playlists.value.filter((p) => p.id !== playlistId);
}

function renamePlaylist(playlistId, name) {
  const trimmed = (name || '').trim();
  if (!trimmed) return;
  const playlist = playlists.value.find((p) => p.id === playlistId);
  if (playlist) playlist.name = trimmed;
}

function addSongToPlaylist(playlistId, songId) {
  const playlist = playlists.value.find((p) => p.id === playlistId);
  if (playlist && !playlist.songIds.includes(songId)) {
    playlist.songIds.push(songId);
  }
}

function removeSongFromPlaylist(playlistId, songId) {
  const playlist = playlists.value.find((p) => p.id === playlistId);
  if (playlist) {
    playlist.songIds = playlist.songIds.filter((id) => id !== songId);
  }
}

function isSongInPlaylist(playlistId, songId) {
  const playlist = playlists.value.find((p) => p.id === playlistId);
  return !!playlist && playlist.songIds.includes(songId);
}

export function usePlaylists() {
  return {
    playlists,
    createPlaylist,
    deletePlaylist,
    renamePlaylist,
    addSongToPlaylist,
    removeSongFromPlaylist,
    isSongInPlaylist
  };
}