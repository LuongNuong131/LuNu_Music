<template>
  <footer
    class="player-bar"
    :class="{ 'has-error': state.error, 'is-playing': state.isPlaying }"
    aria-label="Trình phát nhạc"
  >
    <button
      v-if="state.currentSong"
      class="now-track"
      @click="state.nowPlayingVisible = true"
      aria-label="Mở trình phát toàn màn hình"
    >
      <img
        class="mini-art"
        :src="songArtwork(state.currentSong)"
        :alt="state.currentSong.title"
        @error="handleImageError"
      /><span class="track-details"
        ><strong>{{ state.currentSong.title }}</strong
        ><small>{{ state.currentSong.artist }}</small></span
      ><Maximize2 class="expand-hint" :size="16" />
    </button>
    <div v-else class="now-track empty">
      <span class="mini-art placeholder"><Headphones :size="25" /></span
      ><span class="track-details"
        ><strong>Âm nhạc đang chờ bạn</strong><small>Chọn một bài để bắt đầu</small></span
      >
    </div>
    <button
      v-if="state.currentSong"
      class="player-like"
      :class="{ liked: isLiked(state.currentSong.id) }"
      :aria-pressed="isLiked(state.currentSong.id)"
      aria-label="Yêu thích bài đang phát"
      @click="toggleLike(state.currentSong)"
    >
      <Heart :size="18" :fill="isLiked(state.currentSong.id) ? 'currentColor' : 'none'" />
    </button>
    <div class="player-controls">
      <div class="control-row">
        <button
          class="icon-control optional"
          :class="{ active: state.shuffle }"
          :aria-pressed="state.shuffle"
          @click="toggleShuffle"
          aria-label="Phát ngẫu nhiên"
        >
          <Shuffle :size="17" /></button
        ><button
          class="icon-control previous-control"
          @click="previous"
          :disabled="!state.currentSong"
          aria-label="Bài trước"
        >
          <SkipBack :size="19" fill="currentColor" /></button
        ><button
          class="play-btn"
          @click="togglePlay"
          :disabled="!state.currentSong"
          :aria-label="state.isPlaying ? 'Tạm dừng' : 'Phát nhạc'"
        >
          <LoaderCircle
            v-if="state.isLoading || state.isBuffering"
            class="loading-icon"
            :size="21"
          /><Pause v-else-if="state.isPlaying" :size="20" fill="currentColor" /><Play
            v-else
            :size="20"
            fill="currentColor"
          /></button
        ><button
          class="icon-control"
          @click="next"
          :disabled="!state.currentSong"
          aria-label="Bài tiếp"
        >
          <SkipForward :size="19" fill="currentColor" /></button
        ><button
          class="icon-control optional"
          :class="{ active: state.repeatMode !== 'off' }"
          :aria-label="`Lặp: ${state.repeatMode === 'one' ? 'một bài' : state.repeatMode === 'all' ? 'tất cả' : 'tắt'}`"
          @click="toggleRepeat"
        >
          <component :is="state.repeatMode === 'one' ? Repeat1 : Repeat2" :size="17" />
        </button>
      </div>
      <div class="progress-container">
        <span>{{ formatTime(state.currentTime) }}</span><input
          class="progress-bar"
          type="range"
          min="0"
          :max="state.duration || 0"
          step="0.1"
          :value="state.currentTime"
          :disabled="!state.duration"
          :style="progressStyle"
          aria-label="Tiến trình bài hát"
          :aria-valuetext="`${formatTime(state.currentTime)} trên ${formatTime(state.duration)}`"
          @input="seek(Number($event.target.value))"
        /><span>{{ formatTime(state.duration) }}</span>
      </div>
    </div>
    <div class="player-actions">
      <button
        class="icon-control queue-toggle"
        :class="{ active: state.queueVisible }"
        @click="state.queueVisible = !state.queueVisible"
        aria-label="Mở hàng đợi"
      >
        <ListMusic :size="19" /></button
      ><span class="action-divider"></span
      ><button
        class="icon-control volume-icon"
        @click="toggleMute"
        :aria-label="state.muted ? 'Bật tiếng' : 'Tắt tiếng'"
      >
        <component :is="state.muted || state.volume === 0 ? VolumeX : Volume2" :size="19" /></button
      ><input
        type="range"
        class="volume-bar"
        min="0"
        max="1"
        step="0.01"
        :value="state.muted ? 0 : state.volume"
        @input="setVolume(Number($event.target.value))"
        :style="volumeStyle"
        aria-label="Âm lượng"
      /><button
        class="icon-control full-player"
        :disabled="!state.currentSong"
        @click="state.nowPlayingVisible = true"
        aria-label="Mở lời bài hát"
      >
        <Mic2 :size="18" />
      </button>
    </div>
    <p v-if="state.error" class="player-error" role="alert">{{ state.error }}</p>
    <audio
      v-if="state.currentSong?.url"
      ref="audioRef"
      :src="state.currentSong.url"
      preload="metadata"
      @timeupdate="onTimeUpdate"
      @loadedmetadata="onLoadedMetadata"
      @waiting="handleAudioWaiting"
      @canplay="handleAudioCanPlay"
      @error="handleAudioError"
      @ended="handleAudioEnded"
    ></audio>
  </footer>
</template>
<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue';
import {
  Heart,
  Headphones,
  ListMusic,
  LoaderCircle,
  Maximize2,
  Mic2,
  Pause,
  Play,
  Repeat1,
  Repeat2,
  Shuffle,
  SkipBack,
  SkipForward,
  Volume2,
  VolumeX,
} from '@lucide/vue';
import {
  usePlayer,
  setAudioElement,
  handleAudioLoaded,
  handleAudioTimeUpdate,
  handleAudioWaiting,
  handleAudioCanPlay,
  handleAudioError,
  handleAudioEnded,
} from '../store/playerState';
import { useLibrary } from '../composables/useLibrary';
import { songArtwork } from '../utils/artwork';
const {
  state,
  togglePlay,
  seek,
  setVolume,
  toggleMute,
  toggleShuffle,
  toggleRepeat,
  next,
  previous,
} = usePlayer();
const { isLiked, toggleLike } = useLibrary();
const audioRef = ref(null);
const fallbackCover = '/images/ChoCiu.jpg';
const handleImageError = (event) => {
  const image = event.currentTarget;
  if (image.dataset.fallbackApplied) return;
  image.dataset.fallbackApplied = 'true';
  image.src = fallbackCover;
};
onMounted(() => setAudioElement(audioRef.value));
onBeforeUnmount(() => setAudioElement(null));
watch(
  () => state.currentSong?.url,
  async () => {
    await nextTick();
    setAudioElement(audioRef.value);
    audioRef.value?.load();
  },
);
const onTimeUpdate = () => handleAudioTimeUpdate(audioRef.value?.currentTime || 0);
const onLoadedMetadata = () => handleAudioLoaded(audioRef.value?.duration || 0);
const progressStyle = computed(() => ({
  '--fill': `${state.duration ? (state.currentTime / state.duration) * 100 : 0}%`,
}));
const volumeStyle = computed(() => ({ '--fill': `${(state.muted ? 0 : state.volume) * 100}%` }));
const formatTime = (time) => {
  if (!Number.isFinite(time) || time < 0) return '0:00';
  return `${Math.floor(time / 60)}:${String(Math.floor(time % 60)).padStart(2, '0')}`;
};
</script>
<style scoped>
.player-bar {
  position: relative;
  display: flex;
  align-items: center;
  gap: 14px;
  min-height: 93px;
  padding: 13px 27px;
  border-top: 1px solid var(--hairline);
  background: var(--panel-solid);
  z-index: 140;
}
.now-track {
  display: flex;
  align-items: center;
  gap: 12px;
  min-width: 0;
  width: 25%;
  padding: 0;
  border: 0;
  background: none;
  color: var(--text-main);
  text-align: left;
}
.mini-art {
  display: block;
  flex: none;
  width: 53px;
  height: 53px;
  border-radius: 9px;
  object-fit: cover;
}
.placeholder {
  display: grid;
  place-items: center;
  background: var(--accent-soft);
  color: var(--gold);
}
.track-details {
  display: grid;
  gap: 7px;
  min-width: 0;
  flex: 1;
}
.track-details strong {
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
  font-size: 12px;
  font-weight: 550;
}
.track-details small {
  font-size: 10px;
  color: var(--text-sub);
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
}
.expand-hint {
  color: var(--text-faint);
  flex: none;
}
.player-like {
  display: grid;
  place-items: center;
  width: 36px;
  height: 40px;
  flex: none;
  border: 0;
  background: none;
  color: var(--text-sub);
}
.player-like.liked {
  color: var(--crimson);
}
.player-controls {
  display: grid;
  justify-items: center;
  gap: 7px;
  flex: 1;
  min-width: 180px;
  max-width: 530px;
  margin: auto;
}
.control-row {
  display: flex;
  align-items: center;
  gap: 18px;
}
.icon-control {
  display: grid;
  place-items: center;
  width: 32px;
  height: 32px;
  border: 0;
  border-radius: 8px;
  background: none;
  color: var(--text-sub);
}
.icon-control:hover,
.icon-control.active {
  background: var(--accent-soft);
  color: var(--gold);
}
.play-btn {
  display: grid;
  place-items: center;
  width: 37px;
  height: 37px;
  padding: 0;
  border: 0;
  border-radius: 50%;
  background: #d9d0ff;
  color: #25203e;
}
.play-btn:hover:not(:disabled) {
  background: #c9baff;
}
.progress-container {
  display: flex;
  align-items: center;
  gap: 10px;
  width: 100%;
}
.progress-container > span {
  font-size: 9px;
  color: var(--text-faint);
  font-variant-numeric: tabular-nums;
  min-width: 28px;
  text-align: center;
}
.progress-bar,
.volume-bar {
  appearance: none;
  min-width: 0;
  height: 4px;
  border-radius: 20px;
  outline: none;
  background: linear-gradient(
    to right,
    var(--gold) var(--fill, 0%),
    var(--hairline) var(--fill, 0%)
  );
  cursor: pointer;
}
.progress-bar {
  width: 100%;
  flex: 1;
}
.progress-bar::-webkit-slider-thumb,
.volume-bar::-webkit-slider-thumb {
  appearance: none;
  width: 10px;
  height: 10px;
  border: 0;
  border-radius: 50%;
  background: var(--gold);
  opacity: 0;
}
.progress-bar:hover::-webkit-slider-thumb,
.progress-bar:focus-visible::-webkit-slider-thumb,
.volume-bar:hover::-webkit-slider-thumb,
.volume-bar:focus-visible::-webkit-slider-thumb {
  opacity: 1;
}
.player-actions {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 8px;
  width: 25%;
}
.volume-bar {
  width: 75px;
}
.action-divider {
  height: 18px;
  border-left: 1px solid var(--hairline);
  margin: 0 4px;
}
.player-error {
  position: absolute;
  inset: auto 0 100%;
  padding: 9px 16px;
  background: var(--panel-solid);
  border-top: 1px solid var(--crimson);
  color: var(--crimson);
  font-size: 11px;
  text-align: center;
  line-height: 1.6;
}
.loading-icon {
  animation: spin 1s linear infinite;
}
audio {
  display: none;
}
@media (max-width: 1000px) {
  .player-bar {
    padding-inline: 18px;
  }
  .player-like,
  .expand-hint,
  .full-player,
  .action-divider {
    display: none;
  }
  .player-actions {
    width: 21%;
  }
  .control-row {
    gap: 11px;
  }
}
@media (max-width: 760px) {
  .player-bar {
    min-height: 72px;
    gap: 10px;
    padding: 10px 12px;
    border: 1px solid var(--hairline);
    border-radius: 14px;
    box-shadow: 0 8px 30px #080b1830;
  }
  .now-track {
    width: auto;
    flex: 1;
    gap: 10px;
  }
  .mini-art {
    width: 45px;
    height: 45px;
  }
  .track-details {
    gap: 5px;
  }
  .track-details strong {
    font-size: 11px;
  }
  .track-details small {
    font-size: 9px;
  }
  .optional,
  .previous-control,
  .volume-icon,
  .volume-bar,
  .progress-container {
    display: none;
  }
  .player-controls {
    flex: none;
    min-width: 0;
    gap: 0;
    margin: 0;
  }
  .control-row {
    gap: 5px;
  }
  .play-btn {
    width: 39px;
    height: 39px;
  }
  .icon-control {
    width: 35px;
    height: 40px;
  }
  .player-actions {
    width: auto;
    flex: none;
    gap: 0;
  }
  .player-error {
    border: 1px solid var(--crimson);
    border-radius: 10px 10px 0 0;
    font-size: 10px;
  }
}
@media (prefers-reduced-motion: reduce) {
  .loading-icon {
    animation: none;
  }
}
</style>
