<template>
  <main class="login-wrapper"><div class="login-orbit orbit-one"></div><div class="login-orbit orbit-two"></div><section class="glass-login-box"><div class="login-brand"><span class="brand-mark">LN</span><div><strong>LuNu</strong><small>Music library</small></div></div><div class="logo-area"><p class="eyebrow">A QUIET PLACE TO LISTEN</p><h1>Âm thanh<br /><em>ở lại.</em></h1><p>Đăng nhập để tiếp tục hành trình nghe nhạc được tuyển chọn cho riêng bạn.</p></div><form @submit.prevent="handleLogin" class="login-form"><label class="input-group"><span>TÀI KHOẢN</span><input v-model.trim="username" type="text" autocomplete="username" placeholder="your.name" required /></label><label class="input-group"><span>MẬT KHẨU</span><input v-model="password" type="password" autocomplete="current-password" placeholder="••••••••" required /></label><p v-if="errorMsg" class="error-text" role="alert">{{ errorMsg }}</p><button type="submit" class="login-btn" :disabled="isLoading">{{ isLoading ? 'Đang xác thực...' : 'Mở thư viện' }} <span>→</span></button></form><p class="footer-text">Hệ thống riêng tư · Kết nối an toàn</p></section></main>
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
    const response = await login(username.value, password.value);
    if (response.success) loginUser(response);
    else errorMsg.value = response.message || 'Thông tin đăng nhập chưa chính xác.';
  } catch (error) {
    errorMsg.value = error.message || 'Không thể kết nối đến máy chủ.';
  } finally { isLoading.value = false; }
};
</script>

<style scoped>
.login-wrapper { position: relative; display: grid; place-items: center; min-height: 100vh; overflow: hidden; background: radial-gradient(circle at 70% 10%, rgba(245,185,122,.16), transparent 27%), radial-gradient(circle at 15% 90%, rgba(116,107,255,.14), transparent 34%), #0b0d13; color: var(--text-main); }.login-orbit { position: absolute; border: 1px solid rgba(245,185,122,.11); border-radius: 50%; }.orbit-one { width: min(70vw, 720px); height: min(70vw, 720px); transform: translate(35%, -30%); }.orbit-two { width: min(55vw, 560px); height: min(55vw, 560px); transform: translate(-55%, 35%); border-color: rgba(155,140,255,.1); }.glass-login-box { position: relative; z-index: 1; width: min(430px, calc(100% - 34px)); padding: 28px clamp(25px, 5vw, 48px) 25px; border: 1px solid rgba(255,255,255,.1); border-radius: 25px; background: linear-gradient(145deg, rgba(27,31,43,.9), rgba(13,16,24,.87)); box-shadow: 0 35px 100px rgba(0,0,0,.42); backdrop-filter: blur(22px); }.login-brand { display: flex; align-items: center; gap: 10px; }.brand-mark { display: grid; place-items: center; width: 34px; height: 34px; border-radius: 10px; background: linear-gradient(135deg, var(--gold), var(--coral)); color: #171218; font: 800 10px var(--font-mono); }.login-brand strong { display: block; font: 600 18px var(--font-display); }.login-brand small { display: block; margin-top: 2px; color: var(--text-faint); font: 8px var(--font-mono); letter-spacing: 1px; text-transform: uppercase; }.logo-area { padding: 66px 0 30px; }.eyebrow { color: var(--gold); font: 9px var(--font-mono); letter-spacing: 2px; }.logo-area h1 { margin-top: 14px; font: 500 54px/.92 var(--font-display); letter-spacing: -2px; }.logo-area h1 em { color: var(--gold); font-style: italic; }.logo-area p:last-child { max-width: 320px; margin-top: 19px; color: var(--text-sub); font-size: 12px; line-height: 1.65; }.login-form { display: grid; gap: 14px; }.input-group { display: grid; gap: 7px; }.input-group span { color: var(--text-faint); font: 8px var(--font-mono); letter-spacing: 1.5px; }.input-group input { width: 100%; box-sizing: border-box; padding: 13px 14px; border: 1px solid var(--hairline); border-radius: 10px; outline: 0; background: rgba(3,5,9,.3); color: var(--text-main); font-size: 12px; transition: .2s ease; }.input-group input:focus { border-color: rgba(245,185,122,.65); box-shadow: 0 0 0 3px rgba(245,185,122,.08); }.input-group input::placeholder { color: #555965; }.error-text { margin: 0; color: var(--crimson); font-size: 11px; }.login-btn { display: flex; align-items: center; justify-content: space-between; margin-top: 5px; padding: 14px 16px; border: 0; border-radius: 11px; background: linear-gradient(135deg, var(--gold-bright), var(--gold)); color: #171218; cursor: pointer; font-weight: 800; }.login-btn:hover:not(:disabled) { box-shadow: 0 10px 28px rgba(245,185,122,.23); transform: translateY(-1px); }.login-btn:disabled { opacity: .55; cursor: progress; }.login-btn span { font-size: 18px; }.footer-text { margin-top: 32px; color: var(--text-faint); text-align: center; font: 8px var(--font-mono); letter-spacing: .8px; text-transform: uppercase; }
</style>
