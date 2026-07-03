<!-- src/components/Sidebar.vue -->
<template>
  <div class="sidebar">
    <div class="logo">
      <h2 class="premium-text">LuNu Music</h2>
    </div>
    
    <nav class="nav-links">
      <a href="#" class="active">Trang chủ</a>
      <a href="#">Tìm kiếm</a>
      <a href="#">Thư viện</a>
    </nav>
    
    <div class="divider"></div>
    
    <nav class="nav-links secondary">
      <a href="#">Tạo Playlist</a>
      <a href="#">Bài hát đã thích</a>
    </nav>
  </div>
</template>

<script setup>
// Sidebar hiện tại chứa giao diện tĩnh, phần chuyển trang hoặc logic active mình có thể mở rộng sau.
</script>

<style scoped>
.sidebar {
  padding: 24px 12px;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.logo {
  padding: 0 12px;
  margin-bottom: 10px;
}

.premium-text {
  font-size: 24px;
  font-weight: 800;
  background: linear-gradient(45deg, #1db954, #ffffff);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  letter-spacing: -1px;
}

.nav-links {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.nav-links a {
  text-decoration: none;
  color: #b3b3b3;
  font-weight: 600;
  font-size: 14px;
  padding: 8px 12px;
  border-radius: 8px;
  transition: all 0.3s ease;
}

.nav-links a:hover {
  color: #ffffff;
}

.nav-links a.active {
  background-color: rgba(255, 255, 255, 0.1);
  color: #ffffff;
}

.divider {
  height: 1px;
  background-color: #282828;
  margin: 10px 12px;
}

.secondary a {
  font-weight: 500;
}
</style>