<!-- src/views/Login.vue -->
<template>
  <div class="login-container">
    <div class="login-card">
      <h2>LuNu Music</h2>
      <p>Đăng nhập để quẩy nhạc</p>
      
      <form @submit.prevent="handleLogin">
        <div class="input-group">
          <input 
            type="text" 
            v-model="username" 
            placeholder="Username" 
            required
          />
        </div>
        <div class="input-group">
          <input 
            type="password" 
            v-model="password" 
            placeholder="Password" 
            required
          />
        </div>
        <button type="submit">Đăng nhập</button>
      </form>
      <p v-if="error" class="error-msg">{{ error }}</p>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import { useRouter } from 'vue-router';
import { users } from '../data/users';

const username = ref('');
const password = ref('');
const error = ref('');
const router = useRouter();

const handleLogin = () => {
  const user = users.find(u => u.username === username.value && u.password === password.value);
  
  if (user) {
    localStorage.setItem('isLoggedIn', 'true');
    router.push('/'); // Chuyển hướng vào trang chính
  } else {
    error.value = 'Sai tài khoản hoặc mật khẩu rồi Cưng ơi!';
  }
};
</script>

<style scoped>
.login-container {
  height: 100vh;
  display: flex;
  justify-content: center;
  align-items: center;
  background: linear-gradient(135deg, #1db954 0%, #121212 100%);
}

.login-card {
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(15px);
  -webkit-backdrop-filter: blur(15px);
  padding: 40px;
  border-radius: 20px;
  border: 1px solid rgba(255, 255, 255, 0.2);
  width: 350px;
  text-align: center;
}

h2 { margin-bottom: 20px; color: #fff; }

.input-group { margin-bottom: 15px; }

input {
  width: 100%;
  padding: 12px;
  border-radius: 8px;
  border: none;
  background: rgba(255, 255, 255, 0.05);
  color: white;
}

button {
  width: 100%;
  padding: 12px;
  background: #1db954;
  border: none;
  border-radius: 8px;
  color: white;
  font-weight: bold;
  cursor: pointer;
  margin-top: 10px;
}

.error-msg {
  color: #ff4d4d;
  margin-top: 15px;
  font-size: 0.9em;
}
</style>