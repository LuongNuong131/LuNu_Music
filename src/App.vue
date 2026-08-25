<template>
  <div v-if="!authState.user || !authState.token" id="login-container"><Login /></div>
  <div v-else id="app-container" class="glass-app-wrapper">
    <Sidebar />
    <main class="main-content">
      <AdminView v-if="currentView === 'admin'" />
      <CinemaView v-else-if="currentView === 'cinema'" />
      <LyricsManager v-else-if="currentView === 'lyrics'" :songs="songs" @play-song="playFromLibrary" />
      <PlaylistsView v-else-if="currentView === 'playlists'" :songs="songs" @play-song="playFromLibrary" />
      <ProposalView v-else-if="currentView === 'proposals'" />
      <MainView v-else :songs="songs" :only-liked="currentView === 'liked'" :loading="songsLoading" :error="songsError" @retry="loadSongs" />
    </main>
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
    <CommandPalette :visible="commandOpen" :songs="songs" :playlists="playlists" @close="commandOpen = false" @play-song="playSong" @open-playlist="openPlaylist" @action="runCommand" />
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
import { onBeforeUnmount, onMounted, ref } from 'vue';
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
import ProposalView from './views/ProposalView.vue';
import PlayerBar from './components/PlayerBar.vue';
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
const dialog = useDialog();

const playFromLibrary = (song) => playSong(song, songs);
const playFromQueue = (song) => playSong(song, [player.state.currentSong, ...player.state.queue].filter(Boolean));
const openPlaylist = (playlist) => { selectPlaylist(playlist?.id); currentView.value = 'playlists'; };
const runCommand = (action) => {
  if (action === 'home') currentView.value = 'home';
  if (action === 'search') commandOpen.value = true;
  if (action === 'toggle-shuffle') player.toggleShuffle();
  if (action === 'toggle-queue') player.state.queueVisible = true;
};

const onKeydown = (event) => {
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
onBeforeUnmount(() => window.removeEventListener('keydown', onKeydown));
</script>

<style>
#login-container { min-height: 100vh; width: 100%; }
#app-container { display: grid; grid-template-columns: 244px minmax(0, 1fr); grid-template-rows: minmax(0, 1fr) auto; height: 100vh; min-height: 600px; overflow: hidden; color: var(--text-main); background: radial-gradient(circle at 70% -20%, rgba(245,185,122,.13), transparent 32%), radial-gradient(circle at 0% 100%, rgba(113,110,255,.1), transparent 38%), var(--bg-deep); }
.main-content { min-width: 0; min-height: 0; padding: clamp(18px, 3vw, 40px); overflow: auto; }
#app-container > .player-bar { grid-column: 1 / -1; }
@media (max-width: 760px) { #app-container { display: flex; flex-direction: column; min-height: 100vh; }.main-content { flex: 1; padding: 16px; padding-bottom: 90px; }.glass-sidebar { order: 2; width: 100%; height: 64px; padding: 8px 12px; border-top: 1px solid var(--hairline); border-right: 0; }.sidebar-brand, .user-info { display: none; }.nav-menu { flex-direction: row; justify-content: center; gap: 6px; }.nav-menu button { flex: 1; justify-content: center; text-align: center; }.player-bar { order: 1; position: fixed !important; right: 0; bottom: 64px; left: 0; }.main-content { order: 0; } }
</style>
