<template>
  <main class="login-wrapper">
    <div class="login-layout">
      <section class="login-showcase" aria-labelledby="login-title">
        <div class="showcase-brand">
          <BrandMark /><strong>LuNu<span>music</span></strong>
        </div>
        <div class="showcase-copy">
          <span class="showcase-tag"><Headphones :size="17" /> Giai điệu của riêng bạn</span>
          <h1 id="login-title">Một chút nhạc.<br />Một khoảng riêng.</h1>
          <p>
            Những bài hát bạn thích, những người bạn thương.<br />Tất cả trong một không gian của
            riêng bạn.
          </p>
        </div>
        <img
          class="showcase-art"
          src="/images/listening-room.svg"
          alt="Một đĩa nhạc vinyl trên bìa đĩa màu tím"
          fetchpriority="high"
        />
        <div class="showcase-footer">
          <AudioLines :size="19" /><span>Nhạc hay hơn khi có người cùng nghe.</span>
        </div>
      </section>
      <section class="login-form-panel" aria-labelledby="welcome-title">
        <div class="login-form-content">
          <span class="login-symbol"><Headphones :size="27" /></span>
          <h2 id="welcome-title">Vui vì bạn ở đây.</h2>
          <p class="login-intro">Đăng nhập và tiếp tục câu chuyện âm nhạc của bạn.</p>
          <form @submit.prevent="handleLogin" class="login-form">
            <label class="input-group"
              ><span>Tài khoản</span
              ><input
                v-model.trim="username"
                type="text"
                autocomplete="username"
                placeholder="Tên đăng nhập của bạn"
                required
                :disabled="isLoading" /></label
            ><label class="input-group"
              ><span>Mật khẩu</span
              ><span class="password-field"
                ><input
                  v-model="password"
                  :type="showPassword ? 'text' : 'password'"
                  autocomplete="current-password"
                  placeholder="Nhập mật khẩu"
                  required
                  :disabled="isLoading" /><button
                  type="button"
                  :aria-label="showPassword ? 'Ẩn mật khẩu' : 'Hiện mật khẩu'"
                  :aria-pressed="showPassword"
                  @click="showPassword = !showPassword"
                >
                  <component :is="showPassword ? EyeOff : Eye" :size="18" /></button></span
            ></label>
            <p v-if="errorMsg" class="error-text" role="alert">{{ errorMsg }}</p>
            <button type="submit" class="login-btn" :disabled="isLoading">
              <span>{{
                isLoading ? 'Đang đăng nhập...' : 'Vào không gian của bạn'
              }}</span><LoaderCircle v-if="isLoading" class="login-spinner" :size="19" /><ArrowRight
                v-else
                :size="19"
              />
            </button>
          </form>
          <p class="login-help">
            Chưa có tài khoản? Liên hệ người quản trị<br />LuNu để được mời vào thư viện.
          </p>
          <p class="login-private"><LockKeyhole :size="13" /> Thư viện riêng tư, dành cho bạn.</p>
        </div>
        <span class="login-copyright">LuNu Music · Made for your everyday.</span>
      </section>
    </div>
  </main>
</template>
<script setup>
import { ref } from 'vue';
import {
  ArrowRight,
  AudioLines,
  Eye,
  EyeOff,
  Headphones,
  LoaderCircle,
  LockKeyhole,
} from '@lucide/vue';
import BrandMark from '../components/BrandMark.vue';
import { login } from '../services/api';
import { loginUser } from '../store/appState';

const username = ref('');
const password = ref('');
const showPassword = ref(false);
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
  } finally {
    isLoading.value = false;
  }
};
</script>

<style scoped>
.login-wrapper {
  min-height: 100%;
  background: var(--bg-deep);
  color: var(--text-main);
}
.login-layout {
  display: grid;
  grid-template-columns: 1.05fr 1fr;
  min-height: 100dvh;
  padding: 18px;
  gap: 18px;
}
.login-showcase {
  position: relative;
  display: flex;
  flex-direction: column;
  min-height: 680px;
  padding: 38px clamp(30px, 5vw, 85px);
  border-radius: 22px;
  background: #d9d0ff;
  color: #25203e;
  overflow: hidden;
}
.showcase-brand {
  display: flex;
  align-items: center;
  gap: 11px;
}
.showcase-brand svg {
  width: 39px;
  height: 39px;
  color: #25203e;
  --brand-ink: #d9d0ff;
}
.showcase-brand strong {
  font-size: 25px;
  letter-spacing: -1px;
}
.showcase-brand strong span {
  font-size: 16px;
  font-weight: 400;
  margin-left: 5px;
}
.showcase-copy {
  position: relative;
  z-index: 1;
  margin-top: 70px;
}
.showcase-tag {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 11px;
  color: #5c5075;
}
.showcase-copy h1 {
  margin-top: 22px;
  font-size: clamp(35px, 4vw, 61px);
  line-height: 1.25;
  letter-spacing: -2px;
  font-weight: 700;
}
.showcase-copy p {
  margin-top: 22px;
  font-size: 12px;
  line-height: 1.9;
  color: #5c5075;
}
.showcase-art {
  display: block;
  align-self: center;
  width: min(100%, 420px);
  margin-top: 6px;
  flex: 1;
  min-height: 0;
  max-height: 360px;
  object-fit: contain;
}
.showcase-footer {
  display: flex;
  align-items: center;
  gap: 11px;
  font-size: 10px;
  color: #5c5075;
  margin-top: auto;
}
.login-form-panel {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 45px 28px;
  position: relative;
}
.login-form-content {
  width: min(350px, 100%);
}
.login-symbol {
  display: grid;
  place-items: center;
  width: 57px;
  height: 57px;
  border: 1px solid var(--hairline);
  border-radius: 17px;
  background: var(--accent-soft);
  color: var(--gold);
  margin-bottom: 30px;
}
.login-form-content h2 {
  font-size: 30px;
  letter-spacing: -1px;
  font-weight: 600;
  line-height: 1.4;
}
.login-intro {
  font-size: 12px;
  line-height: 1.9;
  color: var(--text-sub);
  margin-top: 12px;
  max-width: 310px;
}
.login-form {
  display: grid;
  gap: 21px;
  margin-top: 35px;
}
.input-group {
  display: grid;
  gap: 10px;
}
.input-group > span:first-child {
  font-size: 12px;
  color: var(--text-sub);
  font-weight: 500;
}
.input-group input {
  width: 100%;
  height: 48px;
  padding: 13px 15px;
  border: 1px solid var(--hairline);
  border-radius: 10px;
  outline: none;
  background: var(--glass);
  color: var(--text-main);
  font-size: 12px;
}
.input-group input:focus {
  border-color: var(--gold);
}
.input-group input::placeholder {
  color: var(--text-faint);
}
.password-field {
  position: relative;
}
.password-field input {
  padding-right: 47px;
}
.password-field button {
  display: grid;
  place-items: center;
  position: absolute;
  top: 3px;
  right: 4px;
  width: 41px;
  height: 42px;
  border: 0;
  background: none;
  color: var(--text-faint);
}
.login-btn {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  min-height: 49px;
  padding: 14px 17px;
  margin-top: 3px;
  border: 0;
  border-radius: 10px;
  background: #d9d0ff;
  color: #25203e;
  font-size: 12px;
  font-weight: 600;
}
.login-btn:hover:not(:disabled) {
  background: #c9baff;
}
.error-text {
  color: var(--crimson);
  font-size: 11px;
  line-height: 1.8;
}
.login-help {
  margin-top: 24px;
  color: var(--text-sub);
  font-size: 10px;
  line-height: 1.9;
  text-align: center;
}
.login-private {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 7px;
  margin-top: 40px;
  color: var(--text-faint);
  font-size: 9px;
}
.login-copyright {
  position: absolute;
  bottom: 25px;
  color: var(--text-faint);
  font-size: 9px;
}
.login-spinner {
  animation: spin 1s linear infinite;
}
@media (max-width: 760px) {
  .login-layout {
    display: flex;
    flex-direction: column;
    gap: 0;
    padding: 12px;
  }
  .login-showcase {
    min-height: 0;
    padding: 25px 24px 29px;
    border-radius: 17px;
  }
  .showcase-brand svg {
    width: 31px;
    height: 31px;
  }
  .showcase-brand strong {
    font-size: 21px;
  }
  .showcase-copy {
    margin-top: 33px;
  }
  .showcase-tag {
    font-size: 9px;
  }
  .showcase-copy h1 {
    font-size: clamp(31px, 8vw, 42px);
    letter-spacing: -1.2px;
    margin-top: 15px;
  }
  .showcase-copy p {
    font-size: 10px;
    margin-top: 16px;
    max-width: 260px;
  }
  .showcase-art {
    position: absolute;
    width: 150px;
    height: 140px;
    bottom: -17px;
    right: -36px;
    opacity: 0.4;
    pointer-events: none;
  }
  .showcase-footer {
    display: none;
  }
  .login-form-panel {
    padding: 36px 16px 50px;
  }
  .login-symbol {
    display: none;
  }
  .login-form-content h2 {
    font-size: 25px;
  }
  .login-intro {
    font-size: 11px;
  }
  .login-form {
    margin-top: 26px;
    gap: 18px;
  }
  .input-group input {
    font-size: 16px;
  }
  .login-help {
    font-size: 10px;
  }
  .login-private {
    margin-top: 26px;
  }
  .login-copyright {
    bottom: 10px;
  }
  .login-layout {
    min-height: 100dvh;
  }
}
@media (prefers-reduced-motion: reduce) {
  .login-spinner {
    animation: none;
  }
}
</style>
