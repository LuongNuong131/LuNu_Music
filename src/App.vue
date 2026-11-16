<template>
  <div v-if="!authState.user || !authState.token" id="login-container"><Login /></div>
  <div v-else id="app-container" class="music-app">
    <a class="skip-link" href="#main-workspace">Bỏ qua đến nội dung</a>
    <button
      ref="menuToggle"
      type="button"
      class="mobile-menu-toggle"
      :aria-expanded="mobileMenuOpen"
      aria-controls="lunu-navigation"
      aria-label="Mở menu điều hướng"
      @click="mobileMenuOpen = !mobileMenuOpen"
    >
      <Menu :size="21" />
    </button>
    <div
      v-if="mobileMenuOpen"
      class="mobile-menu-backdrop"
      aria-hidden="true"
      @click="mobileMenuOpen = false"
    ></div>
    <Sidebar id="lunu-navigation" :mobile-open="mobileMenuOpen" @close="mobileMenuOpen = false" />
    <main id="main-workspace" class="main-content" tabindex="-1" :inert="mobileMenuOpen">
      <div class="app-utility-bar" aria-label="Thanh công cụ nhanh">
        <div class="utility-context">
          <Headphones :size="17" /><span>Không gian của bạn</span
          ><ChevronRight :size="13" /><strong>{{ viewTitle }}</strong>
        </div>
        <div class="utility-actions">
          <button class="utility-ai" aria-label="Mở trợ lý chọn nhạc" @click="conciergeOpen = true">
            <Sparkles :size="16" /><span>Chọn nhạc cùng AI</span></button
          ><NotificationCenter compact /><button
            class="utility-theme"
            :aria-pressed="themeState === 'light'"
            :aria-label="themeState === 'dark' ? 'Chuyển giao diện sáng' : 'Chuyển giao diện tối'"
            @click="toggleTheme"
          >
            <component :is="themeState === 'dark' ? Sun : Moon" :size="18" /></button
          ><button
            class="utility-search"
            aria-label="Mở tìm kiếm nhanh"
            @click="commandOpen = true"
          >
            <Search :size="17" /><span>Tìm nhanh</span><kbd>Ctrl K</kbd>
          </button>
        </div>
      </div>
      <Transition name="workspace" mode="out-in">
        <div :key="currentView" class="workspace-view">
          <AdminView v-if="currentView === 'admin'" />
          <CinemaView v-else-if="currentView === 'cinema'" />
          <LyricsManager
            v-else-if="currentView === 'lyrics'"
            :songs="songs"
            @play-song="playFromLibrary"
          />
          <PlaylistsView
            v-else-if="currentView === 'playlists'"
            :songs="songs"
            @play-song="playFromLibrary"
          />
          <ArtistsView
            v-else-if="currentView === 'artists'"
            :songs="songs"
            @play-song="playFromLibrary"
          />
          <ProposalView v-else-if="currentView === 'proposals'" />
          <AccountView v-else-if="currentView === 'account'" />
          <RoomsView v-else-if="currentView === 'rooms'" />
          <FriendsView v-else-if="currentView === 'friends'" />
          <ChatView v-else-if="currentView === 'chat'" />
          <MainView
            v-else
            :songs="songs"
            :only-liked="currentView === 'liked'"
            :loading="songsLoading"
            :error="songsError"
            @retry="loadSongs"
          />
        </div>
      </Transition>
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
      :error="player.state.error"
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
    <CommandPalette
      :visible="commandOpen"
      :songs="songs"
      :playlists="playlists"
      @close="commandOpen = false"
      @play-song="playFromLibrary"
      @open-playlist="openPlaylist"
      @action="runCommand"
    />
    <AIConcierge
      :visible="conciergeOpen"
      @close="conciergeOpen = false"
      @play-song="playFromLibrary"
      @queue-song="queueFromConcierge"
    />
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
import {
  computed,
  defineAsyncComponent,
  nextTick,
  onBeforeUnmount,
  onMounted,
  ref,
  watch,
} from 'vue';
import { ChevronRight, Headphones, Menu, Moon, Search, Sparkles, Sun } from '@lucide/vue';
import { loadSongs, songsError, songsLoading } from './data/songs';
import songs from './data/songs';
import { authState, currentView } from './store/appState';
import { resetAurora, setAuroraFromCover, themeState, toggleTheme } from './store/themeState';
import { playSong, usePlayer } from './store/playerState';
import { usePlaylists } from './composables/usePlaylists';
import Login from './views/Login.vue';
const AdminView = defineAsyncComponent(() => import('./views/AdminView.vue'));
const CinemaView = defineAsyncComponent(() => import('./views/CinemaView.vue'));
import Sidebar from './components/Sidebar.vue';
import MainView from './components/MainView.vue';
const LyricsManager = defineAsyncComponent(() => import('./components/LyricsManager.vue'));
const PlaylistsView = defineAsyncComponent(() => import('./views/PlaylistsView.vue'));
const ArtistsView = defineAsyncComponent(() => import('./views/ArtistsView.vue'));
const ProposalView = defineAsyncComponent(() => import('./views/ProposalView.vue'));
const AccountView = defineAsyncComponent(() => import('./views/AccountView.vue'));
const RoomsView = defineAsyncComponent(() => import('./views/RoomsView.vue'));
const FriendsView = defineAsyncComponent(() => import('./views/FriendsView.vue'));
const ChatView = defineAsyncComponent(() => import('./views/ChatView.vue'));
import PlayerBar from './components/PlayerBar.vue';
import RoomSyncBridge from './components/RoomSyncBridge.vue';
import NowPlayingView from './components/NowPlayingView.vue';
import QueuePanel from './components/QueuePanel.vue';
import CommandPalette from './components/CommandPalette.vue';
const AIConcierge = defineAsyncComponent(() => import('./components/AIConcierge.vue'));
import Toast from './components/Toast.vue';
import ConfirmModal from './components/ConfirmModal.vue';
import NotificationCenter from './components/NotificationCenter.vue';
import { useDialog } from './composables/useDialog';

const viewTitle = computed(
  () =>
    ({
      home: 'Khám phá',
      liked: 'Yêu thích',
      playlists: 'Playlist',
      artists: 'Ca sĩ',
      lyrics: 'Lyrics Lab',
      cinema: 'LuNu Tea Room',
      proposals: 'Đề xuất media',
      account: 'Hồ sơ',
      rooms: 'Phòng nghe',
      friends: 'Bạn bè',
      chat: 'Chat',
      admin: 'Quản trị',
    })[currentView.value] || 'Tổng quan',
);
const player = usePlayer();
const { playlists, selectPlaylist } = usePlaylists();
const commandOpen = ref(false);
const conciergeOpen = ref(false);
const mobileMenuOpen = ref(false);
const menuToggle = ref(null);
const dialog = useDialog();
watch(mobileMenuOpen, async (open) => {
  document.body.classList.toggle('mobile-menu-open', open);
  await nextTick();
  if (open) document.querySelector('#lunu-navigation button')?.focus();
  else menuToggle.value?.focus();
});
watch(
  () => authState.token,
  (token) => {
    if (token) loadSongs();
    else songs.splice(0);
  },
  { immediate: true },
);
watch(
  () => player.state.currentSong?.cover,
  (cover) => {
    if (cover) setAuroraFromCover(cover);
    else resetAurora();
  },
  { immediate: true },
);

const playFromLibrary = (song, collection = songs) =>
  playSong(song, Array.isArray(collection) && collection.length ? collection : songs);
const playFromQueue = (song) =>
  playSong(song, [player.state.currentSong, ...player.state.queue].filter(Boolean));
const queueFromConcierge = (song) => player.addToQueue(song);
const openPlaylist = (playlist) => {
  selectPlaylist(playlist?.id);
  currentView.value = 'playlists';
};
const runCommand = (action) => {
  if (action === 'home') currentView.value = 'home';
  if (action === 'search') commandOpen.value = true;
  if (action === 'toggle-shuffle') player.toggleShuffle();
  if (action === 'toggle-queue') player.state.queueVisible = true;
};

const onKeydown = (event) => {
  if (event.key === 'Escape' && mobileMenuOpen.value) {
    mobileMenuOpen.value = false;
    return;
  }
  const typing =
    event.target?.closest?.('input, textarea, select, button, a, [role=slider], [role=dialog]') ||
    event.target?.isContentEditable;
  if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === 'k') {
    event.preventDefault();
    commandOpen.value = !commandOpen.value;
    return;
  }
  if (mobileMenuOpen.value && event.key === 'Tab') {
    const targets = [...document.querySelectorAll('#lunu-navigation button:not(:disabled)')].filter(
      (el) => el.offsetParent !== null,
    );
    const first = targets[0],
      last = targets.at(-1);
    if (event.shiftKey && document.activeElement === first) {
      event.preventDefault();
      last?.focus();
    } else if (!event.shiftKey && document.activeElement === last) {
      event.preventDefault();
      first?.focus();
    }
  }
  if (event.defaultPrevented || typing || !player.state.currentSong) return;
  if (event.code === 'Space') {
    event.preventDefault();
    player.togglePlay();
  } else if (event.key === 'ArrowLeft') player.seek(player.state.currentTime - 5);
  else if (event.key === 'ArrowRight') player.seek(player.state.currentTime + 5);
  else if (event.key === 'ArrowUp') player.setVolume(player.state.volume + 0.05);
  else if (event.key === 'ArrowDown') player.setVolume(player.state.volume - 0.05);
  else if (event.key.toLowerCase() === 'm') player.toggleMute();
  else if (event.key.toLowerCase() === 'n') player.next();
  else if (event.key.toLowerCase() === 'p') player.previous();
  else if (event.key.toLowerCase() === 's') player.toggleShuffle();
  else if (event.key.toLowerCase() === 'r') player.toggleRepeat();
};

onMounted(() => {
  window.addEventListener('keydown', onKeydown);
});
onBeforeUnmount(() => {
  window.removeEventListener('keydown', onKeydown);
  document.body.classList.remove('mobile-menu-open');
});
</script>

<style>
#login-container {
  height: 100%;
  overflow: auto;
}
.skip-link {
  position: fixed;
  top: 10px;
  left: 10px;
  z-index: 2000;
  padding: 12px 16px;
  border-radius: 8px;
  background: var(--gold);
  color: var(--brand-ink);
  transform: translateY(-160%);
}
.skip-link:focus {
  transform: translateY(0);
}
#app-container {
  display: grid;
  grid-template-columns: 232px minmax(0, 1fr);
  grid-template-rows: minmax(0, 1fr) auto;
  height: 100dvh;
  min-height: 0;
  overflow: hidden;
  background: var(--bg-deep);
  color: var(--text-main);
}
.main-content {
  min-width: 0;
  min-height: 0;
  padding: 22px clamp(22px, 2.5vw, 42px) 0;
  overflow: auto;
  scrollbar-gutter: stable;
}
.main-content:focus {
  outline: none;
}
#app-container > .player-bar {
  grid-column: 1/-1;
}
.workspace-view {
  min-height: 0;
}
.app-utility-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  max-width: 1520px;
  margin: 0 auto 25px;
  padding-bottom: 20px;
  border-bottom: 1px solid var(--hairline-soft);
  min-height: 44px;
}
.utility-context {
  display: flex;
  align-items: center;
  gap: 9px;
  font-size: 10px;
  color: var(--text-faint);
}
.utility-context > svg:first-child {
  color: var(--gold);
}
.utility-context strong {
  color: var(--text-sub);
  font-weight: 500;
}
.utility-actions {
  display: flex;
  align-items: center;
  gap: 9px;
}
.utility-actions > button {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  min-height: 36px;
  padding: 8px 11px;
  border: 1px solid var(--hairline);
  border-radius: 9px;
  background: var(--glass);
  color: var(--text-sub);
  font-size: 10px;
}
.utility-actions > button:hover {
  background: var(--accent-soft);
  color: var(--gold);
}
.utility-actions > .utility-ai {
  background: var(--accent-soft);
  color: var(--gold);
  border-color: transparent;
}
.utility-search kbd {
  color: var(--text-faint);
  padding: 2px 4px;
  border: 1px solid var(--hairline);
  border-radius: 4px;
  font-family: var(--font-body);
  font-size: 9px;
}
.mobile-menu-toggle,
.mobile-menu-backdrop {
  display: none;
}
.workspace-enter-active,
.workspace-leave-active {
  transition: opacity 0.12s ease;
}
.workspace-enter-from,
.workspace-leave-to {
  opacity: 0;
}
@media (max-width: 1020px) {
  .utility-context > span,
  .utility-context > svg:nth-child(3) {
    display: none;
  }
  .utility-ai > span {
    display: none;
  }
}
@media (max-width: 760px) {
  #app-container {
    display: flex;
    flex-direction: column;
  }
  .main-content {
    flex: 1;
    padding: 78px 17px 105px;
  }
  .app-utility-bar {
    position: fixed;
    inset: 0 0 auto;
    z-index: 100;
    height: 61px;
    padding: 10px 14px 10px 64px;
    margin: 0;
    border-bottom: 1px solid var(--hairline);
    background: var(--panel-solid);
  }
  .utility-context {
    gap: 6px;
    font-size: 11px;
  }
  .utility-context > svg {
    display: none;
  }
  .utility-actions {
    gap: 6px;
  }
  .utility-actions > button {
    width: 35px;
    padding: 6px;
  }
  .utility-actions > .utility-ai {
    display: none;
  }
  .utility-search > span,
  .utility-search > kbd {
    display: none;
  }
  .mobile-menu-toggle {
    position: fixed;
    z-index: 105;
    top: 11px;
    left: 14px;
    display: grid;
    place-items: center;
    width: 38px;
    height: 38px;
    border: 1px solid var(--hairline);
    border-radius: 10px;
    background: var(--panel-solid);
    color: var(--text-main);
  }
  .mobile-menu-backdrop {
    position: fixed;
    z-index: 160;
    inset: 0;
    display: block;
    background: #080b18a6;
    backdrop-filter: blur(3px);
  }
  #app-container > .player-bar {
    position: fixed;
    inset: auto 10px max(10px, env(safe-area-inset-bottom));
    z-index: 140;
  }
  .music-app > .glass-sidebar {
    flex: none;
  }
  body.mobile-menu-open {
    overflow: hidden;
  }
}
@media (prefers-reduced-motion: reduce) {
  .workspace-enter-active,
  .workspace-leave-active {
    transition: none;
  }
}
</style>
