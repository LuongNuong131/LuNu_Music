<template>
  <main class="login-wrapper">
    <div class="login-orbit orbit-one"></div>
    <div class="login-orbit orbit-two"></div>
    <div class="login-layout">
      <section class="login-showcase" aria-labelledby="login-title">
        <div class="showcase-kicker"><span class="signal-dot"></span> PERSONAL LISTENING ROOM</div>
        <div class="showcase-copy">
          <p class="eyebrow">LU NU / 2026 EDITION</p>
          <h1 id="login-title">Âm thanh<br /><em>ở lại.</em></h1>
          <p>Thư viện cá nhân cho những bài hát bạn muốn nghe chậm hơn, sâu hơn và theo cách của riêng mình.</p>
        </div>
        <div class="showcase-art" aria-hidden="true">
          <div class="vinyl-disc"><div class="vinyl-label">LN<span>LISTEN<br />SLOWLY</span></div></div>
          <div class="showcase-caption"><span>01 / QUIET ROTATION</span><strong>Made for the moments<br />in between.</strong></div>
        </div>
      </section>

      <section class="glass-login-box" aria-label="Đăng nhập LuNu Music">
        <div class="login-brand"><span class="brand-mark">LN</span><div><strong>LuNu</strong><small>Music library</small></div></div>
        <div class="login-card-copy"><p class="eyebrow">WELCOME BACK</p><h2>Chào mừng<br /><em>trở lại.</em></h2><p>Đăng nhập để tiếp tục hành trình nghe nhạc được tuyển chọn cho riêng bạn.</p></div>
        <form @submit.prevent="handleLogin" class="login-form">
          <label class="input-group"><span>TÀI KHOẢN</span><input v-model.trim="username" type="text" autocomplete="username" placeholder="your.name" required /></label>
          <label class="input-group"><span>MẬT KHẨU</span><input v-model="password" type="password" autocomplete="current-password" placeholder="••••••••" required /></label>
          <p v-if="errorMsg" class="error-text" role="alert">{{ errorMsg }}</p>
          <button type="submit" class="login-btn" :disabled="isLoading"><span>{{ isLoading ? 'Đang xác thực...' : 'Mở thư viện' }}</span><b>↗</b></button>
        </form>
        <p class="footer-text"><span>Hệ thống riêng tư</span><i></i><span>Kết nối an toàn</span></p>
      </section>
    </div>
  </main>
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
.login-wrapper { position: relative; display: grid; place-items: center; min-height: 100vh; overflow: hidden; background: radial-gradient(circle at 70% 10%, rgba(255,196,107,.15), transparent 27%), radial-gradient(circle at 15% 90%, rgba(116,107,255,.14), transparent 34%), #080a10; color: var(--text-main); }
.login-layout { position: relative; z-index: 1; display: grid; grid-template-columns: minmax(0, 1fr) minmax(350px, 430px); gap: clamp(45px, 8vw, 120px); align-items: center; width: min(1060px, calc(100% - 48px)); padding: 36px 0; }
.login-showcase { min-width: 0; }
.showcase-kicker { display: inline-flex; align-items: center; gap: 9px; color: var(--gold); font: 9px var(--font-mono); letter-spacing: 1.8px; }
.signal-dot { width: 6px; height: 6px; border-radius: 50%; background: var(--mint); box-shadow: 0 0 14px var(--mint); }
.showcase-copy { padding: 90px 0 44px; }
.eyebrow { margin: 0 0 13px; color: var(--gold); font: 9px var(--font-mono); letter-spacing: 2.2px; }
.showcase-copy h1 { margin: 0; color: #faf7f0; font: 500 clamp(66px, 9vw, 124px)/.84 var(--font-display); letter-spacing: -6px; }
.showcase-copy h1 em, .login-card-copy h2 em { color: var(--gold); font-style: italic; }
.showcase-copy > p:last-child { max-width: 420px; margin-top: 28px; color: var(--text-sub); font-size: 14px; line-height: 1.75; }
.showcase-art { position: relative; min-height: 125px; padding-left: 158px; display: flex; align-items: center; }
.vinyl-disc { position: absolute; left: 18px; width: 154px; height: 154px; border-radius: 50%; background: repeating-radial-gradient(circle at center, #11151e 0 2px, #202532 3px 4px, #10131b 5px 7px); box-shadow: 0 22px 45px rgba(0,0,0,.42), inset 0 0 0 1px rgba(255,255,255,.08); animation: slow-spin 18s linear infinite; }
.vinyl-disc::after { content: ''; position: absolute; inset: 15px; border: 1px solid rgba(255,255,255,.06); border-radius: 50%; }
.vinyl-label { position: absolute; inset: 52px; display: grid; place-items: center; border-radius: 50%; background: linear-gradient(135deg, var(--gold), var(--coral)); color: #18131a; text-align: center; font: 800 12px var(--font-mono); line-height: 1; }
.vinyl-label span { display: block; margin-top: 4px; font-size: 5px; letter-spacing: 1px; line-height: 1.35; }
.showcase-caption { display: grid; gap: 8px; padding-left: 18px; border-left: 1px solid rgba(245,185,122,.28); }
.showcase-caption span { color: var(--text-faint); font: 8px var(--font-mono); letter-spacing: 1.4px; }
.showcase-caption strong { color: var(--text-main); font: 500 18px/1.2 var(--font-display); }
.glass-login-box { width: 100%; padding: 31px clamp(26px, 4vw, 42px) 25px; border: 1px solid rgba(255,255,255,.11); border-radius: 28px; background: linear-gradient(145deg, rgba(27,31,43,.93), rgba(12,15,23,.88)); box-shadow: 0 35px 100px rgba(0,0,0,.44), inset 0 1px 0 rgba(255,255,255,.06); backdrop-filter: blur(22px); }
.login-brand { display: flex; align-items: center; gap: 10px; }
.brand-mark { display: grid; place-items: center; width: 36px; height: 36px; border-radius: 11px; background: linear-gradient(135deg, var(--gold), var(--coral)); color: #171218; font: 800 10px var(--font-mono); box-shadow: 0 9px 22px rgba(245,185,122,.16); }
.login-brand strong { display: block; font: 600 18px var(--font-display); }.login-brand small { display: block; margin-top: 2px; color: var(--text-faint); font: 8px var(--font-mono); letter-spacing: 1px; text-transform: uppercase; }
.login-card-copy { padding: 74px 0 28px; }.login-card-copy h2 { margin: 0; font: 500 40px/.95 var(--font-display); letter-spacing: -1.8px; }.login-card-copy > p:last-child { max-width: 300px; margin-top: 15px; color: var(--text-sub); font-size: 12px; line-height: 1.65; }
.login-form { display: grid; gap: 14px; }.input-group { display: grid; gap: 7px; }.input-group span { color: var(--text-faint); font: 8px var(--font-mono); letter-spacing: 1.5px; }.input-group input { width: 100%; box-sizing: border-box; padding: 14px; border: 1px solid var(--hairline); border-radius: 11px; outline: 0; background: rgba(3,5,9,.3); color: var(--text-main); font-size: 12px; transition: border-color .2s var(--ease-out), box-shadow .2s var(--ease-out), background .2s var(--ease-out); }.input-group input:focus { border-color: rgba(245,185,122,.7); background: rgba(3,5,9,.5); box-shadow: 0 0 0 3px rgba(245,185,122,.08); }.input-group input::placeholder { color: #555965; }.error-text { margin: 0; color: var(--crimson); font-size: 11px; }.login-btn { display: flex; align-items: center; justify-content: space-between; margin-top: 5px; padding: 14px 16px; border: 0; border-radius: 11px; background: linear-gradient(135deg, var(--gold-bright), var(--gold)); color: #171218; cursor: pointer; font-weight: 800; }.login-btn:hover:not(:disabled) { box-shadow: 0 12px 30px rgba(245,185,122,.24); transform: translateY(-2px); }.login-btn b { font-size: 17px; }.login-btn:disabled { opacity: .55; cursor: progress; }.footer-text { display: flex; justify-content: center; align-items: center; gap: 9px; margin-top: 30px; color: var(--text-faint); font: 8px var(--font-mono); letter-spacing: .8px; text-transform: uppercase; }.footer-text i { width: 3px; height: 3px; border-radius: 50%; background: var(--gold-dim); }
.login-orbit { position: absolute; border: 1px solid rgba(245,185,122,.09); border-radius: 50%; pointer-events: none; }.orbit-one { width: min(70vw, 720px); height: min(70vw, 720px); transform: translate(35%, -30%); }.orbit-two { width: min(55vw, 560px); height: min(55vw, 560px); transform: translate(-55%, 35%); border-color: rgba(155,140,255,.1); }
@keyframes slow-spin { to { transform: rotate(360deg); } }
@media (max-width: 760px) { .login-layout { grid-template-columns: 1fr; gap: 18px; width: min(470px, calc(100% - 28px)); padding: 24px 0; }.login-showcase { padding: 8px 7px 0; }.showcase-copy { padding: 48px 0 24px; }.showcase-copy h1 { font-size: clamp(56px, 16vw, 86px); letter-spacing: -4px; }.showcase-copy > p:last-child { margin-top: 18px; font-size: 12px; }.showcase-art { display: none; }.glass-login-box { padding: 25px 24px 20px; border-radius: 23px; }.login-card-copy { padding: 35px 0 24px; }.login-card-copy h2 { font-size: 34px; } }
@media (prefers-reduced-motion: reduce) { .vinyl-disc { animation: none; } }
</style>
