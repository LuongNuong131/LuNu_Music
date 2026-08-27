<template>
  <section class="account-container">
    <header class="account-header">
      <div>
        <p class="eyebrow">IDENTITY / ACCOUNT</p>
        <h1>Không gian <em>của bạn.</em></h1>
        <p>Quản lý hồ sơ cá nhân và bảo mật tài khoản trong một không gian riêng tư.</p>
      </div>
      <div class="account-status"><span class="status-orb"></span><span>SECURE PROFILE</span></div>
    </header>

    <div v-if="isLoading" class="account-state glass-panel">Đang tải hồ sơ của bạn...</div>
    <div v-else class="account-grid">
      <section class="profile-card glass-panel">
        <div class="section-heading">
          <div><span class="panel-kicker">PERSONAL IDENTITY</span><h2>Hồ sơ cá nhân</h2></div>
          <span class="profile-index">01</span>
        </div>

        <div class="profile-hero">
          <div class="avatar-stage">
            <img v-if="avatarPreview || profile.avatar_url" :src="avatarPreview || profile.avatar_url" alt="Ảnh đại diện" class="profile-avatar" />
            <div v-else class="profile-avatar profile-initial">{{ initials }}</div>
            <button type="button" class="avatar-edit" @click="openFilePicker" aria-label="Đổi ảnh đại diện" title="Đổi ảnh đại diện">↗</button>
          </div>
          <div class="profile-identity">
            <strong>{{ profile.display_name || profile.username }}</strong>
            <span>@{{ profile.username }}</span>
            <small>{{ profile.role === 'admin' ? 'Administrator' : 'Member' }} · Thành viên LuNu</small>
          </div>
        </div>

        <input ref="fileInput" class="file-input" type="file" accept="image/png,image/jpeg,image/webp" @change="handleAvatarChange" />
        <div class="upload-hint">JPG, PNG hoặc WebP · tối đa 5 MiB</div>

        <form class="profile-form" @submit.prevent="saveProfile">
          <label><span>TÊN HIỂN THỊ</span><input v-model.trim="profile.display_name" maxlength="120" placeholder="Tên bạn muốn mọi người nhìn thấy" /></label>
          <label><span>USERNAME</span><input :value="profile.username" disabled class="locked-input" /><small>Tên đăng nhập cố định để giữ nguyên bạn bè và lịch sử.</small></label>
          <label class="wide"><span>GIỚI THIỆU</span><textarea v-model="profile.bio" maxlength="280" rows="4" placeholder="Một vài điều về bạn và gu âm nhạc của bạn..."></textarea><small class="character-count">{{ profile.bio.length }}/280</small></label>
          <div class="form-actions"><button type="submit" class="primary-btn" :disabled="isSaving">{{ isSaving ? 'Đang lưu...' : 'Lưu hồ sơ' }}</button></div>
        </form>
      </section>

      <section class="security-card glass-panel">
        <div class="section-heading">
          <div><span class="panel-kicker">ACCOUNT SECURITY</span><h2>Bảo mật tài khoản</h2></div>
          <span class="profile-index">02</span>
        </div>
        <p class="section-note">Đổi mật khẩu định kỳ để bảo vệ thư viện, playlist và các hoạt động xã hội của bạn.</p>
        <form class="password-form" @submit.prevent="changePassword">
          <label><span>MẬT KHẨU HIỆN TẠI</span><input v-model="passwords.current" type="password" autocomplete="current-password" required placeholder="Nhập mật khẩu hiện tại" /></label>
          <label><span>MẬT KHẨU MỚI</span><input v-model="passwords.next" type="password" autocomplete="new-password" minlength="8" required placeholder="Tối thiểu 8 ký tự" /></label>
          <label><span>XÁC NHẬN MẬT KHẨU MỚI</span><input v-model="passwords.confirm" type="password" autocomplete="new-password" minlength="8" required placeholder="Nhập lại mật khẩu mới" /></label>
          <button type="submit" class="secondary-btn" :disabled="isChangingPassword">{{ isChangingPassword ? 'Đang cập nhật...' : 'Cập nhật mật khẩu →' }}</button>
        </form>
        <div class="security-note"><span>◈</span><p>Mật khẩu được xử lý ở backend và không bao giờ hiển thị trong hồ sơ hoặc khu vực quản trị.</p></div>
      </section>
    </div>
  </section>
</template>

<script setup>
import { computed, onMounted, onBeforeUnmount, ref } from 'vue';
import { changeMyPassword, getMyProfile, updateMyProfile, uploadMyAvatar } from '../services/api';
import { authState, updateAuthUser } from '../store/appState';
import { useToast } from '../composables/useToast';

const { showToast } = useToast();
const fileInput = ref(null);
const isLoading = ref(true);
const isSaving = ref(false);
const isChangingPassword = ref(false);
const avatarPreview = ref('');
const profile = ref({ id: '', username: '', role: 'user', display_name: '', avatar_url: '', bio: '' });
const passwords = ref({ current: '', next: '', confirm: '' });

const initials = computed(() => (profile.value.display_name || profile.value.username || 'U').trim().slice(0, 2).toUpperCase());

const syncUser = (user) => {
  profile.value = { ...profile.value, ...user };
  updateAuthUser(user);
};

const loadProfile = async () => {
  isLoading.value = true;
  try {
    const response = await getMyProfile();
    syncUser(response.user || authState.user || {});
  } catch (error) {
    syncUser(authState.user || {});
    showToast(error.message || 'Không thể tải hồ sơ lúc này.', { type: 'warning', duration: 4200 });
  } finally {
    isLoading.value = false;
  }
};

const saveProfile = async () => {
  isSaving.value = true;
  try {
    const response = await updateMyProfile(profile.value);
    syncUser(response.user || profile.value);
    showToast(response.message || 'Đã cập nhật hồ sơ.', { type: 'success' });
  } catch (error) {
    showToast(error.message || 'Không thể cập nhật hồ sơ.', { type: 'error', duration: 4600 });
  } finally {
    isSaving.value = false;
  }
};

const openFilePicker = () => fileInput.value?.click();

const handleAvatarChange = async (event) => {
  const file = event.target.files?.[0];
  event.target.value = '';
  if (!file) return;
  if (!['image/jpeg', 'image/png', 'image/webp'].includes(file.type)) {
    showToast('Avatar chỉ hỗ trợ JPG, PNG hoặc WebP.', { type: 'warning' });
    return;
  }
  if (file.size > 5 * 1024 * 1024) {
    showToast('Avatar không được lớn hơn 5 MiB.', { type: 'warning' });
    return;
  }
  if (avatarPreview.value) URL.revokeObjectURL(avatarPreview.value);
  avatarPreview.value = URL.createObjectURL(file);
  try {
    const response = await uploadMyAvatar(file);
    syncUser(response.user || profile.value);
    if (avatarPreview.value) URL.revokeObjectURL(avatarPreview.value);
    avatarPreview.value = '';
    showToast(response.message || 'Đã cập nhật ảnh đại diện.', { type: 'success' });
  } catch (error) {
    if (avatarPreview.value) URL.revokeObjectURL(avatarPreview.value);
    avatarPreview.value = '';
    showToast(error.message || 'Không thể cập nhật ảnh đại diện.', { type: 'error', duration: 4600 });
  }
};

const changePassword = async () => {
  if (passwords.value.next !== passwords.value.confirm) {
    showToast('Mật khẩu xác nhận chưa trùng khớp.', { type: 'warning' });
    return;
  }
  isChangingPassword.value = true;
  try {
    const response = await changeMyPassword(passwords.value.current, passwords.value.next);
    passwords.value = { current: '', next: '', confirm: '' };
    showToast(response.message || 'Đã đổi mật khẩu thành công.', { type: 'success', duration: 4200 });
  } catch (error) {
    showToast(error.message || 'Không thể đổi mật khẩu.', { type: 'error', duration: 4600 });
  } finally {
    isChangingPassword.value = false;
  }
};

onMounted(loadProfile);
onBeforeUnmount(() => { if (avatarPreview.value) URL.revokeObjectURL(avatarPreview.value); });
</script>

<style scoped>
.account-container { max-width: 1180px; margin: 0 auto; padding: 18px 0 80px; }.account-header { display: flex; align-items: flex-end; justify-content: space-between; gap: 24px; padding: 32px 0 34px; }.eyebrow, .panel-kicker { color: var(--gold); font: 9px var(--font-mono); letter-spacing: 1.8px; }.account-header h1 { margin-top: 12px; font: 500 clamp(40px, 5vw, 62px)/.95 var(--font-display); letter-spacing: -2px; }.account-header h1 em { color: var(--gold); font-style: italic; }.account-header p:last-child { max-width: 520px; margin-top: 15px; color: var(--text-sub); font-size: 12px; line-height: 1.6; }.account-status { display: flex; align-items: center; gap: 8px; padding: 9px 12px; border: 1px solid rgba(139,224,190,.22); border-radius: 99px; color: var(--mint); font: 8px var(--font-mono); letter-spacing: 1px; }.status-orb { width: 7px; height: 7px; border-radius: 50%; background: var(--mint); box-shadow: 0 0 12px var(--mint); }.account-grid { display: grid; grid-template-columns: minmax(0, 1.12fr) minmax(310px, .88fr); gap: 16px; }.profile-card, .security-card { padding: clamp(18px, 3vw, 30px); border-radius: 20px; }.section-heading { display: flex; align-items: flex-start; justify-content: space-between; gap: 12px; margin-bottom: 25px; }.section-heading h2 { margin-top: 7px; color: var(--text-main); font: 500 25px var(--font-display); }.profile-index { color: var(--text-faint); font: 10px var(--font-mono); }.profile-hero { display: flex; align-items: center; gap: 17px; padding-bottom: 24px; border-bottom: 1px solid var(--hairline-soft); }.avatar-stage { position: relative; flex: 0 0 auto; }.profile-avatar { display: grid; place-items: center; width: 92px; height: 92px; border: 1px solid rgba(245,185,122,.42); border-radius: 28px; object-fit: cover; background: linear-gradient(135deg, var(--violet), var(--gold)); color: #171218; font: 800 25px var(--font-mono); box-shadow: 0 15px 40px rgba(0,0,0,.28); }.avatar-edit { position: absolute; right: -7px; bottom: -7px; display: grid; place-items: center; width: 29px; height: 29px; border: 2px solid #141722; border-radius: 10px; background: var(--gold); color: #171218; cursor: pointer; font-weight: 800; }.avatar-edit:hover { transform: translateY(-1px); box-shadow: 0 7px 16px rgba(245,185,122,.23); }.profile-identity { display: flex; flex-direction: column; min-width: 0; }.profile-identity strong { overflow: hidden; color: var(--text-main); text-overflow: ellipsis; white-space: nowrap; font: 500 26px var(--font-display); }.profile-identity span { margin-top: 5px; color: var(--gold); font: 10px var(--font-mono); }.profile-identity small { margin-top: 15px; color: var(--text-faint); font-size: 10px; }.file-input { display: none; }.upload-hint { margin: 12px 0 21px; color: var(--text-faint); font: 9px var(--font-mono); letter-spacing: .5px; }.profile-form, .password-form { display: grid; gap: 15px; }.profile-form { grid-template-columns: 1fr 1fr; }.profile-form label, .password-form label { display: grid; gap: 7px; }.profile-form label span, .password-form label span { color: var(--text-faint); font: 8px var(--font-mono); letter-spacing: 1.3px; }.profile-form input, .profile-form textarea, .password-form input { width: 100%; box-sizing: border-box; padding: 12px 13px; border: 1px solid var(--hairline); border-radius: 10px; outline: 0; background: rgba(3,5,9,.33); color: var(--text-main); font: 11px/1.45 var(--font-body); transition: .2s ease; }.profile-form textarea { resize: vertical; }.profile-form input:focus, .profile-form textarea:focus, .password-form input:focus { border-color: rgba(245,185,122,.58); box-shadow: 0 0 0 3px rgba(245,185,122,.07); }.locked-input { opacity: .55; cursor: not-allowed; }.profile-form small, .password-form small { color: var(--text-faint); font-size: 9px; line-height: 1.4; }.wide, .form-actions { grid-column: 1 / -1; }.character-count { text-align: right; }.form-actions { display: flex; justify-content: flex-end; }.primary-btn, .secondary-btn { border: 0; border-radius: 10px; padding: 12px 16px; cursor: pointer; font-size: 10px; font-weight: 800; }.primary-btn { background: linear-gradient(135deg, var(--gold-bright), var(--gold)); color: #171218; }.secondary-btn { margin-top: 4px; background: rgba(245,185,122,.12); border: 1px solid rgba(245,185,122,.25); color: var(--gold-bright); }.primary-btn:hover:not(:disabled), .secondary-btn:hover:not(:disabled) { transform: translateY(-1px); box-shadow: 0 10px 24px rgba(245,185,122,.14); }.primary-btn:disabled, .secondary-btn:disabled { opacity: .55; cursor: progress; }.section-note { margin: -9px 0 24px; color: var(--text-sub); font-size: 11px; line-height: 1.6; }.security-card { align-self: start; }.security-note { display: flex; align-items: flex-start; gap: 10px; margin-top: 27px; padding: 12px; border: 1px solid rgba(139,224,190,.16); border-radius: 12px; background: rgba(139,224,190,.04); }.security-note span { color: var(--mint); font-size: 15px; }.security-note p { color: var(--text-sub); font-size: 10px; line-height: 1.55; }.account-state { padding: 40px; color: var(--text-sub); border-radius: 18px; text-align: center; font-size: 11px; }
@media (max-width: 860px) { .account-grid { grid-template-columns: 1fr; }.security-card { align-self: auto; } }
@media (max-width: 620px) { .account-container { padding-bottom: 100px; }.account-header { align-items: flex-start; flex-direction: column; padding-top: 20px; }.account-status { align-self: flex-start; }.profile-form { grid-template-columns: 1fr; }.wide, .form-actions { grid-column: auto; }.form-actions { justify-content: stretch; }.form-actions button, .secondary-btn { width: 100%; }.profile-avatar { width: 76px; height: 76px; border-radius: 23px; }.profile-identity strong { font-size: 21px; } }
</style>
