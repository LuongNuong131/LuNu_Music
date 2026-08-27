<template>
  <div v-if="!authState.user || !authState.token" id="login-container"><Login /></div>
  <div v-else id="app-container" class="glass-app-wrapper noise-overlay">
    <button type="button" class="mobile-menu-toggle" :aria-expanded="mobileMenuOpen" aria-controls="lunu-navigation" @click="mobileMenuOpen = true"><span></span><span></span><span></span><b>Menu</b></button>
    <button type="button" class="theme-quick-toggle" :aria-label="themeState === 'dark' ? 'Chuyển sang Light mode' : 'Chuyển sang Dark mode'" :title="themeState === 'dark' ? 'Light mode' : 'Dark mode'" @click="toggleTheme">{{ themeState === 'dark' ? '☾' : '☀' }}</button>
    <div v-if="mobileMenuOpen" class="mobile-menu-backdrop" aria-hidden="true" @click="mobileMenuOpen = false"></div>
    <Sidebar id="lunu-navigation" :mobile-open="mobileMenuOpen" @close="mobileMenuOpen = false" />
    <main class="main-content">
      <div class="app-utility-bar" role="navigation" aria-label="Thanh công cụ nhanh">
        <div class="utility-context"><span class="utility-pulse"></span><span>LISTENING ROOM</span><b>/</b><strong>{{ viewTitle }}</strong></div>
        <div class="utility-actions"><NotificationCenter compact /><button type="button" class="utility-search" aria-label="Mở tìm kiếm nhanh" @click="commandOpen = true"><span>⌕</span><span class="utility-search-label">Tìm nhanh</span><kbd>⌘ K</kbd></button></div>
      </div>
      <AdminView v-if="currentView === 'admin'" />
      <CinemaView v-else-if="currentView === 'cinema'" />
      <LyricsManager v-else-if="currentView === 'lyrics'" :songs="songs" @play-song="playFromLibrary" />
      <PlaylistsView v-else-if="currentView === 'playlists'" :songs="songs" @play-song="playFromLibrary" />
      <ArtistsView v-else-if="currentView === 'artists'" :songs="songs" @play-song="playFromLibrary" />
      <ProposalView v-else-if="currentView === 'proposals'" />
      <AccountView v-else-if="currentView === 'account'" />
      <RoomsView v-else-if="currentView === 'rooms'" />
      <FriendsView v-else-if="currentView === 'friends'" />
      <ChatView v-else-if="currentView === 'chat'" />
      <MainView v-else :songs="songs" :only-liked="currentView === 'liked'" :loading="songsLoading" :error="songsError" @retry="loadSongs" />
    </main>
    <RoomSyncBridge />
    <PlayerBar />
    <NowPlayingView
      :visible="player.state.nowPlayingVisible"
      :current-song="player.state.currentSong"
      :is-playing="player.state.isPlaying"
      :is-shuffle="player.state.shuffle"
      :repeat-mode="player.state.repeatMode"
      :current-time="player.state.currentTime"
      :duration="player.state.duration"
      @close="player.state.nowPlayingVisible = false"
      @toggle-play="player.togglePlay"
      @next="player.next"
      @prev="player.previous"
      @toggle-shuffle="player.toggleShuffle"
      @toggle-repeat="player.toggleRepeat"
      @seek="player.seek"
      @manage-lyrics="currentView = 'lyrics'"
    />
    <QueuePanel
      :visible="player.state.queueVisible"
      :current-song="player.state.currentSong"
      :queue="player.state.queue"
      @close="player.state.queueVisible = false"
      @remove="player.removeFromQueue"
      @clear="player.clearQueue"
      @play="playFromQueue"
    />
    <CommandPalette :visible="commandOpen" :songs="songs" :playlists="playlists" @close="commandOpen = false" @play-song="playFromLibrary" @open-playlist="openPlaylist" @action="runCommand" />
    <Toast />
    <ConfirmModal
      :visible="dialog.state.visible"
      :title="dialog.state.title"
      :message="dialog.state.message"
      :mode="dialog.state.mode"
      :initial-value="dialog.state.initialValue"
      :placeholder="dialog.state.placeholder"
      :confirm-label="dialog.state.confirmLabel"
      :cancel-label="dialog.state.cancelLabel"
      :danger="dialog.state.danger"
      @confirm="dialog.confirm"
      @cancel="dialog.cancel"
    />
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue';
import { loadSongs, songsError, songsLoading } from './data/songs';
import songs from './data/songs';
import { authState, currentView } from './store/appState';
import { themeState, toggleTheme } from './store/themeState';
import { playSong, usePlayer } from './store/playerState';
import { usePlaylists } from './composables/usePlaylists';
import Login from './views/Login.vue';
import AdminView from './views/AdminView.vue';
import CinemaView from './views/CinemaView.vue';
import Sidebar from './components/Sidebar.vue';
import MainView from './components/MainView.vue';
import LyricsManager from './components/LyricsManager.vue';
import PlaylistsView from './views/PlaylistsView.vue';
import ArtistsView from './views/ArtistsView.vue';
import ProposalView from './views/ProposalView.vue';
import AccountView from './views/AccountView.vue';
import RoomsView from './views/RoomsView.vue';
import FriendsView from './views/FriendsView.vue';
import ChatView from './views/ChatView.vue';
import PlayerBar from './components/PlayerBar.vue';
import RoomSyncBridge from './components/RoomSyncBridge.vue';
import NowPlayingView from './components/NowPlayingView.vue';
import QueuePanel from './components/QueuePanel.vue';
import CommandPalette from './components/CommandPalette.vue';
import Toast from './components/Toast.vue';
import ConfirmModal from './components/ConfirmModal.vue';
import NotificationCenter from './components/NotificationCenter.vue';
import { useDialog } from './composables/useDialog';

const viewTitle = computed(() => ({ home: 'Tổng quan', liked: 'Yêu thích', playlists: 'Playlist', artists: 'Ca sĩ', lyrics: 'Lyrics Lab', cinema: 'LuNu Tea Room', proposals: 'Đề xuất media', account: 'Hồ sơ', rooms: 'Phòng nghe', friends: 'Bạn bè', chat: 'Chat', admin: 'Quản trị' }[currentView.value] || 'Tổng quan'));
const player = usePlayer();
const { playlists, selectPlaylist } = usePlaylists();
const commandOpen = ref(false);
const mobileMenuOpen = ref(false);
const dialog = useDialog();
watch(mobileMenuOpen, (open) => { document.body.classList.toggle('mobile-menu-open', open); });

const playFromLibrary = (song, collection = songs) => playSong(song, Array.isArray(collection) && collection.length ? collection : songs);
const playFromQueue = (song) => playSong(song, [player.state.currentSong, ...player.state.queue].filter(Boolean));
const openPlaylist = (playlist) => { selectPlaylist(playlist?.id); currentView.value = 'playlists'; };
const runCommand = (action) => {
  if (action === 'home') currentView.value = 'home';
  if (action === 'search') commandOpen.value = true;
  if (action === 'toggle-shuffle') player.toggleShuffle();
  if (action === 'toggle-queue') player.state.queueVisible = true;
};

const onKeydown = (event) => {
  if (event.key === 'Escape' && mobileMenuOpen.value) { mobileMenuOpen.value = false; return; }
  const tag = event.target?.tagName?.toLowerCase();
  const typing = tag === 'input' || tag === 'textarea' || event.target?.isContentEditable;
  if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === 'k') { event.preventDefault(); commandOpen.value = !commandOpen.value; return; }
  if (typing || !player.state.currentSong) return;
  if (event.code === 'Space') { event.preventDefault(); player.togglePlay(); }
  else if (event.key === 'ArrowLeft') player.seek(player.state.currentTime - 5);
  else if (event.key === 'ArrowRight') player.seek(player.state.currentTime + 5);
  else if (event.key === 'ArrowUp') player.setVolume(player.state.volume + 0.05);
  else if (event.key === 'ArrowDown') player.setVolume(player.state.volume - 0.05);
  else if (event.key.toLowerCase() === 'm') player.toggleMute();
  else if (event.key.toLowerCase() === 'n') player.next();
  else if (event.key.toLowerCase() === 'p') player.previous();
  else if (event.key.toLowerCase() === 's') player.toggleShuffle();
  else if (event.key.toLowerCase() === 'r') player.toggleRepeat();
};

onMounted(async () => { window.addEventListener('keydown', onKeydown); if (authState.user) await loadSongs(); });
onBeforeUnmount(() => { window.removeEventListener('keydown', onKeydown); document.body.classList.remove('mobile-menu-open'); });
</script>

<style>
#login-container { min-height: 100vh; width: 100%; }
#app-container { display: grid; grid-template-columns: 244px minmax(0, 1fr); grid-template-rows: minmax(0, 1fr) auto; height: 100vh; min-height: 600px; overflow: hidden; color: var(--text-main); background: radial-gradient(circle at 70% -20%, rgba(245,185,122,.13), transparent 32%), radial-gradient(circle at 0% 100%, rgba(113,110,255,.1), transparent 38%), var(--bg-deep); }
.main-content { min-width: 0; min-height: 0; padding: clamp(18px, 3vw, 40px); overflow: auto; }
.mobile-menu-toggle, .theme-quick-toggle, .mobile-menu-backdrop { display: none; }
#app-container > .player-bar { grid-column: 1 / -1; }
@media (max-width: 760px) { #app-container { display: flex; flex-direction: column; min-height: 100vh; }.main-content { flex: 1; order: 0; padding: 72px 16px max(90px, calc(74px + env(safe-area-inset-bottom))); }.theme-quick-toggle { position: fixed; z-index: 90; top: max(12px, env(safe-area-inset-top)); right: 14px; display: grid; place-items: center; width: 40px; height: 40px; border: 1px solid rgba(245,185,122,.3); border-radius: 12px; background: rgba(13,16,24,.92); color: var(--gold-bright); box-shadow: 0 10px 28px rgba(0,0,0,.25); cursor: pointer; font-size: 18px; backdrop-filter: blur(14px); }.mobile-menu-toggle { position: fixed; z-index: 90; top: max(12px, env(safe-area-inset-top)); left: 14px; display: inline-flex; align-items: center; gap: 4px; height: 40px; padding: 7px 11px; border: 1px solid rgba(245,185,122,.3); border-radius: 12px; background: rgba(13,16,24,.92); color: var(--gold-bright); box-shadow: 0 10px 28px rgba(0,0,0,.25); cursor: pointer; backdrop-filter: blur(14px); }.mobile-menu-toggle span { display: block; width: 15px; height: 1.5px; border-radius: 2px; background: currentColor; }.mobile-menu-toggle b { margin-left: 4px; font: 9px var(--font-mono); letter-spacing: 1px; text-transform: uppercase; }.mobile-menu-backdrop { position: fixed; z-index: 110; inset: 0; display: block; background: rgba(3,5,10,.62); backdrop-filter: blur(2px); }.player-bar { order: 1; position: fixed !important; right: 0; bottom: 64px; left: 0; } body.mobile-menu-open { overflow: hidden; } }
@media (max-width: 380px) { .mobile-menu-toggle { padding-right: 9px; padding-left: 9px; }.mobile-menu-toggle b { display: none; } }
:root[data-theme='light'] #app-container { background: radial-gradient(circle at 70% -20%, rgba(154,103,60,.13), transparent 34%), radial-gradient(circle at 0% 100%, rgba(102,89,168,.09), transparent 38%), var(--bg-deep); }
:root[data-theme='light'] .theme-quick-toggle { background: rgba(255,250,243,.92); color: var(--gold-bright); box-shadow: 0 10px 28px rgba(91,67,46,.14); }
@media (prefers-reduced-motion: reduce) { .mobile-menu-toggle, .theme-quick-toggle, .mobile-menu-backdrop { transition: none; } }
.app-utility-bar { display: flex; align-items: center; justify-content: space-between; gap: 18px; max-width: 1440px; margin: 0 auto 14px; min-height: 34px; color: var(--text-faint); }
.utility-context { display: flex; align-items: center; gap: 9px; min-width: 0; font: 8px var(--font-mono); letter-spacing: 1.6px; }
.utility-context strong { overflow: hidden; color: var(--text-main); font-weight: 500; text-overflow: ellipsis; white-space: nowrap; letter-spacing: .4px; }
.utility-context b { color: var(--hairline); font-weight: 400; }
.utility-pulse { width: 6px; height: 6px; flex: none; border-radius: 50%; background: var(--mint); box-shadow: 0 0 12px var(--mint); }
.utility-actions { display: flex; align-items: center; gap: 8px; flex: none; }.utility-search { display: inline-flex; align-items: center; gap: 8px; flex: none; padding: 7px 9px; border: 1px solid var(--hairline-soft); border-radius: 9px; background: rgba(255,255,255,.035); color: var(--text-sub); cursor: pointer; font: 10px var(--font-body); }
.utility-search:hover { border-color: rgba(245,185,122,.34); background: rgba(245,185,122,.07); color: var(--text-main); }
.utility-search > span:first-child { color: var(--gold); font-size: 15px; line-height: .7; }
.utility-search kbd { padding: 3px 5px; border: 1px solid var(--hairline-soft); border-radius: 5px; color: var(--text-faint); font: 8px var(--font-mono); }
@media (max-width: 760px) { .app-utility-bar { margin: 0 4px 12px; min-height: 25px; }.utility-context > span:not(.utility-pulse), .utility-context b { display: none; }.utility-actions { gap: 6px; }.utility-search { padding: 7px 8px; }.utility-search-label, .utility-search kbd { display: none; } }
/* Mobile shell v2: phone-first navigation and floating player dock. */
@media (max-width: 760px) {
  #app-container { min-height: 100dvh; height: 100dvh; }
  #app-container .main-content { padding-top: 78px; padding-bottom: calc(104px + env(safe-area-inset-bottom)); }
  #app-container .app-utility-bar { position: fixed; z-index: 100; top: 0; right: 0; left: 0; display: flex; min-height: 62px; margin: 0; padding: max(10px, env(safe-area-inset-top)) 14px 9px 76px; border-bottom: 1px solid rgba(255,255,255,.07); background: linear-gradient(180deg, rgba(8,10,16,.97), rgba(8,10,16,.84)); backdrop-filter: blur(18px); }
  #app-container .utility-context { gap: 7px; font-size: 8px; }
  #app-container .utility-context strong { font-size: 10px; }
  #app-container .utility-actions { margin-left: auto; }
  #app-container .utility-search { width: 34px; height: 34px; padding: 0; justify-content: center; border-radius: 10px; }
  #app-container .mobile-menu-toggle { z-index: 180; top: max(10px, env(safe-area-inset-top)); left: 14px; width: 46px; height: 36px; padding: 0; justify-content: center; border-color: rgba(245,185,122,.34); border-radius: 11px; background: rgba(18,21,30,.92); }
  #app-container .mobile-menu-toggle b { display: none; }
  #app-container .theme-quick-toggle { display: none; }
  #app-container > .glass-sidebar { position: fixed; z-index: 170; top: 0; bottom: 0; left: 0; width: min(310px, 86vw); height: 100dvh; padding: max(20px, env(safe-area-inset-top)) 18px max(18px, env(safe-area-inset-bottom)); border-right: 1px solid rgba(245,185,122,.2); border-top: 0; border-radius: 0 24px 24px 0; background: linear-gradient(180deg, rgba(18,22,32,.99), rgba(8,11,17,.98)); box-shadow: 26px 0 70px rgba(0,0,0,.5); }
  #app-container > .glass-sidebar .sidebar-brand { padding-bottom: 28px; }
  #app-container > .glass-sidebar .nav-menu { padding-top: 2px; }
  #app-container > .glass-sidebar .nav-menu button { min-height: 43px; border-radius: 12px; }
  #app-container > .glass-sidebar .sidebar-note { margin-bottom: 18px; }
  #app-container > .player-bar { position: fixed !important; z-index: 140; right: 12px; bottom: max(12px, env(safe-area-inset-bottom)); left: 12px; min-height: 68px !important; padding: 8px 11px !important; border: 1px solid rgba(245,185,122,.2); border-radius: 19px; background: rgba(16,19,28,.94); box-shadow: 0 18px 45px rgba(0,0,0,.42), 0 0 0 1px rgba(255,255,255,.03); backdrop-filter: blur(22px); }
  #app-container > .player-bar .mini-art { width: 42px; height: 42px; border-radius: 12px; }
  #app-container > .player-bar .track-title { font-size: 11px; }
  #app-container > .player-bar .track-artist { margin-top: 3px; font-size: 9px; }
  #app-container > .player-bar .play-btn { width: 40px; height: 40px; }
}
@media (max-width: 390px) {
  #app-container .main-content { padding-right: 11px; padding-left: 11px; }
  #app-container .app-utility-bar { padding-right: 11px; padding-left: 70px; }
  #app-container > .player-bar { right: 8px; left: 8px; }
}
</style>
