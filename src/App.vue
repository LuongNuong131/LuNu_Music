<template>
  <div v-if="!authState.user || !authState.token" id="login-container"><Login /></div>
  <div v-else id="app-container" class="glass-app-wrapper">
    <button type="button" class="mobile-menu-toggle" :aria-expanded="mobileMenuOpen" aria-controls="lunu-navigation" @click="mobileMenuOpen = true"><span></span><span></span><span></span><b>Menu</b></button>
    <div v-if="mobileMenuOpen" class="mobile-menu-backdrop" aria-hidden="true" @click="mobileMenuOpen = false"></div>
    <Sidebar id="lunu-navigation" :mobile-open="mobileMenuOpen" @close="mobileMenuOpen = false" />
    <main class="main-content">
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
    <NotificationCenter />
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
import { onBeforeUnmount, onMounted, ref, watch } from 'vue';
import { loadSongs, songsError, songsLoading } from './data/songs';
import songs from './data/songs';
import { authState, currentView } from './store/appState';
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
.mobile-menu-toggle, .mobile-menu-backdrop { display: none; }
#app-container > .player-bar { grid-column: 1 / -1; }
@media (max-width: 760px) { #app-container { display: flex; flex-direction: column; min-height: 100vh; }.main-content { flex: 1; order: 0; padding: 72px 16px max(90px, calc(74px + env(safe-area-inset-bottom))); }.mobile-menu-toggle { position: fixed; z-index: 90; top: max(12px, env(safe-area-inset-top)); left: 14px; display: inline-flex; align-items: center; gap: 4px; height: 40px; padding: 7px 11px; border: 1px solid rgba(245,185,122,.3); border-radius: 12px; background: rgba(13,16,24,.92); color: var(--gold-bright); box-shadow: 0 10px 28px rgba(0,0,0,.25); cursor: pointer; backdrop-filter: blur(14px); }.mobile-menu-toggle span { display: block; width: 15px; height: 1.5px; border-radius: 2px; background: currentColor; }.mobile-menu-toggle b { margin-left: 4px; font: 9px var(--font-mono); letter-spacing: 1px; text-transform: uppercase; }.mobile-menu-backdrop { position: fixed; z-index: 110; inset: 0; display: block; background: rgba(3,5,10,.62); backdrop-filter: blur(2px); }.player-bar { order: 1; position: fixed !important; right: 0; bottom: 64px; left: 0; } body.mobile-menu-open { overflow: hidden; } }
@media (max-width: 380px) { .mobile-menu-toggle { padding-right: 9px; padding-left: 9px; }.mobile-menu-toggle b { display: none; } }
@media (prefers-reduced-motion: reduce) { .mobile-menu-toggle, .mobile-menu-backdrop { transition: none; } }
</style>
