<template>
  <div class="login-wrapper">
    <div class="glass-login-box">
      <div class="logo-area">
        <h2>LuNu Music</h2>
        <p>Vui lòng đăng nhập để nghe nhạc</p>
      </div>

      <form @submit.prevent="handleLogin" class="login-form">
        <div class="input-group">
          <input type="text" v-model="username" placeholder="Tài khoản" required />
        </div>
        <div class="input-group">
          <input type="password" v-model="password" placeholder="Mật khẩu" required />
        </div>
        <p v-if="errorMsg" class="error-text">{{ errorMsg }}</p>
        
        <button type="submit" class="glass-btn login-btn" :disabled="isLoading">
          {{ isLoading ? 'Đang xác thực...' : 'Vào Giao Diện' }}
        </button>
      </form>
      <p class="footer-text">Hệ thống cấp quyền kín. Liên hệ Admin để nhận tài khoản.</p>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import { login } from '../services/api';
import { loginUser } from '../store/appState';

const username = ref('');
const password = ref('');
const errorMsg = ref('');
const isLoading = ref(false);

const handleLogin = async () => {
  errorMsg.value = '';
  isLoading.value = true;
  
  try {
    const res = await login(username.value, password.value);
    if (res.success) {
      loginUser(res.user);
    } else {
      errorMsg.value = res.message;
    }
  } catch (error) {
    errorMsg.value = 'Lỗi kết nối đến máy chủ!';
  } finally {
    isLoading.value = false;
  }
};
</script>

<style scoped>
.login-wrapper {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100vh;
  width: 100vw;
  background: linear-gradient(135deg, #0f2027, #203a43, #2c5364);
  color: white;
}

.glass-login-box {
  background: rgba(255, 255, 255, 0.05);
  border-radius: 20px;
  padding: 40px;
  width: 100%;
  max-width: 400px;
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  box-shadow: 0 15px 35px rgba(0,0,0,0.5);
  text-align: center;
}

.logo-area h2 {
  font-size: 2rem;
  margin-bottom: 5px;
  color: #1db954;
}

.logo-area p {
  color: rgba(255,255,255,0.6);
  margin-bottom: 30px;
  font-size: 0.9rem;
}

.input-group {
  margin-bottom: 20px;
}

.input-group input {
  width: 100%;
  padding: 15px 20px;
  border-radius: 12px;
  border: 1px solid rgba(255, 255, 255, 0.2);
  background: rgba(0, 0, 0, 0.3);
  color: #fff;
  font-size: 1rem;
  outline: none;
  transition: all 0.3s ease;
  box-sizing: border-box;
}

.input-group input:focus {
  border-color: #1db954;
  box-shadow: 0 0 10px rgba(29, 185, 84, 0.3);
}

.error-text {
  color: #ff4d4f;
  margin-bottom: 15px;
  font-size: 0.9rem;
}

.login-btn {
  width: 100%;
  padding: 15px;
  border-radius: 12px;
  border: 1px solid rgba(29, 185, 84, 0.5);
  background: rgba(29, 185, 84, 0.2);
  color: #1db954;
  font-weight: bold;
  font-size: 1.1rem;
  cursor: pointer;
  transition: all 0.3s ease;
}

.login-btn:hover {
  background: rgba(29, 185, 84, 0.8);
  color: white;
  box-shadow: 0 0 15px rgba(29, 185, 84, 0.5);
}

.footer-text {
  margin-top: 25px;
  font-size: 0.8rem;
  color: rgba(255,255,255,0.4);
}
</style>