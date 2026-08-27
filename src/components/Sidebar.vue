<template>
  <aside class="glass-sidebar">
    <div class="sidebar-brand"><div class="brand-mark">LN</div><div><strong>LuNu</strong><span>Music library</span></div></div>
    <div class="sidebar-label">WORKSPACE</div>
    <nav class="nav-menu" aria-label="Điều hướng chính">
      <button :class="{ active: currentView === 'home' }" @click="currentView = 'home'"><span>⌂</span> Tổng quan</button>
      <button :class="{ active: currentView === 'liked' }" @click="currentView = 'liked'"><span>♥</span> Yêu thích</button>
      <button :class="{ active: currentView === 'playlists' }" @click="currentView = 'playlists'"><span>▤</span> Playlist</button>
      <button :class="{ active: currentView === 'lyrics' }" @click="currentView = 'lyrics'"><span>Aa</span> Lyrics Lab</button>
      <button :class="{ active: currentView === 'cinema' }" @click="currentView = 'cinema'"><span>▶</span> LuNu Tea Room</button>
      <button :class="{ active: currentView === 'proposals' }" @click="currentView = 'proposals'"><span>✧</span> Đề xuất media</button>
      <button :class="{ active: currentView === 'account' }" @click="currentView = 'account'"><span>◎</span> Hồ sơ</button>
      <button :class="{ active: currentView === 'rooms' }" @click="currentView = 'rooms'"><span>◉</span> Phòng nghe</button>
      <button v-if="authState.user?.role === 'admin'" :class="{ active: currentView === 'admin' }" @click="currentView = 'admin'"><span>✦</span> Quản trị</button>
    </nav>
    <div class="sidebar-note"><span class="note-orb">◖</span><div><small>NOW CURATING</small><p>Những âm thanh<br />đáng nhớ.</p></div></div>
    <div class="user-info"><img v-if="authState.user?.avatar_url" :src="authState.user.avatar_url" :alt="authState.user.display_name || authState.user.username" class="avatar avatar-image" /><div v-else class="avatar">{{ (authState.user?.display_name || authState.user?.username || 'U').slice(0, 1).toUpperCase() }}</div><div class="user-copy"><strong>{{ authState.user?.display_name || authState.user?.username || 'Listener' }}</strong><span>@{{ authState.user?.username || 'listener' }} · {{ authState.user?.role === 'admin' ? 'Administrator' : 'Member' }}</span></div><button @click="logoutUser" class="logout-btn" aria-label="Đăng xuất">↗</button></div>
  </aside>
</template>

<script setup>
import { authState, currentView, logoutUser } from '../store/appState';
</script>

<style scoped>
.glass-sidebar { display: flex; flex-direction: column; width: 244px; padding: 27px 18px 17px; border-right: 1px solid var(--hairline); background: linear-gradient(180deg, rgba(17,20,29,.95), rgba(10,12,18,.88)); }.sidebar-brand { display: flex; align-items: center; gap: 11px; padding: 0 10px 42px; }.brand-mark { display: grid; place-items: center; width: 35px; height: 35px; border: 1px solid rgba(245,185,122,.45); border-radius: 11px; background: linear-gradient(135deg, var(--gold), var(--coral)); color: #171218; font: 800 10px var(--font-mono); letter-spacing: -1px; box-shadow: 0 8px 25px rgba(245,185,122,.16); }.sidebar-brand strong { display: block; color: var(--text-main); font: 600 18px var(--font-display); letter-spacing: -.5px; }.sidebar-brand span { display: block; margin-top: 2px; color: var(--text-faint); font: 8px var(--font-mono); letter-spacing: 1.1px; text-transform: uppercase; }.sidebar-label { padding: 0 10px 11px; color: var(--text-faint); font: 8px var(--font-mono); letter-spacing: 1.8px; }.nav-menu { display: flex; flex-direction: column; gap: 4px; }.nav-menu button { display: flex; align-items: center; gap: 12px; width: 100%; padding: 12px 11px; border: 1px solid transparent; border-radius: 11px; background: transparent; color: var(--text-sub); text-align: left; cursor: pointer; font-size: 11px; transition: .2s ease; }.nav-menu button span { display: grid; place-items: center; width: 20px; color: var(--text-faint); font: 700 12px var(--font-mono); }.nav-menu button:hover, .nav-menu button.active { border-color: var(--hairline-soft); background: linear-gradient(90deg, rgba(245,185,122,.13), rgba(245,185,122,.025)); color: var(--text-main); }.nav-menu button.active span { color: var(--gold); }.sidebar-note { display: flex; align-items: flex-start; gap: 11px; margin: auto 9px 28px; padding: 16px 10px; border: 1px solid rgba(245,185,122,.14); border-radius: 13px; background: radial-gradient(circle at 15% 10%, rgba(245,185,122,.12), transparent 65%), rgba(255,255,255,.025); }.note-orb { color: var(--gold); font-size: 20px; }.sidebar-note small { color: var(--gold-dim); font: 8px var(--font-mono); letter-spacing: 1.2px; }.sidebar-note p { margin-top: 7px; color: var(--text-sub); font: italic 14px/1.3 var(--font-display); }.user-info { display: flex; align-items: center; gap: 9px; padding: 13px 7px 0; border-top: 1px solid var(--hairline-soft); }.avatar { display: grid; place-items: center; width: 30px; height: 30px; border-radius: 50%; background: linear-gradient(135deg, var(--violet), var(--gold)); color: #15111a; font: 800 11px var(--font-mono); }.avatar-image { object-fit: cover; }.user-copy { display: flex; flex: 1; flex-direction: column; min-width: 0; }.user-copy strong, .user-copy span { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }.user-copy strong { color: var(--text-main); font-size: 10px; }.user-copy span { margin-top: 3px; color: var(--text-faint); font: 8px var(--font-mono); text-transform: uppercase; }.logout-btn { width: 28px; height: 28px; border: 1px solid transparent; border-radius: 8px; background: transparent; color: var(--text-faint); cursor: pointer; }.logout-btn:hover { border-color: rgba(255,109,125,.3); color: var(--crimson); }@media (max-width: 760px) { .glass-sidebar { width: 100%; height: 64px; padding: 8px 12px; border-top: 1px solid var(--hairline); border-right: 0; }.sidebar-brand, .sidebar-note, .user-info, .sidebar-label { display: none; }.nav-menu { flex-direction: row; justify-content: center; gap: 6px; height: 100%; }.nav-menu button { flex: 1; justify-content: center; padding: 7px; }.nav-menu button span { width: auto; }.nav-menu button:not(.active) { opacity: .75; } }
</style>

<style scoped>
@media (max-width: 760px) {
  .glass-sidebar { overflow: hidden; }
  .nav-menu { justify-content: flex-start; gap: 4px; overflow-x: auto; overflow-y: hidden; scroll-snap-type: x proximity; scrollbar-width: none; }
  .nav-menu::-webkit-scrollbar { display: none; }
  .nav-menu button { flex: 0 0 auto; min-width: 72px; min-height: 50px; flex-direction: column; gap: 3px; padding: 5px 8px; border-radius: 9px; scroll-snap-align: center; font-size: 8px; white-space: nowrap; }
  .nav-menu button span { height: 18px; font-size: 13px; }
}
@media (max-width: 380px) {
  .nav-menu button { min-width: 64px; padding-right: 5px; padding-left: 5px; font-size: 7px; }
}
</style>
