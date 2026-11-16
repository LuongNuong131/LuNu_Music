<template>
  <section class="music-workspace">
    <div class="listening-content">
      <header class="welcome-heading">
        <div>
          <p>{{ greeting }}, {{ listenerName }}</p>
          <h1>{{ onlyLiked ? 'Nhạc bạn yêu thích' : 'Hôm nay, nghe gì?' }}</h1>
        </div>
        <button class="quiet-button" @click="state.queueVisible = true">
          <ListMusic :size="18" /><span>Hàng đợi</span>
        </button>
      </header>
      <section v-if="!onlyLiked" class="listening-feature" aria-labelledby="feature-title">
        <div class="feature-copy">
          <span class="feature-tag"><AudioLines :size="16" /> Không gian âm nhạc của bạn</span>
          <h2 id="feature-title">Bật nhạc.<br />Bật cảm hứng.</h2>
          <p>Để những giai điệu quen thuộc<br />đưa bạn đến một tâm trạng mới.</p>
          <button class="feature-play" :disabled="!recommendations.length" @click="playMix">
            <Play :size="17" fill="currentColor" /> Nghe mix của bạn</button
          ><span class="feature-note">{{ songs.length }} bài hát, một thế giới riêng.</span>
        </div>
        <img
          class="feature-art"
          src="/images/listening-room.svg"
          alt="Đĩa nhạc vinyl trên bìa đĩa màu tím nhạt"
          fetchpriority="high"
        />
      </section>
      <section
        v-if="!onlyLiked && recommendations.length"
        class="rotation-section"
        aria-labelledby="rotation-title"
      >
        <div class="section-heading">
          <div>
            <h2 id="rotation-title">Có thể bạn muốn nghe</h2>
            <p>Giai điệu quen, cảm xúc mới.</p>
          </div>
          <button class="text-button" @click="shuffleMix">
            <Shuffle :size="16" /> Đổi giai điệu
          </button>
        </div>
        <div class="rotation-grid">
          <article v-for="song in recommendations" :key="song.id" class="rotation-card">
            <button
              class="rotation-art"
              @click="play(song, recommendations)"
              :aria-label="`Phát ${song.title}`"
            >
              <img
                :src="songArtwork(song)"
                :alt="`Bìa ${song.title}`"
                loading="lazy"
                @error="handleImageError"
              /><span class="art-play"
                ><Pause
                  v-if="isCurrent(song) && state.isPlaying"
                  :size="20"
                  fill="currentColor" /><Play v-else :size="20" fill="currentColor" /></span
              ><span v-if="isCurrent(song)" class="playing-label"
                ><AudioLines :size="14" /> Đang chọn</span
              >
            </button>
            <div class="rotation-meta">
              <div>
                <h3>{{ song.title }}</h3>
                <p>{{ song.artist || 'Chưa rõ nghệ sĩ' }}</p>
              </div>
              <button
                class="heart-button"
                :class="{ liked: isLiked(song.id) }"
                :aria-pressed="isLiked(song.id)"
                :aria-label="
                  isLiked(song.id) ? `Bỏ yêu thích ${song.title}` : `Yêu thích ${song.title}`
                "
                @click="toggleLike(song)"
              >
                <Heart :size="17" :fill="isLiked(song.id) ? 'currentColor' : 'none'" />
              </button>
            </div>
          </article>
        </div>
      </section>
      <section class="collection" aria-labelledby="collection-title">
        <div class="section-heading collection-heading">
          <div>
            <h2 id="collection-title">
              {{ onlyLiked ? 'Bộ sưu tập yêu thích' : 'Thư viện của bạn' }}
            </h2>
            <p>
              {{ filteredSongs.length }} bài hát{{
                query ? ' phù hợp' : ' để bạn thả mình vào âm nhạc'
              }}
            </p>
          </div>
          <button class="text-button" :disabled="!filteredSongs.length" @click="playAll">
            <Play :size="16" /> Phát tất cả
          </button>
        </div>
        <div class="library-toolbar">
          <label class="library-search"
            ><Search :size="18" /><input
              v-model="query"
              type="search"
              placeholder="Tìm bài hát, nghệ sĩ..."
              aria-label="Tìm bài hát hoặc nghệ sĩ" /></label
          ><select v-model="sortBy" aria-label="Sắp xếp thư viện">
            <option value="recent">Mới cập nhật</option>
            <option value="title">Tên bài hát</option>
            <option value="artist">Nghệ sĩ</option>
          </select>
          <div class="view-toggle" role="group" aria-label="Kiểu hiển thị thư viện">
            <button
              :class="{ active: viewMode === 'list' }"
              :aria-pressed="viewMode === 'list'"
              aria-label="Hiển thị dạng danh sách"
              @click="viewMode = 'list'"
            >
              <List :size="18" /></button
            ><button
              :class="{ active: viewMode === 'grid' }"
              :aria-pressed="viewMode === 'grid'"
              aria-label="Hiển thị dạng lưới"
              @click="viewMode = 'grid'"
            >
              <LayoutGrid :size="17" />
            </button>
          </div>
        </div>
        <div v-if="error" class="library-alert" role="alert">
          <CloudOff :size="19" />
          <p>{{ error }}<span v-if="songs.length"> Đang hiển thị thư viện dự phòng.</span></p>
          <button @click="$emit('retry')">Thử lại</button>
        </div>
        <div v-if="loading" class="loading-tracks" aria-label="Đang tải thư viện" aria-busy="true">
          <div v-for="n in 5" :key="n"><span></span><i></i><i></i></div>
        </div>
        <div v-else-if="!filteredSongs.length" class="collection-empty">
          <component :is="onlyLiked ? Heart : Search" :size="34" />
          <h3>
            {{
              onlyLiked && !query ? 'Giữ lại những giai điệu bạn yêu' : 'Chưa có bài hát phù hợp'
            }}
          </h3>
          <p>
            {{
              onlyLiked && !query
                ? 'Chạm vào trái tim cạnh một bài hát để thêm vào đây.'
                : query
                  ? 'Thử tên bài hát hoặc nghệ sĩ khác.'
                  : 'Thêm bản nhạc đầu tiên để bắt đầu thư viện của bạn.'
            }}
          </p>
          <button v-if="query" class="quiet-button" @click="query = ''">Xóa tìm kiếm</button>
        </div>
        <div v-else class="track-collection" :class="{ 'grid-mode': viewMode === 'grid' }">
          <div v-if="viewMode === 'list'" class="track-table-head" aria-hidden="true">
            <span>#</span><span>Bài hát</span><span>Nghệ sĩ</span><Clock3 :size="14" />
          </div>
          <article
            v-for="(song, index) in visibleSongs"
            :key="song.id"
            class="library-track"
            :class="{ 'is-current': isCurrent(song) }"
          >
            <button class="track-number" :aria-label="`Phát ${song.title}`" @click="play(song)">
              <AudioLines v-if="isCurrent(song) && state.isPlaying" :size="16" /><span v-else>{{
                String(index + 1).padStart(2, '0')
              }}</span
              ><Play class="number-play" :size="14" fill="currentColor" /></button
            ><button class="track-cover" :aria-label="`Phát ${song.title}`" @click="play(song)">
              <img
                :src="songArtwork(song)"
                :alt="`Bìa ${song.title}`"
                loading="lazy"
                @error="handleImageError"
              /><span><Play :size="20" fill="currentColor" /></span></button
            ><button class="track-name" @click="play(song)">
              <strong>{{ song.title }}</strong><small>{{ song.artist || 'Chưa rõ nghệ sĩ' }}</small>
            </button>
            <p class="track-artist-name">{{ song.artist || 'Chưa rõ nghệ sĩ' }}</p>
            <span class="track-duration">{{ durationLabel(song.duration) }}</span>
            <div class="track-buttons">
              <button
                class="heart-button"
                :class="{ liked: isLiked(song.id) }"
                :aria-pressed="isLiked(song.id)"
                :aria-label="
                  isLiked(song.id) ? `Bỏ yêu thích ${song.title}` : `Yêu thích ${song.title}`
                "
                @click="toggleLike(song)"
              >
                <Heart :size="17" :fill="isLiked(song.id) ? 'currentColor' : 'none'" /></button
              ><button
                class="track-action"
                :aria-label="`Thêm ${song.title} vào hàng đợi`"
                @click="queueSong(song)"
              >
                <ListPlus :size="18" /></button
              ><button
                class="track-action"
                :aria-label="`Thêm ${song.title} vào playlist`"
                @click="playlistMenuSong = song"
              >
                <Plus :size="18" />
              </button>
            </div>
          </article>
        </div>
        <button
          v-if="visibleSongs.length < filteredSongs.length"
          class="load-more"
          @click="visibleCount += 24"
        >
          Xem thêm {{ Math.min(24, filteredSongs.length - visibleCount) }} bài hát
          <ChevronDown :size="16" />
        </button>
      </section>
      <section v-if="!onlyLiked && history.length" class="recent-section">
        <div class="section-heading">
          <div>
            <h2>Nghe lại một chút</h2>
            <p>Những bài bạn vừa ghé qua.</p>
          </div>
        </div>
        <div class="recent-list">
          <button v-for="item in history.slice(0, 4)" :key="item.id" @click="play(item.song)">
            <img
              :src="songArtwork(item.song)"
              alt=""
              loading="lazy"
              @error="handleImageError"
            /><span
              ><strong>{{ item.song.title }}</strong
              ><small>{{ item.song.artist }}</small></span
            ><Play :size="17" />
          </button>
        </div>
      </section>
      <p class="collection-footer">
        <AudioLines :size="16" /> LuNu Music. Một chút nhạc, một chút bình yên.
      </p>
    </div>
    <aside class="listening-aside" aria-label="Không gian nghe nhạc">
      <div class="aside-heading">
        <h2>{{ state.currentSong ? 'Đang phát' : 'Chờ một giai điệu' }}</h2>
        <AudioLines :size="19" />
      </div>
      <div class="aside-cover">
        <img
          v-if="state.currentSong"
          :src="songArtwork(state.currentSong)"
          :alt="`Bìa ${state.currentSong.title}`"
          @error="handleImageError"
        /><img v-else src="/images/listening-room.svg" alt="Đĩa nhạc đang chờ phát" />
      </div>
      <div class="aside-song">
        <h3>{{ state.currentSong?.title || 'Bản nhạc tiếp theo là gì?' }}</h3>
        <p>{{ state.currentSong?.artist || 'Chọn một bài hát và tận hưởng.' }}</p>
      </div>
      <button
        class="aside-listen"
        :disabled="!state.currentSong && !recommendations.length"
        @click="state.currentSong ? (state.nowPlayingVisible = true) : playMix()"
      >
        <component :is="state.currentSong ? Maximize2 : Play" :size="17" />{{
          state.currentSong ? 'Mở trình phát' : 'Bắt đầu nghe'
        }}
      </button>
      <div class="up-next-heading">
        <h3>Tiếp theo</h3>
        <button aria-label="Mở hàng đợi" @click="state.queueVisible = true">
          <ArrowUpRight :size="18" />
        </button>
      </div>
      <div v-if="upNext.length" class="up-next-list">
        <button
          v-for="(song, index) in upNext"
          :key="`${song.id}-${index}`"
          @click="play(song, upNext)"
        >
          <img :src="songArtwork(song)" alt="" loading="lazy" @error="handleImageError" /><span
            ><strong>{{ song.title }}</strong
            ><small>{{ song.artist }}</small></span
          ><Play :size="13" />
        </button>
      </div>
      <p v-else class="aside-empty">Thêm bài vào hàng đợi để giữ âm nhạc tiếp nối.</p>
      <div class="listening-tip">
        <Headphones :size="23" />
        <p>Dành một khoảng lặng<br />cho những điều bạn thích.</p>
      </div>
    </aside>
    <Teleport to="body"
      ><div
        v-if="playlistMenuSong"
        class="playlist-picker-backdrop"
        @click.self="playlistMenuSong = null"
        @keydown.esc="playlistMenuSong = null"
      >
        <section
          class="playlist-picker"
          role="dialog"
          aria-modal="true"
          aria-labelledby="playlist-picker-title"
          tabindex="-1"
          ref="pickerRef"
        >
          <header>
            <div>
              <h2 id="playlist-picker-title">Thêm vào playlist</h2>
              <p>{{ playlistMenuSong.title }}</p>
            </div>
            <button
              class="quiet-button"
              aria-label="Đóng chọn playlist"
              @click="playlistMenuSong = null"
            >
              <X :size="20" />
            </button>
          </header>
          <div v-if="playlists.length" class="playlist-picker-list">
            <button
              v-for="playlist in playlists"
              :key="playlist.id"
              :disabled="hasSong(playlist, playlistMenuSong.id)"
              @click="addSongToPlaylist(playlist)"
            >
              <ListMusic :size="20" /><span
                ><strong>{{ playlist.name }}</strong
                ><small>{{
                  hasSong(playlist, playlistMenuSong.id)
                    ? 'Đã có trong playlist'
                    : `${playlist.songIds.length} bài hát`
                }}</small></span
              ><Plus :size="18" />
            </button>
          </div>
          <div v-else class="picker-empty">
            <p>Bạn chưa có playlist nào.</p>
            <button class="quiet-button" @click="goToPlaylists">Tạo playlist đầu tiên</button>
          </div>
        </section>
      </div></Teleport
    >
  </section>
</template>
<script setup>
import { computed, ref, watch } from 'vue';
import { useDialogFocus } from '../composables/useDialogFocus';
import {
  AudioLines,
  ArrowUpRight,
  ChevronDown,
  Clock3,
  CloudOff,
  Headphones,
  Heart,
  LayoutGrid,
  List,
  ListMusic,
  ListPlus,
  Maximize2,
  Pause,
  Play,
  Plus,
  Search,
  Shuffle,
  X,
} from '@lucide/vue';
import songs from '../data/songs';
import { useLibrary } from '../composables/useLibrary';
import { addToQueue, playSong, playerState, togglePlay } from '../store/playerState';
import { usePlaylists } from '../composables/usePlaylists';
import { useToast } from '../composables/useToast';
import { authState, currentView } from '../store/appState';
import { normalizeSearch } from '../utils/search';
import { songArtwork } from '../utils/artwork';
const props = defineProps({
  songs: { type: Array, default: () => songs },
  loading: Boolean,
  error: { type: String, default: '' },
  onlyLiked: Boolean,
});
defineEmits(['retry']);
const query = ref('');
const sortBy = ref('recent');
const viewMode = ref('list');
const visibleCount = ref(24);
const rotationOffset = ref(0);
const fallbackCover = '/images/ChoCiu.jpg';
const state = playerState;
const listenerName = computed(
  () => authState.user?.display_name || authState.user?.username || 'bạn',
);
const greeting = computed(() => {
  const hour = new Date().getHours();
  return hour < 12 ? 'Chào buổi sáng' : hour < 18 ? 'Chào buổi chiều' : 'Chào buổi tối';
});
const { isLiked, toggleLike, history, recordPlay } = useLibrary();
const { playlists, addSong, hasSong } = usePlaylists();
const toast = useToast();
const playlistMenuSong = ref(null);
const pickerRef = ref(null);
useDialogFocus(
  computed(() => Boolean(playlistMenuSong.value)),
  pickerRef,
  () => {
    playlistMenuSong.value = null;
  },
);
const handleImageError = (event) => {
  const image = event.currentTarget;
  if (!image || image.dataset.fallbackApplied === 'true') return;
  image.dataset.fallbackApplied = 'true';
  image.src = fallbackCover;
};
const preferences = computed(() => {
  const artists = new Set(
    props.songs.filter((song) => isLiked(song.id)).map((song) => normalizeSearch(song.artist)),
  );
  const recent = new Map(
    history.value.map((item, index) => [String(item.songId), Math.max(0, 18 - index)]),
  );
  return { artists, recent };
});
const recommendationScore = (song) =>
  (isLiked(song.id) ? 50 : 0) +
  (preferences.value.artists.has(normalizeSearch(song.artist)) ? 25 : 0) +
  (preferences.value.recent.get(String(song.id)) || 8);
const rankedSongs = computed(() =>
  [...props.songs].sort((a, b) => recommendationScore(b) - recommendationScore(a)),
);
const recommendations = computed(() => {
  const list = rankedSongs.value;
  if (!list.length) return [];
  const start = rotationOffset.value % list.length;
  return [...list.slice(start), ...list.slice(0, start)].slice(0, 5);
});
const filteredSongs = computed(() => {
  const term = normalizeSearch(query.value);
  const list = props.songs.filter(
    (song) =>
      (!props.onlyLiked || isLiked(song.id)) &&
      (!term || normalizeSearch(`${song.title} ${song.artist}`).includes(term)),
  );
  return [...list].sort((a, b) =>
    sortBy.value === 'title'
      ? a.title.localeCompare(b.title, 'vi')
      : sortBy.value === 'artist'
        ? (a.artist || '').localeCompare(b.artist || '', 'vi')
        : 0,
  );
});
const visibleSongs = computed(() => filteredSongs.value.slice(0, visibleCount.value));
watch([query, sortBy, () => props.onlyLiked], () => {
  visibleCount.value = 24;
});
const isCurrent = (song) => String(state.currentSong?.id) === String(song.id);
const play = (song, collection = filteredSongs.value) => {
  if (isCurrent(song)) {
    togglePlay();
    return;
  }
  playSong(song, collection);
  recordPlay(song);
};
const playAll = () => {
  if (filteredSongs.value[0]) {
    playSong(filteredSongs.value[0], filteredSongs.value);
    recordPlay(filteredSongs.value[0]);
  }
};
const playMix = () => {
  if (recommendations.value[0]) {
    playSong(recommendations.value[0], recommendations.value);
    recordPlay(recommendations.value[0]);
  }
};
const shuffleMix = () => {
  rotationOffset.value += 5;
};
const queueSong = (song) => {
  addToQueue(song);
  toast.showToast(`Đã thêm “${song.title}” vào hàng đợi.`, { type: 'success' });
};
const addSongToPlaylist = (playlist) => {
  if (!playlistMenuSong.value) return;
  addSong(playlist.id, playlistMenuSong.value.id);
  playlistMenuSong.value = null;
};
const goToPlaylists = () => {
  playlistMenuSong.value = null;
  currentView.value = 'playlists';
};
const upNext = computed(() =>
  state.queue.length
    ? state.queue.slice(0, 3)
    : recommendations.value.filter((song) => !isCurrent(song)).slice(0, 3),
);
const durationLabel = (duration) => {
  const n = Number(duration);
  return Number.isFinite(n) && n > 0
    ? `${Math.floor(n / 60)}:${String(Math.floor(n % 60)).padStart(2, '0')}`
    : '—';
};
</script>
<style scoped>
.music-workspace {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 240px;
  gap: 30px;
  max-width: 1520px;
  margin: auto;
}
.listening-content {
  min-width: 0;
}
.welcome-heading {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 18px;
  margin: 10px 0 26px;
}
.welcome-heading p {
  font-size: 12px;
  color: var(--text-sub);
  margin-bottom: 7px;
}
.welcome-heading h1 {
  font-size: 27px;
  letter-spacing: -1px;
  line-height: 1.35;
  font-weight: 650;
}
.quiet-button,
.text-button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  min-height: 40px;
  padding: 8px 13px;
  border: 1px solid var(--hairline);
  border-radius: 9px;
  background: var(--glass);
  color: var(--text-sub);
  font-size: 11px;
  white-space: nowrap;
}
.text-button {
  border: 0;
  background: transparent;
  padding: 8px 0;
  color: var(--gold);
}
.quiet-button:hover {
  background: var(--accent-soft);
  color: var(--gold);
}
.listening-feature {
  position: relative;
  overflow: hidden;
  display: flex;
  align-items: center;
  min-height: 300px;
  border-radius: 20px;
  background: #d9d0ff;
  color: #25203e;
}
.feature-copy {
  position: relative;
  z-index: 1;
  padding: 30px 34px;
  width: 60%;
}
.feature-tag {
  display: flex;
  align-items: center;
  gap: 7px;
  font-size: 10px;
  font-weight: 500;
  color: #554675;
}
.feature-copy h2 {
  margin: 18px 0 14px;
  font-size: clamp(32px, 3.1vw, 47px);
  font-weight: 750;
  line-height: 1.23;
  letter-spacing: -1.8px;
}
.feature-copy p {
  font-size: 11px;
  line-height: 1.8;
  color: #5c5075;
}
.feature-play {
  display: flex;
  align-items: center;
  gap: 9px;
  min-height: 43px;
  margin-top: 22px;
  padding: 11px 17px;
  border: 0;
  border-radius: 25px;
  background: #25203e;
  color: #fff;
  font-size: 11px;
  font-weight: 600;
}
.feature-play:hover {
  background: #44365e;
}
.feature-note {
  display: block;
  margin-top: 13px;
  font-size: 9px;
  color: #5c5075;
}
.feature-art {
  position: absolute;
  width: 57%;
  height: 100%;
  object-fit: contain;
  right: -3%;
  top: 5%;
  pointer-events: none;
}
.section-heading {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 14px;
  margin-bottom: 20px;
}
.section-heading h2 {
  font-size: 18px;
  font-weight: 600;
  letter-spacing: -0.5px;
}
.section-heading p {
  margin-top: 6px;
  color: var(--text-sub);
  font-size: 10px;
}
.rotation-section {
  margin: 32px 0 36px;
}
.rotation-grid {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 16px;
}
.rotation-card {
  min-width: 0;
}
.rotation-art {
  position: relative;
  display: block;
  width: 100%;
  aspect-ratio: 1;
  padding: 0;
  border: 0;
  border-radius: 12px;
  overflow: hidden;
  background: var(--bg-elevated);
}
.rotation-art img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}
.art-play {
  position: absolute;
  right: 10px;
  bottom: 10px;
  display: grid;
  place-items: center;
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: #d9d0ff;
  color: #25203e;
  opacity: 0;
  transition: opacity 0.15s;
}
.rotation-art:hover .art-play,
.rotation-art:focus-visible .art-play {
  opacity: 1;
}
.playing-label {
  position: absolute;
  inset: auto 0 0;
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px;
  background: #111526d9;
  color: #e1d9ff;
  font-size: 9px;
}
.rotation-meta {
  display: flex;
  align-items: flex-start;
  gap: 3px;
  margin-top: 12px;
}
.rotation-meta > div {
  min-width: 0;
  flex: 1;
}
.rotation-meta h3 {
  font-size: 11px;
  font-weight: 550;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.rotation-meta p {
  margin-top: 5px;
  font-size: 9px;
  color: var(--text-sub);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.heart-button,
.track-action {
  display: grid;
  place-items: center;
  flex: none;
  width: 34px;
  height: 36px;
  border: 0;
  border-radius: 7px;
  background: none;
  color: var(--text-sub);
}
.rotation-meta .heart-button {
  width: 23px;
  height: 25px;
  margin-top: -4px;
}
.heart-button:hover,
.heart-button.liked {
  color: var(--crimson);
}
.track-action:hover {
  background: var(--accent-soft);
  color: var(--gold);
}
.library-toolbar {
  display: flex;
  align-items: center;
  gap: 12px;
  margin: 16px 0 17px;
}
.library-search {
  display: flex;
  align-items: center;
  gap: 10px;
  flex: 1;
  min-width: 0;
  min-height: 42px;
  padding: 10px 13px;
  border: 1px solid var(--hairline);
  border-radius: 10px;
  color: var(--text-faint);
  background: var(--glass);
}
.library-search:focus-within {
  border-color: var(--gold);
}
.library-search input {
  width: 100%;
  min-width: 0;
  border: 0;
  outline: none;
  background: none;
  color: var(--text-main);
  font-size: 11px;
}
.library-search input::placeholder {
  color: var(--text-faint);
}
.library-toolbar select {
  max-width: 145px;
  min-height: 42px;
  border: 1px solid var(--hairline);
  border-radius: 10px;
  padding: 9px;
  background: var(--panel-solid);
  color: var(--text-sub);
  font-size: 10px;
}
.view-toggle {
  display: flex;
  border: 1px solid var(--hairline);
  border-radius: 9px;
  padding: 3px;
  gap: 2px;
}
.view-toggle button {
  display: grid;
  place-items: center;
  width: 33px;
  height: 33px;
  border: 0;
  border-radius: 6px;
  background: none;
  color: var(--text-sub);
}
.view-toggle button.active {
  background: var(--accent-soft);
  color: var(--gold);
}
.track-table-head {
  display: grid;
  grid-template-columns: 30px minmax(0, 1fr) 24% 112px;
  align-items: center;
  gap: 10px;
  padding: 8px 12px 13px;
  color: var(--text-faint);
  font-size: 9px;
  border-bottom: 1px solid var(--hairline-soft);
}
.track-table-head > svg {
  margin-left: 15px;
}
.library-track {
  display: grid;
  grid-template-columns: 30px 42px minmax(0, 1fr) 24% 35px 100px;
  align-items: center;
  gap: 10px;
  min-width: 0;
  padding: 9px 10px;
  border-radius: 10px;
  border-bottom: 1px solid var(--hairline-soft);
}
.library-track:hover {
  background: var(--glass);
}
.library-track.is-current {
  background: var(--accent-soft);
}
.track-number {
  position: relative;
  display: grid;
  place-items: center;
  width: 28px;
  height: 38px;
  border: 0;
  background: none;
  color: var(--text-faint);
  font-size: 10px;
}
.is-current .track-number,
.is-current .track-name {
  color: var(--gold);
}
.number-play {
  display: none;
}
.track-number:hover > span {
  display: none;
}
.track-number:hover .number-play {
  display: block;
}
.track-cover {
  position: relative;
  display: block;
  aspect-ratio: 1;
  overflow: hidden;
  padding: 0;
  border: 0;
  border-radius: 7px;
  background: var(--bg-elevated);
}
.track-cover img {
  display: block;
  width: 100%;
  height: 100%;
  object-fit: cover;
}
.track-cover > span {
  position: absolute;
  inset: 0;
  display: grid;
  place-items: center;
  background: #11152666;
  color: #fff;
  opacity: 0;
}
.track-cover:hover > span,
.track-cover:focus-visible > span {
  opacity: 1;
}
.track-name {
  display: grid;
  gap: 4px;
  min-width: 0;
  padding: 0;
  border: 0;
  background: none;
  color: var(--text-main);
  text-align: left;
}
.track-name strong {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 11px;
  font-weight: 500;
}
.track-name small {
  display: none;
  color: var(--text-sub);
  font-size: 10px;
}
.track-artist-name {
  font-size: 10px;
  color: var(--text-sub);
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
}
.track-duration {
  font-size: 10px;
  color: var(--text-faint);
  font-variant-numeric: tabular-nums;
}
.track-buttons {
  display: flex;
  justify-content: flex-end;
  gap: 0;
}
.load-more {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 9px;
  margin: 20px auto;
  padding: 11px 18px;
  border: 1px solid var(--hairline);
  border-radius: 20px;
  background: none;
  color: var(--text-sub);
  font-size: 11px;
}
.grid-mode {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 16px;
}
.grid-mode .library-track {
  display: flex;
  flex-direction: column;
  align-items: stretch;
  gap: 0;
  padding: 9px;
  border: 1px solid var(--hairline-soft);
  border-radius: 13px;
  background: var(--surface-2);
}
.grid-mode .track-cover {
  border-radius: 9px;
}
.grid-mode .track-number,
.grid-mode .track-artist-name,
.grid-mode .track-duration {
  display: none;
}
.grid-mode .track-name {
  margin-top: 11px;
  gap: 5px;
}
.grid-mode .track-name small {
  display: block;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.grid-mode .track-buttons {
  justify-content: space-between;
  margin-top: 8px;
}
.collection-empty {
  display: grid;
  justify-items: center;
  gap: 14px;
  padding: 54px 16px;
  border: 1px dashed var(--hairline);
  border-radius: 13px;
  text-align: center;
}
.collection-empty > svg {
  color: var(--gold);
}
.collection-empty h3 {
  font-size: 16px;
}
.collection-empty p {
  font-size: 12px;
  color: var(--text-sub);
  max-width: 360px;
  line-height: 1.7;
}
.library-alert {
  display: flex;
  align-items: flex-start;
  gap: 9px;
  padding: 13px;
  border: 1px solid var(--hairline);
  border-radius: 10px;
  margin-bottom: 16px;
  color: var(--text-sub);
  font-size: 11px;
  line-height: 1.7;
}
.library-alert > svg {
  flex: none;
  color: var(--gold);
}
.library-alert > p {
  flex: 1;
}
.library-alert button {
  border: 0;
  background: none;
  color: var(--gold);
  white-space: nowrap;
}
.loading-tracks > div {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 12px;
}
.loading-tracks span {
  width: 42px;
  height: 42px;
  border-radius: 8px;
  background: var(--surface-3);
}
.loading-tracks i {
  width: 35%;
  height: 12px;
  border-radius: 5px;
  background: var(--surface-3);
}
.loading-tracks i:last-child {
  width: 20%;
  margin-left: auto;
}
.recent-section {
  margin-top: 34px;
}
.recent-list {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
}
.recent-list > button {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
  padding: 10px;
  border: 1px solid var(--hairline-soft);
  border-radius: 10px;
  background: var(--surface-2);
  color: var(--text-main);
  text-align: left;
}
.recent-list img {
  width: 42px;
  height: 42px;
  object-fit: cover;
  border-radius: 7px;
}
.recent-list span {
  display: grid;
  gap: 5px;
  flex: 1;
  min-width: 0;
}
.recent-list strong {
  font-size: 11px;
  font-weight: 500;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.recent-list small {
  font-size: 10px;
  color: var(--text-sub);
}
.recent-list svg {
  color: var(--gold);
  flex: none;
}
.collection-footer {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  padding: 35px 0 15px;
  font-size: 10px;
  color: var(--text-faint);
}
.listening-aside {
  padding: 13px 0 0 25px;
  border-left: 1px solid var(--hairline-soft);
  align-self: start;
  position: sticky;
  top: 0;
}
.aside-heading {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 23px;
  color: var(--gold);
}
.aside-heading h2 {
  font-size: 12px;
  font-weight: 550;
  color: var(--text-main);
}
.aside-cover {
  aspect-ratio: 1;
  border-radius: 14px;
  overflow: hidden;
  background: #d9d0ff;
}
.aside-cover img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}
.aside-song {
  margin-top: 18px;
  text-align: center;
}
.aside-song h3 {
  font-size: 14px;
  line-height: 1.5;
  font-weight: 600;
  overflow-wrap: anywhere;
}
.aside-song p {
  font-size: 10px;
  color: var(--text-sub);
  margin-top: 7px;
  line-height: 1.6;
}
.aside-listen {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  min-height: 40px;
  width: 100%;
  margin-top: 20px;
  border: 1px solid var(--hairline);
  border-radius: 9px;
  background: var(--accent-soft);
  color: var(--gold);
  font-size: 11px;
}
.up-next-heading {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin: 31px 0 14px;
}
.up-next-heading h3 {
  font-size: 12px;
  font-weight: 500;
}
.up-next-heading button {
  display: grid;
  place-items: center;
  width: 32px;
  height: 32px;
  border: 0;
  border-radius: 7px;
  background: none;
  color: var(--text-sub);
}
.up-next-list {
  display: grid;
  gap: 13px;
}
.up-next-list > button {
  display: flex;
  align-items: center;
  gap: 9px;
  min-width: 0;
  border: 0;
  background: none;
  color: var(--text-main);
  text-align: left;
}
.up-next-list img {
  width: 36px;
  height: 36px;
  border-radius: 7px;
  object-fit: cover;
}
.up-next-list span {
  display: grid;
  gap: 5px;
  flex: 1;
  min-width: 0;
}
.up-next-list strong {
  font-size: 10px;
  font-weight: 500;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.up-next-list small {
  font-size: 9px;
  color: var(--text-sub);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.up-next-list svg {
  flex: none;
  color: var(--text-faint);
}
.aside-empty {
  color: var(--text-sub);
  font-size: 11px;
  line-height: 1.8;
}
.listening-tip {
  display: grid;
  justify-items: center;
  gap: 12px;
  padding: 28px 8px;
  margin-top: 30px;
  border-top: 1px solid var(--hairline-soft);
  color: var(--text-faint);
  text-align: center;
  font-size: 10px;
  line-height: 1.9;
}
.listening-tip svg {
  color: var(--gold);
}
.playlist-picker-backdrop {
  position: fixed;
  inset: 0;
  z-index: 410;
  display: grid;
  place-items: center;
  padding: 18px;
  background: #080b18b3;
  backdrop-filter: blur(8px);
}
.playlist-picker {
  width: min(420px, 100%);
  max-height: 80dvh;
  overflow: auto;
  padding: 24px;
  border: 1px solid var(--hairline);
  border-radius: 18px;
  background: var(--panel-solid);
}
.playlist-picker header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 10px;
}
.playlist-picker h2 {
  font-size: 18px;
}
.playlist-picker header p {
  margin-top: 8px;
  font-size: 11px;
  color: var(--text-sub);
}
.playlist-picker-list {
  display: grid;
  gap: 8px;
  margin-top: 24px;
}
.playlist-picker-list button {
  display: flex;
  align-items: center;
  gap: 12px;
  min-height: 58px;
  padding: 10px;
  border: 1px solid var(--hairline);
  border-radius: 9px;
  background: var(--surface-2);
  color: var(--text-main);
  text-align: left;
}
.playlist-picker-list span {
  display: grid;
  gap: 5px;
  flex: 1;
}
.playlist-picker-list strong {
  font-size: 12px;
}
.playlist-picker-list small {
  font-size: 10px;
  color: var(--text-sub);
}
.picker-empty {
  display: grid;
  justify-items: center;
  gap: 16px;
  padding: 30px 0 6px;
  color: var(--text-sub);
  font-size: 12px;
}
@media (min-width: 1600px) {
  .music-workspace {
    gap: 40px;
    grid-template-columns: minmax(0, 1fr) 260px;
  }
  .listening-feature {
    min-height: 340px;
  }
  .feature-copy {
    padding: 35px 42px;
  }
  .feature-copy h2 {
    font-size: 52px;
  }
}
@media (max-width: 1250px) {
  .music-workspace {
    grid-template-columns: minmax(0, 1fr);
  }
  .listening-aside {
    display: none;
  }
  .rotation-grid {
    gap: 14px;
  }
}
@media (max-width: 900px) {
  .rotation-grid {
    gap: 10px;
  }
  .rotation-meta .heart-button {
    display: none;
  }
  .library-track {
    grid-template-columns: 24px 42px minmax(0, 1fr) 32px 100px;
    gap: 8px;
  }
  .track-artist-name {
    display: none;
  }
  .track-name small {
    display: block;
  }
  .track-table-head {
    grid-template-columns: 24px minmax(0, 1fr) 32px 100px;
  }
  .track-table-head > span:nth-child(3) {
    display: none;
  }
  .track-table-head > svg {
    margin-left: 0;
  }
  .feature-copy {
    width: 67%;
    padding: 28px;
  }
  .feature-art {
    width: 55%;
    right: -9%;
  }
}
@media (max-width: 760px) {
  .welcome-heading {
    margin-top: 5px;
    margin-bottom: 20px;
  }
  .welcome-heading h1 {
    font-size: 23px;
  }
  .welcome-heading p {
    font-size: 11px;
  }
  .welcome-heading .quiet-button {
    width: 42px;
    height: 42px;
    padding: 0;
  }
  .welcome-heading .quiet-button span {
    display: none;
  }
  .listening-feature {
    min-height: 280px;
    border-radius: 17px;
  }
  .feature-copy {
    width: 87%;
    padding: 25px 22px;
  }
  .feature-copy h2 {
    font-size: 32px;
  }
  .feature-copy p {
    font-size: 10px;
  }
  .feature-tag {
    font-size: 9px;
  }
  .feature-art {
    width: 58%;
    height: 75%;
    top: 27%;
    right: -17%;
    opacity: 0.85;
  }
  .feature-note {
    font-size: 9px;
  }
  .feature-play {
    font-size: 10px;
    padding: 10px 14px;
  }
  .rotation-section {
    margin: 28px 0;
  }
  .section-heading h2 {
    font-size: 17px;
  }
  .section-heading p {
    font-size: 10px;
  }
  .text-button {
    font-size: 10px;
  }
  .rotation-grid {
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 13px;
  }
  .rotation-card:nth-child(n + 4) {
    display: none;
  }
  .rotation-meta h3 {
    font-size: 10px;
  }
  .rotation-meta p {
    font-size: 9px;
  }
  .art-play {
    opacity: 1;
    width: 31px;
    height: 31px;
    right: 7px;
    bottom: 7px;
  }
  .library-toolbar {
    gap: 8px;
    flex-wrap: wrap;
  }
  .library-search {
    flex-basis: 100%;
  }
  .library-search input {
    font-size: 16px;
  }
  .library-toolbar select {
    flex: 1;
    max-width: none;
    font-size: 11px;
  }
  .library-track {
    grid-template-columns: 40px minmax(0, 1fr) 101px;
    gap: 10px;
    padding: 9px 4px;
  }
  .track-number,
  .track-duration,
  .track-table-head {
    display: none;
  }
  .track-name strong {
    font-size: 11px;
  }
  .track-name small {
    font-size: 10px;
  }
  .track-buttons button {
    width: 33px;
    height: 44px;
  }
  .track-cover {
    width: 40px;
  }
  .grid-mode {
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 10px;
  }
  .grid-mode .track-cover {
    width: 100%;
  }
  .grid-mode .track-buttons {
    margin-top: 5px;
  }
  .collection-footer {
    font-size: 9px;
  }
  .recent-list {
    grid-template-columns: 1fr;
  }
  .library-alert {
    flex-wrap: wrap;
  }
  .library-alert p {
    flex-basis: calc(100% - 35px);
  }
  .library-alert button {
    margin-left: 28px;
  }
  .playlist-picker {
    padding: 20px;
  }
  .section-heading .text-button {
    gap: 5px;
  }
  .listening-aside {
    display: none;
  }
}
@media (max-width: 370px) {
  .feature-copy h2 {
    font-size: 29px;
  }
  .feature-copy {
    padding: 23px 18px;
  }
  .feature-tag {
    font-size: 8px;
  }
  .library-track {
    grid-template-columns: 36px minmax(0, 1fr) 90px;
    gap: 8px;
  }
  .track-buttons button {
    width: 30px;
  }
  .track-cover {
    width: 36px;
  }
  .rotation-grid {
    gap: 9px;
  }
}
@media (hover: hover) {
  .library-track:focus-within .track-cover > span {
    opacity: 1;
  }
}
@media (prefers-reduced-motion: reduce) {
  .art-play {
    transition: none;
  }
}
</style>
