<template>
  <!-- Màn hình Đăng Nhập nếu chưa có user -->
  <div v-if="!authState.user" id="login-container">
    <Login />
  </div>

  <!-- Giao diện chính sau khi Login thành công -->
  <div v-else id="app-container" class="glass-app-wrapper">
    <Sidebar />
    
    <main class="main-content">
      <!-- Hiển thị AdminView hoặc MainView dựa trên State -->
      <AdminView v-if="currentView === 'admin'" />
      <MainView v-else />
    </main>
    
    <!-- Player luôn hiện ở dưới -->
    <PlayerBar />
    <NowPlayingView />
    <QueuePanel />
    <CommandPalette />
    <Toast />
  </div>
</template>

<script setup>
import { onMounted } from 'vue';
import { loadSongs } from './data/songs';
import { authState, currentView } from './store/appState';

import Login from './views/Login.vue';
import AdminView from './views/AdminView.vue';
import Sidebar from './components/Sidebar.vue';
import MainView from './components/MainView.vue';
import PlayerBar from './components/PlayerBar.vue';
import NowPlayingView from './components/NowPlayingView.vue';
import QueuePanel from './components/QueuePanel.vue';
import CommandPalette from './components/CommandPalette.vue';
import Toast from './components/Toast.vue';

onMounted(() => {
  // Chỉ tải nhạc nếu đã login
  if (authState.user) {
    loadSongs();
  }
});
</script>

<style>
/* Reset style & Base App */
body, html { margin: 0; padding: 0; font-family: 'Inter', system-ui, sans-serif; }

#login-container {
  height: 100vh;
  width: 100vw;
}

#app-container {
  display: flex;
  height: 100vh;
  background: linear-gradient(135deg, #0a0a0a, #1a1a1a);
  color: white;
  overflow: hidden;
}

.main-content {
  flex: 1;
  padding: 24px;
  overflow-y: auto;
  background: rgba(255, 255, 255, 0.02);
  backdrop-filter: blur(20px);
  border-left: 1px solid rgba(255, 255, 255, 0.05);
}
</style>