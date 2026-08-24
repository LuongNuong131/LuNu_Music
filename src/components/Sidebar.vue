<template>
  <div class="sidebar glass-sidebar">
    <div class="logo">
      <h2>LuNu Music</h2>
    </div>
    
    <nav class="nav-menu">
      <button @click="currentView = 'home'" :class="{ active: currentView === 'home' }">Trang Chủ</button>
      <!-- Nút Quản Lý ẩn đi với User thường -->
      <button v-if="authState.user?.role === 'admin'" @click="currentView = 'admin'" :class="{ active: currentView === 'admin' }">
        Quản Lý (Admin)
      </button>
    </nav>

    <div class="user-info">
      <p>Xin chào, <strong>{{ authState.user?.username }}</strong></p>
      <button @click="logoutUser" class="logout-btn">Đăng xuất</button>
    </div>
  </div>
</template>

<script setup>
import { authState, currentView, logoutUser } from '../store/appState';
</script>

<style scoped>
.glass-sidebar {
  width: 250px;
  background: rgba(0, 0, 0, 0.2);
  backdrop-filter: blur(10px);
  border-right: 1px solid rgba(255, 255, 255, 0.05);
  display: flex;
  flex-direction: column;
  padding: 20px;
}

.logo h2 { color: #1db954; margin-bottom: 30px; font-size: 1.5rem; }

.nav-menu { display: flex; flex-direction: column; gap: 10px; flex: 1; }

.nav-menu button {
  background: transparent;
  border: none;
  color: #b3b3b3;
  text-align: left;
  padding: 10px;
  font-size: 1rem;
  font-weight: bold;
  cursor: pointer;
  border-radius: 8px;
  transition: all 0.3s;
}

.nav-menu button:hover, .nav-menu button.active {
  background: rgba(255, 255, 255, 0.1);
  color: white;
}

.user-info {
  margin-top: auto;
  border-top: 1px solid rgba(255,255,255,0.1);
  padding-top: 15px;
}

.user-info p { color: white; font-size: 0.9rem; margin-bottom: 10px; }

.logout-btn {
  width: 100%;
  background: transparent;
  border: 1px solid rgba(255, 255, 255, 0.2);
  color: white;
  padding: 8px;
  border-radius: 8px;
  cursor: pointer;
}
.logout-btn:hover { background: rgba(255, 77, 79, 0.2); border-color: #ff4d4f; color: #ff4d4f; }
</style>