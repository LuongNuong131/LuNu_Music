<!-- src/views/Login.vue -->
<template>
  <div class="login-container">
    <div class="grain"></div>

    <div class="login-card">
      <div class="vinyl-wrap">
        <div class="vinyl">
          <div class="vinyl-label">LN</div>
        </div>
      </div>

      <p class="eyebrow">LuNu Music &mdash; Label Session</p>
      <h1 class="brand">LuNu</h1>
      <p class="tagline">Đăng nhập để quẩy nhạc</p>

      <form @submit.prevent="handleLogin">
        <div class="input-group">
          <label for="username">Username</label>
          <input
            id="username"
            type="text"
            v-model="username"
            placeholder="Tên đăng nhập"
            autocomplete="username"
            required
          />
        </div>
        <div class="input-group">
          <label for="password">Password</label>
          <input
            id="password"
            type="password"
            v-model="password"
            placeholder="Mật khẩu"
            autocomplete="current-password"
            required
          />
        </div>
        <button type="submit" :class="{ shake: error }">Vào nghe nhạc</button>
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
  position: relative;
  height: 100vh;
  display: flex;
  justify-content: center;
  align-items: center;
  background:
    radial-gradient(60% 50% at 50% 0%, rgba(232, 184, 109, 0.12) 0%, transparent 60%),
    var(--bg-color);
  overflow: hidden;
}

.grain {
  position: absolute;
  inset: 0;
  pointer-events: none;
  opacity: 0.05;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='120' height='120'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='2' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E");
}

.login-card {
  position: relative;
  background: linear-gradient(180deg, var(--panel-bg) 0%, #100d08 100%);
  padding: 44px 40px 36px;
  border-radius: 16px;
  border: 1px solid var(--hairline);
  width: 360px;
  text-align: center;
  box-shadow: 0 30px 80px rgba(0, 0, 0, 0.55), 0 0 0 1px rgba(232, 184, 109, 0.04);
}

.vinyl-wrap {
  display: flex;
  justify-content: center;
  margin-bottom: 20px;
}

.vinyl {
  width: 84px;
  height: 84px;
  border-radius: 50%;
  background:
    repeating-radial-gradient(circle at center, #1a1712 0px, #1a1712 2px, #0d0b08 3px, #0d0b08 4px);
  border: 1px solid var(--hairline);
  display: flex;
  align-items: center;
  justify-content: center;
  animation: spin 6s linear infinite;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.5);
}

.vinyl-label {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: linear-gradient(135deg, var(--gold-bright), var(--gold-dim));
  color: #100d08;
  font-family: var(--font-display);
  font-size: 14px;
  letter-spacing: 0.5px;
  display: flex;
  align-items: center;
  justify-content: center;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.eyebrow {
  font-family: var(--font-mono);
  font-size: 10px;
  letter-spacing: 2px;
  text-transform: uppercase;
  color: var(--gold-dim);
  margin-bottom: 6px;
}

.brand {
  font-family: var(--font-display);
  font-size: 52px;
  line-height: 1;
  letter-spacing: 1px;
  background: linear-gradient(180deg, var(--gold-bright) 0%, var(--gold-dim) 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.tagline {
  color: var(--text-sub);
  font-size: 13px;
  margin-bottom: 26px;
}

.input-group {
  margin-bottom: 14px;
  text-align: left;
}

.input-group label {
  display: block;
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.5px;
  text-transform: uppercase;
  color: var(--text-faint);
  margin-bottom: 6px;
}

input {
  width: 100%;
  padding: 12px 14px;
  border-radius: 8px;
  border: 1px solid var(--hairline-soft);
  background: rgba(255, 255, 255, 0.03);
  color: var(--text-main);
  font-family: var(--font-body);
  font-size: 14px;
  transition: border-color 0.2s ease, background 0.2s ease;
}

input::placeholder {
  color: var(--text-faint);
}

input:focus {
  border-color: var(--gold-dim);
  background: rgba(232, 184, 109, 0.05);
  outline: none;
}

button {
  width: 100%;
  padding: 13px;
  background: linear-gradient(135deg, var(--gold-bright), var(--gold));
  border: none;
  border-radius: 8px;
  color: #100d08;
  font-weight: 800;
  font-size: 14px;
  letter-spacing: 0.3px;
  cursor: pointer;
  margin-top: 12px;
  transition: transform 0.15s ease, box-shadow 0.15s ease;
}

button:hover {
  transform: translateY(-1px);
  box-shadow: 0 10px 24px rgba(232, 184, 109, 0.25);
}

button:active {
  transform: translateY(0);
}

button.shake {
  animation: shake 0.4s ease;
}

@keyframes shake {
  0%, 100% { transform: translateX(0); }
  25% { transform: translateX(-6px); }
  75% { transform: translateX(6px); }
}

.error-msg {
  color: var(--crimson);
  margin-top: 16px;
  font-size: 13px;
  font-weight: 600;
}
</style>