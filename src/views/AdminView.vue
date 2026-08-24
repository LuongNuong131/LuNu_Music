<template>
  <div class="admin-container">
    <div class="admin-header">
      <h2>Trung Tâm Điều Khiển LuNu</h2>
      <div class="tab-buttons">
        <button :class="{ active: activeTab === 'songs' }" @click="activeTab = 'songs'">Quản lý Bài Hát</button>
        <button :class="{ active: activeTab === 'users' }" @click="activeTab = 'users'">Quản lý Tài Khoản</button>
      </div>
    </div>

    <!-- TAB QUẢN LÝ BÀI HÁT -->
    <div v-if="activeTab === 'songs'" class="admin-panel glass-panel">
      <h3>Thêm Nhạc Bằng Bot</h3>
      <!-- Bot tải nhạc chỉ xuất hiện ở đây -->
      <DiscordBotSearch @song-added="refreshSongs" />
      
      <h3 style="margin-top: 30px;">Danh sách nhạc hệ thống</h3>
      <div class="list-wrapper">
        <div v-for="song in songsList" :key="song.id" class="list-item">
          <div class="info">
            <img :src="song.cover" alt="cover" class="tiny-cover" />
            <span>{{ song.title }} - {{ song.artist }}</span>
          </div>
          <button @click="handleDeleteSong(song.id)" class="delete-btn">Xóa</button>
        </div>
      </div>
    </div>

    <!-- TAB QUẢN LÝ TÀI KHOẢN -->
    <div v-if="activeTab === 'users'" class="admin-panel glass-panel">
      <h3>Cấp tài khoản mới</h3>
      <form @submit.prevent="handleAddUser" class="add-user-form">
        <input v-model="newUser.username" placeholder="Tên đăng nhập" required class="glass-input"/>
        <input v-model="newUser.password" placeholder="Mật khẩu" required class="glass-input"/>
        <select v-model="newUser.role" class="glass-input">
          <option value="user">User thường</option>
          <option value="admin">Admin</option>
        </select>
        <button type="submit" class="glass-btn">Cấp Quyền</button>
      </form>
      <p class="msg">{{ userMsg }}</p>

      <h3 style="margin-top: 30px;">Danh sách Tài khoản</h3>
      <div class="list-wrapper">
        <div v-for="u in usersList" :key="u.id" class="list-item">
          <div class="info">
            <strong>{{ u.username }}</strong> <span class="badge">{{ u.role }}</span>
          </div>
          <button v-if="u.username !== 'admin'" @click="handleDeleteUser(u.id)" class="delete-btn">Thu hồi</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import DiscordBotSearch from '../components/DiscordBotSearch.vue';
import { getUsers, addUser, deleteUser, getSongs, deleteSong } from '../services/api';
import { loadSongs } from '../data/songs';

const activeTab = ref('songs');
const songsList = ref([]);
const usersList = ref([]);
const userMsg = ref('');

const newUser = ref({ username: '', password: '', role: 'user' });

const refreshSongs = async () => {
  songsList.value = await getSongs();
  loadSongs(); // Update store chung cho app
};

const refreshUsers = async () => {
  usersList.value = await getUsers();
};

const handleDeleteSong = async (id) => {
  if(confirm("Ông có chắc muốn xóa bài này khỏi hệ thống không?")) {
    await deleteSong(id);
    await refreshSongs();
  }
};

const handleAddUser = async () => {
  const res = await addUser(newUser.value.username, newUser.value.password, newUser.value.role);
  userMsg.value = res.message;
  newUser.value = { username: '', password: '', role: 'user' };
  refreshUsers();
  setTimeout(() => userMsg.value = '', 3000);
};

const handleDeleteUser = async (id) => {
  if(confirm("Chắc chắn muốn thu hồi tài khoản này?")) {
    await deleteUser(id);
    await refreshUsers();
  }
};

onMounted(() => {
  refreshSongs();
  refreshUsers();
});
</script>

<style scoped>
.admin-container {
  padding: 20px;
  color: white;
}
.admin-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}
.tab-buttons button {
  background: transparent;
  border: none;
  color: rgba(255,255,255,0.5);
  font-size: 1.1rem;
  margin-left: 20px;
  cursor: pointer;
  padding-bottom: 5px;
}
.tab-buttons button.active {
  color: #1db954;
  border-bottom: 2px solid #1db954;
}
.glass-panel {
  background: rgba(255, 255, 255, 0.02);
  border-radius: 16px;
  padding: 24px;
  border: 1px solid rgba(255, 255, 255, 0.05);
}
.add-user-form {
  display: flex;
  gap: 10px;
  margin-top: 15px;
}
.glass-input {
  flex: 1;
  padding: 10px 15px;
  border-radius: 8px;
  border: 1px solid rgba(255, 255, 255, 0.2);
  background: rgba(0, 0, 0, 0.3);
  color: #fff;
}
.glass-btn {
  padding: 10px 20px;
  border-radius: 8px;
  background: rgba(29, 185, 84, 0.2);
  border: 1px solid rgba(29, 185, 84, 0.5);
  color: #1db954;
  cursor: pointer;
}
.list-wrapper {
  margin-top: 15px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.list-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: rgba(0,0,0,0.3);
  padding: 10px 15px;
  border-radius: 8px;
}
.tiny-cover { width: 30px; height: 30px; border-radius: 4px; margin-right: 10px; object-fit: cover;}
.info { display: flex; align-items: center; }
.badge { background: #1db954; padding: 2px 6px; border-radius: 10px; font-size: 0.7rem; color: black; margin-left: 10px;}
.delete-btn { background: #ff4d4f; border: none; color: white; padding: 6px 12px; border-radius: 6px; cursor: pointer;}
.msg { color: #1db954; margin-top: 10px; font-size: 0.9rem;}
</style>