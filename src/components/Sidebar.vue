<template>
  <aside
    class="glass-sidebar"
    :class="{ 'mobile-open': mobileOpen }"
    aria-label="Điều hướng LuNu Music"
    :inert="isPhone && !mobileOpen"
  >
    <div class="sidebar-topline">
      <button class="sidebar-brand" @click="navigate('home')" aria-label="LuNu Music, trang chủ">
        <BrandMark /><span
          ><strong>LuNu<span>music</span></strong
          ><small>Giai điệu của riêng bạn</small></span
        ></button
      ><button v-if="mobileOpen" class="drawer-close" aria-label="Đóng menu" @click="emit('close')">
        <X :size="21" />
      </button>
    </div>
    <nav class="nav-menu" aria-label="Điều hướng chính">
      <section v-for="group in navGroups" :key="group.label" class="nav-group">
        <h2 class="sidebar-label">{{ group.label }}</h2>
        <button
          v-for="item in group.items"
          :key="item.view"
          :class="{ active: currentView === item.view }"
          :aria-current="currentView === item.view ? 'page' : undefined"
          @click="navigate(item.view)"
        >
          <component :is="item.icon" :size="19" :stroke-width="1.8" /><span>{{ item.label }}</span
          ><span v-if="item.view === 'liked' && likedCount" class="nav-count">{{
            likedCount
          }}</span>
        </button>
      </section>
    </nav>
    <button class="sidebar-room" @click="navigate('rooms')">
      <Headphones :size="25" /><strong>Nghe cùng nhau</strong
      ><span>Mời một người, chung giai điệu.</span><b>Mở phòng nghe <ArrowUpRight :size="16" /></b>
    </button>
    <button class="theme-switcher" @click="toggleTheme" :aria-pressed="themeState === 'light'">
      <component :is="themeState === 'dark' ? Sun : Moon" :size="18" /><span>{{
        themeState === 'dark' ? 'Giao diện sáng' : 'Giao diện tối'
      }}</span>
    </button>
    <div class="user-info">
      <button class="profile-button" @click="navigate('account')">
        <img
          v-if="avatarUrl"
          :src="avatarUrl"
          alt=""
          class="avatar"
          @error="avatarFailed = true"
        /><span v-else class="avatar">{{ name.slice(0, 1).toUpperCase() }}</span
        ><span class="user-copy"
          ><strong>{{ name }}</strong
          ><small>{{
            authState.user?.role === 'admin' ? 'Quản trị viên' : 'Thành viên LuNu'
          }}</small></span
        ></button
      ><button @click="logoutUser" class="logout-btn" aria-label="Đăng xuất">
        <LogOut :size="18" />
      </button>
    </div>
  </aside>
</template>
<script setup>
import { computed, ref, onMounted, onBeforeUnmount } from 'vue';
import {
  Compass,
  Heart,
  ListMusic,
  Mic2,
  Clapperboard,
  Radio,
  Users,
  MessageCircle,
  CircleUserRound,
  Text,
  Lightbulb,
  Settings2,
  Headphones,
  ArrowUpRight,
  Sun,
  Moon,
  LogOut,
  X,
} from '@lucide/vue';
import BrandMark from './BrandMark.vue';
import { authState, currentView, logoutUser } from '../store/appState';
import { themeState, toggleTheme } from '../store/themeState';
import { useLibrary } from '../composables/useLibrary';
defineProps({ mobileOpen: Boolean });
const emit = defineEmits(['close']);
const { likedCount } = useLibrary();
const name = computed(() => authState.user?.display_name || authState.user?.username || 'Bạn');
const avatarFailed = ref(false);
const avatarUrl = computed(() => !avatarFailed.value && authState.user?.avatar_url);
const isPhone = ref(false);
const media = window.matchMedia('(max-width: 760px)');
const syncPhone = () => {
  isPhone.value = media.matches;
};
onMounted(() => {
  syncPhone();
  media.addEventListener('change', syncPhone);
});
onBeforeUnmount(() => media.removeEventListener('change', syncPhone));
const navGroups = computed(() => [
  {
    label: 'Âm nhạc',
    items: [
      { view: 'home', icon: Compass, label: 'Khám phá' },
      { view: 'liked', icon: Heart, label: 'Yêu thích' },
      { view: 'playlists', icon: ListMusic, label: 'Playlist của bạn' },
      { view: 'artists', icon: Mic2, label: 'Nghệ sĩ' },
    ],
  },
  {
    label: 'Kết nối',
    items: [
      { view: 'rooms', icon: Radio, label: 'Phòng nghe' },
      { view: 'cinema', icon: Clapperboard, label: 'LuNu Tea Room' },
      { view: 'friends', icon: Users, label: 'Bạn bè' },
      { view: 'chat', icon: MessageCircle, label: 'Tin nhắn' },
    ],
  },
  {
    label: 'Không gian riêng',
    items: [
      { view: 'lyrics', icon: Text, label: 'Lời bài hát' },
      { view: 'proposals', icon: Lightbulb, label: 'Đề xuất nhạc' },
      { view: 'account', icon: CircleUserRound, label: 'Hồ sơ' },
      ...(authState.user?.role === 'admin'
        ? [{ view: 'admin', icon: Settings2, label: 'Quản trị' }]
        : []),
    ],
  },
]);
const navigate = (view) => {
  currentView.value = view;
  emit('close');
};
</script>
<style scoped>
.glass-sidebar {
  width: 232px;
  min-height: 0;
  display: flex;
  flex-direction: column;
  gap: 16px;
  padding: 30px 18px 16px;
  border-right: 1px solid var(--hairline-soft);
  background: var(--panel-solid);
}
.sidebar-topline {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.sidebar-brand {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 0 8px 17px;
  border: 0;
  background: none;
  text-align: left;
  color: var(--gold);
}
.sidebar-brand svg {
  width: 38px;
  height: 38px;
}
.sidebar-brand strong {
  display: flex;
  gap: 5px;
  align-items: baseline;
  color: var(--text-main);
  font-size: 23px;
  letter-spacing: -1px;
}
.sidebar-brand strong span {
  font-size: 14px;
  font-weight: 400;
  letter-spacing: -0.4px;
}
.sidebar-brand small {
  display: block;
  margin-top: 3px;
  color: var(--text-sub);
  font-size: 9px;
}
.nav-menu {
  flex: 1;
  min-height: 0;
  overflow: auto;
  display: flex;
  flex-direction: column;
  gap: 23px;
}
.nav-group {
  display: grid;
  gap: 3px;
}
.sidebar-label {
  padding: 0 12px 8px;
  font-size: 10px;
  font-weight: 500;
  color: var(--text-faint);
}
.nav-menu button {
  display: flex;
  gap: 12px;
  align-items: center;
  min-height: 42px;
  padding: 10px 12px;
  border: 0;
  border-radius: 9px;
  background: none;
  color: var(--text-sub);
  text-align: left;
  font-size: 12px;
}
.nav-menu button:hover {
  background: var(--glass);
  color: var(--text-main);
}
.nav-menu button.active {
  background: var(--accent-soft);
  color: var(--gold);
  font-weight: 600;
}
.nav-count {
  margin-left: auto;
  font-size: 10px;
}
.sidebar-room {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 9px;
  flex: none;
  padding: 16px;
  border: 1px solid var(--hairline);
  border-radius: 14px;
  background: var(--surface-2);
  text-align: left;
  color: var(--text-main);
}
.sidebar-room > svg {
  color: var(--gold);
}
.sidebar-room strong {
  font-size: 12px;
}
.sidebar-room > span {
  font-size: 9px;
  color: var(--text-sub);
}
.sidebar-room b {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  margin-top: 5px;
  font-size: 10px;
  color: var(--gold);
}
.theme-switcher {
  display: flex;
  gap: 12px;
  align-items: center;
  padding: 8px 12px;
  border: 0;
  background: none;
  color: var(--text-sub);
  font-size: 11px;
}
.user-info {
  display: flex;
  align-items: center;
  gap: 6px;
  padding-top: 15px;
  border-top: 1px solid var(--hairline);
}
.profile-button {
  display: flex;
  align-items: center;
  gap: 9px;
  flex: 1;
  min-width: 0;
  padding: 0;
  border: 0;
  background: none;
  text-align: left;
  color: var(--text-main);
}
.avatar {
  display: grid;
  place-items: center;
  flex: none;
  width: 34px;
  height: 34px;
  border-radius: 50%;
  background: var(--accent-soft);
  color: var(--gold);
  font-size: 14px;
  object-fit: cover;
}
.user-copy {
  display: grid;
  gap: 4px;
  min-width: 0;
}
.user-copy strong {
  font-size: 11px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.user-copy small {
  font-size: 9px;
  color: var(--text-faint);
}
.logout-btn,
.drawer-close {
  display: grid;
  place-items: center;
  flex: none;
  width: 36px;
  height: 40px;
  border: 0;
  background: none;
  color: var(--text-sub);
}
.drawer-close {
  display: none;
}
@media (max-height: 850px) {
  .sidebar-room {
    display: none;
  }
  .nav-menu {
    gap: 15px;
  }
  .glass-sidebar {
    padding-top: 23px;
    gap: 12px;
  }
  .nav-menu button {
    min-height: 38px;
  }
}
@media (max-width: 760px) {
  .glass-sidebar {
    position: fixed;
    z-index: 170;
    inset: 0 auto 0 0;
    width: min(310px, 86vw);
    height: 100dvh;
    transform: translateX(-100%);
    transition: transform 0.2s ease;
    padding-top: 24px;
    box-shadow: none;
  }
  .glass-sidebar.mobile-open {
    transform: translateX(0);
    box-shadow: 20px 0 60px #0004;
  }
  .drawer-close {
    display: grid;
  }
  .nav-menu button {
    min-height: 44px;
  }
  .sidebar-room {
    display: none;
  }
}
@media (prefers-reduced-motion: reduce) {
  .glass-sidebar {
    transition: none;
  }
}
</style>
