<template>
  <Teleport to="body"
    ><Transition name="player-reveal"
      ><section
        v-if="visible"
        ref="dialogRef"
        class="np-overlay"
        role="dialog"
        aria-modal="true"
        aria-labelledby="now-playing-title"
        tabindex="-1"
      >
        <header class="np-topbar">
          <div class="np-brand"><BrandMark /><span>Không gian nghe nhạc</span></div>
          <button class="np-close" aria-label="Thu nhỏ trình phát" @click="emit('close')">
            <ChevronDown :size="23" />
          </button>
        </header>
        <div class="np-body" :class="{ 'lyrics-open': showLyrics }">
          <div class="np-player">
            <div class="np-art">
              <img
                v-if="currentSong"
                :src="songArtwork(currentSong)"
                :alt="`Bìa ${currentSong.title}`"
                @error="handleImageError"
              />
            </div>
            <div class="np-meta">
              <div>
                <h1 id="now-playing-title">{{ currentSong?.title || 'Chọn một bài hát' }}</h1>
                <p>{{ currentSong?.artist || 'Âm nhạc đang chờ bạn' }}</p>
              </div>
              <button
                v-if="currentSong"
                class="np-icon"
                :class="{ active: isLiked(currentSong.id) }"
                :aria-pressed="isLiked(currentSong.id)"
                aria-label="Yêu thích bài đang phát"
                @click="toggleLike(currentSong)"
              >
                <Heart :size="22" :fill="isLiked(currentSong.id) ? 'currentColor' : 'none'" />
              </button>
            </div>
            <p v-if="error" class="np-error" role="alert">{{ error }}</p>
            <div class="np-progress">
              <input
                type="range"
                min="0"
                :max="duration || 0"
                step="0.1"
                :value="currentTime"
                :disabled="!duration"
                :style="{ '--fill': progressPct + '%' }"
                aria-label="Tua bài hát trong trình phát"
                @input="emit('seek', Number($event.target.value))"
              />
              <div>
                <span>{{ formatTime(currentTime) }}</span><span>{{ formatTime(duration) }}</span>
              </div>
            </div>
            <div class="np-controls">
              <button
                class="np-icon"
                :class="{ active: isShuffle }"
                :aria-pressed="isShuffle"
                aria-label="Phát ngẫu nhiên trong trình phát"
                @click="emit('toggle-shuffle')"
              >
                <Shuffle :size="21" /></button
              ><button
                class="np-icon"
                aria-label="Bài trước trong trình phát"
                @click="emit('prev')"
              >
                <SkipBack :size="24" fill="currentColor" /></button
              ><button
                class="np-play"
                :aria-label="isPlaying ? 'Tạm dừng trong trình phát' : 'Phát trong trình phát'"
                @click="emit('toggle-play')"
              >
                <component :is="isPlaying ? Pause : Play" :size="25" fill="currentColor" /></button
              ><button class="np-icon" aria-label="Bài tiếp trong trình phát" @click="emit('next')">
                <SkipForward :size="24" fill="currentColor" /></button
              ><button
                class="np-icon"
                :class="{ active: repeatMode !== 'off' }"
                :aria-label="`Chế độ lặp ${repeatMode}`"
                @click="emit('toggle-repeat')"
              >
                <component :is="repeatMode === 'one' ? Repeat1 : Repeat2" :size="21" />
              </button>
            </div>
            <button
              class="np-lyrics-toggle"
              :class="{ active: showLyrics }"
              :aria-pressed="showLyrics"
              @click="showLyrics = !showLyrics"
            >
              <Mic2 :size="17" />{{ showLyrics ? 'Ẩn lời bài hát' : 'Hiện lời bài hát' }}
            </button>
          </div>
          <section v-if="showLyrics" class="np-lyrics" aria-labelledby="lyrics-heading">
            <header>
              <h2 id="lyrics-heading">Lời bài hát</h2>
              <span>{{
                lyricsLoading ? 'Đang đọc lời...' : isSynced ? 'Đồng bộ theo nhạc' : 'Lời bài hát'
              }}</span>
            </header>
            <div v-if="lyricsLoading" class="lyrics-empty">
              <LoaderCircle :size="28" />
              <p>Đang đọc lời bài hát...</p>
            </div>
            <div v-else-if="lyricsMissing" class="lyrics-empty">
              <Mic2 :size="32" />
              <h3>Một giai điệu chờ lời.</h3>
              <p>Bài hát này chưa có lời. Bạn có thể thêm lời để lần nghe sau trọn vẹn hơn.</p>
              <button @click="openLyricsManager">Thêm lời bài hát <Plus :size="16" /></button>
            </div>
            <div v-else-if="isSynced" class="lyrics-lines">
              <button
                v-for="(line, index) in lines"
                :key="`${line.time}-${index}`"
                :ref="
                  (element) => {
                    if (element) lyricRefs[index] = element;
                  }
                "
                :class="{ active: index === currentLyricIndex, passed: index < currentLyricIndex }"
                :aria-current="index === currentLyricIndex ? 'true' : undefined"
                :aria-label="`Tua đến ${formatTime(line.time)}: ${line.text}`"
                @click="emit('seek', line.time)"
              >
                {{ line.text || '♪' }}
              </button>
            </div>
            <div v-else class="lyrics-plain">{{ lyricsContent }}</div>
          </section>
        </div>
        <footer class="np-footer">
          <Headphones :size="16" /> Một chút nhạc, một khoảng riêng.
        </footer>
      </section></Transition
    ></Teleport
  >
</template>
<script setup>
import { computed, nextTick, ref, toRef, watch } from 'vue';
import {
  ChevronDown,
  Headphones,
  Heart,
  LoaderCircle,
  Mic2,
  Pause,
  Play,
  Plus,
  Repeat1,
  Repeat2,
  Shuffle,
  SkipBack,
  SkipForward,
} from '@lucide/vue';
import BrandMark from './BrandMark.vue';
import { songArtwork } from '../utils/artwork';
import { useLyrics } from '../composables/useLyrics';
import { useLibrary } from '../composables/useLibrary';
import { useDialogFocus } from '../composables/useDialogFocus';
const props = defineProps({
  visible: Boolean,
  currentSong: Object,
  isPlaying: Boolean,
  isShuffle: Boolean,
  repeatMode: String,
  currentTime: Number,
  duration: Number,
  error: String,
});
const emit = defineEmits([
  'close',
  'toggle-play',
  'next',
  'prev',
  'toggle-shuffle',
  'toggle-repeat',
  'seek',
  'manage-lyrics',
]);
const showLyrics = ref(window.innerWidth > 760),
  dialogRef = ref(null),
  lyricRefs = ref([]);
const { isLiked, toggleLike } = useLibrary();
useDialogFocus(toRef(props, 'visible'), dialogRef, () => emit('close'));
const {
  content: lyricsContent,
  isMissing: lyricsMissing,
  isLoading: lyricsLoading,
  lines,
  isSynced,
} = useLyrics(
  computed(() => props.currentSong),
  { allowProvider: false },
);
const progressPct = computed(() =>
  props.duration ? (props.currentTime / props.duration) * 100 : 0,
);
const currentLyricIndex = computed(() => {
  let index = -1;
  lines.value.forEach((line, i) => {
    if (line.time <= props.currentTime) index = i;
  });
  return index;
});
watch(currentLyricIndex, async (index) => {
  if (!props.visible || !showLyrics.value || index < 0) return;
  await nextTick();
  lyricRefs.value[index]?.scrollIntoView({
    behavior: window.matchMedia('(prefers-reduced-motion: reduce)').matches ? 'instant' : 'smooth',
    block: 'center',
  });
});
watch(
  () => props.currentSong?.id,
  () => {
    lyricRefs.value = [];
  },
);
const openLyricsManager = () => {
  emit('close');
  emit('manage-lyrics');
};
const handleImageError = (event) => {
  const image = event.currentTarget;
  if (image.dataset.fallbackApplied) return;
  image.dataset.fallbackApplied = 'true';
  image.src = songArtwork({ ...props.currentSong, cover: '' });
};
const formatTime = (time) =>
  Number.isFinite(time) && time > 0
    ? `${Math.floor(time / 60)}:${String(Math.floor(time % 60)).padStart(2, '0')}`
    : '0:00';
</script>
<style scoped>
.np-overlay {
  position: fixed;
  inset: 0;
  z-index: 300;
  display: flex;
  flex-direction: column;
  background: var(--bg-deep);
  color: var(--text-main);
  overflow: auto;
  outline: none;
}
.np-topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 25px clamp(22px, 5vw, 75px);
}
.np-brand {
  display: flex;
  align-items: center;
  gap: 12px;
  color: var(--gold);
  font-size: 12px;
}
.np-brand svg {
  width: 33px;
  height: 33px;
}
.np-brand span {
  color: var(--text-sub);
}
.np-close {
  display: grid;
  place-items: center;
  width: 43px;
  height: 43px;
  border: 1px solid var(--hairline);
  border-radius: 50%;
  background: var(--glass);
  color: var(--text-main);
}
.np-body {
  display: grid;
  grid-template-columns: minmax(0, 410px);
  justify-content: center;
  align-items: center;
  gap: clamp(40px, 8vw, 130px);
  width: min(1100px, calc(100% - 64px));
  margin: auto;
  padding: 25px 0;
}
.np-body.lyrics-open {
  grid-template-columns: minmax(0, 410px) minmax(0, 1fr);
}
.np-player {
  min-width: 0;
}
.np-art {
  aspect-ratio: 1;
  overflow: hidden;
  border-radius: 18px;
  background: var(--panel-solid);
  box-shadow: var(--shadow-deep);
}
.np-art img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}
.np-meta {
  display: flex;
  align-items: center;
  gap: 20px;
  margin-top: 25px;
}
.np-meta > div {
  min-width: 0;
  flex: 1;
}
.np-meta h1 {
  font-size: 25px;
  line-height: 1.45;
  letter-spacing: -0.7px;
  overflow-wrap: anywhere;
}
.np-meta p {
  margin-top: 9px;
  font-size: 13px;
  color: var(--text-sub);
}
.np-icon {
  display: grid;
  place-items: center;
  flex: none;
  width: 42px;
  height: 44px;
  border: 0;
  border-radius: 10px;
  background: none;
  color: var(--text-sub);
}
.np-icon:hover,
.np-icon.active {
  color: var(--gold);
  background: var(--accent-soft);
}
.np-progress {
  margin-top: 27px;
}
.np-progress input {
  width: 100%;
  height: 4px;
  appearance: none;
  background: linear-gradient(
    to right,
    var(--gold) var(--fill, 0%),
    var(--hairline) var(--fill, 0%)
  );
  border-radius: 9px;
}
.np-progress input::-webkit-slider-thumb {
  appearance: none;
  width: 12px;
  height: 12px;
  background: var(--gold);
  border-radius: 50%;
}
.np-progress > div {
  display: flex;
  justify-content: space-between;
  margin-top: 12px;
  color: var(--text-faint);
  font-size: 11px;
  font-variant-numeric: tabular-nums;
}
.np-controls {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  margin-top: 20px;
}
.np-play {
  display: grid;
  place-items: center;
  flex: none;
  width: 62px;
  height: 62px;
  border: 0;
  border-radius: 50%;
  background: #d9d0ff;
  color: #25203e;
}
.np-lyrics-toggle {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 9px;
  min-height: 41px;
  margin: 23px auto 0;
  padding: 10px 15px;
  border: 1px solid var(--hairline);
  border-radius: 20px;
  background: var(--glass);
  color: var(--text-sub);
  font-size: 11px;
}
.np-lyrics-toggle.active {
  color: var(--gold);
  border-color: var(--gold);
}
.np-lyrics {
  display: flex;
  flex-direction: column;
  min-height: 400px;
  max-height: 650px;
  align-self: stretch;
  min-width: 0;
  padding-top: 15px;
}
.np-lyrics > header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 15px;
  padding: 0 0 25px;
  border-bottom: 1px solid var(--hairline);
}
.np-lyrics h2 {
  font-size: 17px;
  font-weight: 500;
}
.np-lyrics > header > span {
  color: var(--text-faint);
  font-size: 10px;
}
.lyrics-empty {
  display: grid;
  align-content: center;
  justify-items: start;
  gap: 18px;
  flex: 1;
  padding: 35px 0;
  color: var(--gold);
}
.lyrics-empty h3 {
  font-size: 22px;
  color: var(--text-main);
  font-weight: 500;
}
.lyrics-empty p {
  max-width: 300px;
  font-size: 12px;
  color: var(--text-sub);
  line-height: 1.9;
}
.lyrics-empty button {
  display: flex;
  align-items: center;
  gap: 9px;
  padding: 12px 15px;
  border: 1px solid var(--hairline);
  border-radius: 10px;
  background: var(--accent-soft);
  color: var(--gold);
  font-size: 11px;
}
.lyrics-lines {
  display: flex;
  flex-direction: column;
  gap: 22px;
  overflow: auto;
  padding: 30px 5px 50px;
}
.lyrics-lines button {
  padding: 4px 0;
  border: 0;
  background: none;
  color: var(--text-faint);
  text-align: left;
  font-size: clamp(21px, 2.4vw, 32px);
  line-height: 1.6;
  font-weight: 600;
  transition: color 0.2s;
}
.lyrics-lines button.active {
  color: var(--gold);
}
.lyrics-lines button.passed {
  color: var(--text-sub);
}
.lyrics-lines button:hover {
  color: var(--text-main);
}
.lyrics-plain {
  overflow: auto;
  padding: 26px 0;
  font-size: 18px;
  line-height: 2;
  white-space: pre-wrap;
  color: var(--text-sub);
}
.np-footer {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 9px;
  min-height: 60px;
  padding: 20px;
  color: var(--text-faint);
  font-size: 10px;
}
.np-error {
  margin-top: 16px;
  color: var(--crimson);
  font-size: 11px;
  line-height: 1.8;
}
.player-reveal-enter-active,
.player-reveal-leave-active {
  transition: opacity 0.15s ease;
}
.player-reveal-enter-from,
.player-reveal-leave-to {
  opacity: 0;
}
@media (max-width: 760px) {
  .np-topbar {
    padding: 17px 20px;
  }
  .np-brand {
    font-size: 11px;
  }
  .np-body,
  .np-body.lyrics-open {
    display: flex;
    flex-direction: column;
    align-items: stretch;
    gap: 28px;
    width: min(400px, calc(100% - 44px));
    padding: 18px 0;
  }
  .np-art {
    max-height: 38dvh;
    max-width: 38dvh;
    margin: auto;
    width: 100%;
    border-radius: 14px;
  }
  .np-meta h1 {
    font-size: 22px;
  }
  .np-meta {
    margin-top: 22px;
  }
  .np-meta p {
    font-size: 12px;
  }
  .np-progress {
    margin-top: 20px;
  }
  .np-controls {
    margin-top: 15px;
  }
  .np-play {
    width: 56px;
    height: 56px;
  }
  .np-lyrics {
    min-height: 280px;
    max-height: 420px;
  }
  .np-lyrics > header {
    padding-bottom: 18px;
  }
  .lyrics-lines button {
    font-size: 23px;
  }
  .np-footer {
    font-size: 9px;
    padding: 12px;
  }
  .lyrics-open .np-art {
    display: none;
  }
  .np-lyrics-toggle {
    margin-top: 18px;
  }
}
@media (prefers-reduced-motion: reduce) {
  .player-reveal-enter-active,
  .player-reveal-leave-active {
    transition: none;
  }
}
</style>
