<!-- src/components/PlayerBar.vue -->
<template>
  <div class="player-bar">
    <div
      class="song-info"
      v-if="currentSong"
      @click="npVisible = true"
      role="button"
      tabindex="0"
      title="Mở màn hình Đang phát"
      @keyup.enter="npVisible = true"
    >
      <div class="cover-wrap" :class="{ spinning: isPlaying }">
        <img :src="currentSong.cover" class="cover-img" />
      </div>
      <div class="details">
        <div class="title">{{ currentSong.title }}</div>
        <div class="artist">{{ currentSong.artist }}</div>
      </div>
      <span class="expand-hint">⌃</span>
    </div>
    <div class="song-info empty" v-else>
      <div class="cover-wrap placeholder"></div>
      <div class="details">
        <div class="title muted">Chưa phát bài nào</div>
        <div class="artist muted">Chọn một track để bắt đầu</div>
      </div>
    </div>

    <div class="player-controls">
      <div class="buttons">
        <button
          class="shuffle-btn"
          :class="{ active: isShuffle }"
          @click="emit('toggle-shuffle')"
          :title="isShuffle ? 'Shuffle: đang bật' : 'Shuffle: đang tắt'"
          :aria-pressed="isShuffle"
        >
          <svg class="shuffle-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
            <polyline points="16 3 21 3 21 8"></polyline>
            <line x1="4" y1="20" x2="21" y2="3"></line>
            <polyline points="21 16 21 21 16 21"></polyline>
            <line x1="15" y1="15" x2="21" y2="21"></line>
            <line x1="4" y1="4" x2="9" y2="9"></line>
          </svg>
        </button>
        <button class="control-btn" @click="emit('prev')" :disabled="!currentSong" title="Previous (←)" aria-label="Bài trước">⏮</button>
        <button class="play-btn" @click="togglePlay" :disabled="!currentSong" title="Play/Pause (Space)" aria-label="Phát/Tạm dừng">
          <span v-if="isPlaying">⏸</span>
          <span v-else class="play-icon">▶</span>
        </button>
        <button class="control-btn" @click="emit('next')" :disabled="!currentSong" title="Next (→)" aria-label="Bài tiếp theo">⏭</button>
        <button
          class="repeat-btn"
          :class="{ active: repeatMode !== 'off' }"
          @click="emit('toggle-repeat')"
          :title="repeatTitle"
          :aria-pressed="repeatMode !== 'off'"
        >
          <svg v-if="repeatMode !== 'one'" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
            <polyline points="17 1 21 5 17 9"></polyline>
            <path d="M3 11V9a4 4 0 0 1 4-4h14"></path>
            <polyline points="7 23 3 19 7 15"></polyline>
            <path d="M21 13v2a4 4 0 0 1-4 4H3"></path>
          </svg>
          <span v-else class="repeat-one">1</span>
        </button>
      </div>

      <div class="progress-container">
        <span class="time">{{ formatTime(currentTime) }}</span>
        <input
          type="range"
          class="progress-bar"
          min="0"
          :max="duration || 0"
          v-model="currentTime"
          @input="seek"
          :disabled="!currentSong"
          :style="progressStyle"
        />
        <span class="time">{{ formatTime(duration) }}</span>
      </div>
    </div>

    <div class="volume-control">
      <button class="queue-toggle" @click="emit('toggle-queue')" title="Hàng đợi phát" aria-label="Hàng đợi phát">▤</button>
      <button class="vol-icon" @click="toggleMute" :title="volume > 0 ? 'Tắt tiếng (M)' : 'Bật tiếng (M)'" aria-label="Tắt/Bật tiếng">
        {{ volume > 0 ? (volume > 0.5 ? '🔊' : '🔉') : '🔈' }}
      </button>
      <input
        type="range"
        class="volume-bar"
        min="0"
        max="1"
        step="0.01"
        v-model="volume"
        @input="updateVolume"
        :style="volumeStyle"
      />
    </div>

    <audio
      ref="audioRef"
      :src="currentSong?.url"
      @timeupdate="onTimeUpdate"
      @loadedmetadata="onLoadedMetadata"
      @ended="onEnded"
      @error="onAudioError"
    ></audio>

    <!-- Màn hình Đang phát toàn màn hình — điểm nhấn giao diện -->
    <NowPlayingView
      :visible="npVisible"
      :current-song="currentSong"
      :is-playing="isPlaying"
      :is-shuffle="isShuffle"
      :repeat-mode="repeatMode"
      :current-time="currentTime"
      :duration="duration"
      :visualizer-data="visualizerData"
      @close="npVisible = false"
      @toggle-play="togglePlay"
      @next="emit('next')"
      @prev="emit('prev')"
      @toggle-shuffle="emit('toggle-shuffle')"
      @toggle-repeat="emit('toggle-repeat')"
      @seek="seekTo"
    />
  </div>
</template>

<script setup>
import { ref, watch, computed, onMounted, onUnmounted, nextTick } from 'vue';
import NowPlayingView from './NowPlayingView.vue';
import { useToast } from '../composables/useToast.js';

const props = defineProps({
  currentSong: Object,
  isShuffle: Boolean,
  repeatMode: { type: String, default: 'off' } // 'off' | 'all' | 'one'
});

const emit = defineEmits(['next', 'prev', 'toggle-shuffle', 'toggle-repeat', 'update:is-playing', 'toggle-queue']);
const { showToast } = useToast();

const audioRef = ref(null);
const isPlaying = ref(false);
const currentTime = ref(0);
const duration = ref(0);
const volume = ref(1);
const previousVolume = ref(1);
const npVisible = ref(false);

// ===== Web Audio API — visualizer phản ứng theo âm thanh thật =====
let audioCtx = null;
let analyser = null;
let sourceNode = null;
let dataArray = null;
let rafId = null;
const visualizerData = ref(new Array(24).fill(0));

const ensureAudioGraph = () => {
  if (audioCtx || !audioRef.value) return;
  try {
    const Ctx = window.AudioContext || window.webkitAudioContext;
    audioCtx = new Ctx();
    analyser = audioCtx.createAnalyser();
    analyser.fftSize = 64;
    analyser.smoothingTimeConstant = 0.8;
    sourceNode = audioCtx.createMediaElementSource(audioRef.value);
    sourceNode.connect(analyser);
    analyser.connect(audioCtx.destination);
    dataArray = new Uint8Array(analyser.frequencyBinCount);
  } catch (err) {
    // Một số trình duyệt cũ / môi trường không hỗ trợ Web Audio API — app vẫn phát nhạc bình thường, chỉ mất hiệu ứng visualizer
    console.warn('Không khởi tạo được Web Audio API, visualizer sẽ không hoạt động.', err);
  }
};

const tick = () => {
  if (analyser && dataArray) {
    analyser.getByteFrequencyData(dataArray);
    visualizerData.value = Array.from(dataArray).slice(0, 24);
  }
  rafId = requestAnimationFrame(tick);
};

const setPlaying = (value) => {
  isPlaying.value = value;
  emit('update:is-playing', value);
};

watch(() => props.currentSong, async (song) => {
  if (!song) return;
  ensureAudioGraph();
  audioCtx?.resume();
  await nextTick(); // đợi :src cập nhật xong trên DOM rồi mới play, thay cho setTimeout không ổn định
  try {
    await audioRef.value.play();
    setPlaying(true);
  } catch (err) {
    // Trình duyệt chặn autoplay hoặc file lỗi — không để lỗi rơi im lặng ngoài console
    setPlaying(false);
  }
});

const togglePlay = () => {
  ensureAudioGraph();
  audioCtx?.resume();
  if (isPlaying.value) {
    audioRef.value.pause();
    setPlaying(false);
  } else {
    audioRef.value.play().then(() => setPlaying(true)).catch(() => setPlaying(false));
  }
};

const onTimeUpdate = () => currentTime.value = audioRef.value.currentTime;
const onLoadedMetadata = () => duration.value = audioRef.value.duration;
const seek = () => audioRef.value.currentTime = currentTime.value;
const seekTo = (value) => {
  currentTime.value = value;
  if (audioRef.value) audioRef.value.currentTime = value;
};

const updateVolume = () => {
  audioRef.value.volume = volume.value;
  if (volume.value > 0) previousVolume.value = volume.value;
};

const toggleMute = () => {
  if (volume.value > 0) {
    previousVolume.value = volume.value;
    volume.value = 0;
  } else {
    volume.value = previousVolume.value || 1;
  }
  if (audioRef.value) audioRef.value.volume = volume.value;
};

const onEnded = () => {
  if (props.repeatMode === 'one') {
    audioRef.value.currentTime = 0;
    audioRef.value.play().catch(() => {});
    setPlaying(true);
    return;
  }
  setPlaying(false);
  emit('next');
};

const onAudioError = () => {
  if (props.currentSong) {
    showToast(`Không phát được "${props.currentSong.title}" — file có thể bị thiếu hoặc lỗi.`, { type: 'error' });
  }
  setPlaying(false);
};

const formatTime = (time) => {
  if (!time || isNaN(time)) return "0:00";
  const m = Math.floor(time / 60);
  const s = Math.floor(time % 60);
  return `${m}:${s < 10 ? '0' : ''}${s}`;
};

const repeatTitle = computed(() => {
  if (props.repeatMode === 'one') return 'Lặp lại: 1 bài';
  if (props.repeatMode === 'all') return 'Lặp lại: tất cả';
  return 'Lặp lại: tắt';
});

const progressStyle = computed(() => {
  const pct = duration.value ? (currentTime.value / duration.value) * 100 : 0;
  return { '--fill': `${pct}%` };
});

const volumeStyle = computed(() => ({ '--fill': `${volume.value * 100}%` }));

// ===== Phím tắt bàn phím =====
const isTypingTarget = (el) => {
  if (!el) return false;
  const tag = el.tagName;
  return tag === 'INPUT' || tag === 'TEXTAREA' || el.isContentEditable;
};

const handleKeydown = (e) => {
  if (isTypingTarget(e.target)) return;

  if (e.key === 'Escape' && npVisible.value) {
    npVisible.value = false;
    return;
  }

  // Bỏ qua khi đang focus vào 1 nút bấm để không bị bấm đúp (Space/Enter đã có hành vi mặc định của trình duyệt)
  if (e.target.tagName === 'BUTTON' && (e.key === ' ' || e.key === 'Enter')) return;

  switch (e.key) {
    case ' ':
      e.preventDefault();
      togglePlay();
      break;
    case 'ArrowRight':
      if (props.currentSong) { e.preventDefault(); emit('next'); }
      break;
    case 'ArrowLeft':
      if (props.currentSong) { e.preventDefault(); emit('prev'); }
      break;
    case 'm':
    case 'M':
      toggleMute();
      break;
  }
};

onMounted(() => {
  window.addEventListener('keydown', handleKeydown);
  rafId = requestAnimationFrame(tick);
});

onUnmounted(() => {
  window.removeEventListener('keydown', handleKeydown);
  if (rafId) cancelAnimationFrame(rafId);
  audioCtx?.close();
});
</script>

<style scoped>
.player-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 20px;
  height: 100%;
}

.song-info {
  display: flex;
  align-items: center;
  width: 30%;
  min-width: 0;
  cursor: pointer;
  border-radius: 10px;
  padding: 6px 8px;
  margin-left: -8px;
  transition: background 0.15s ease;
}

.song-info:not(.empty):hover {
  background: rgba(255, 255, 255, 0.04);
}

.song-info:not(.empty):hover .expand-hint {
  opacity: 1;
}

.song-info.empty {
  cursor: default;
}

.expand-hint {
  margin-left: 8px;
  color: var(--text-faint);
  font-size: 12px;
  opacity: 0;
  transition: opacity 0.15s ease;
  flex-shrink: 0;
}

.cover-wrap {
  width: 52px;
  height: 52px;
  border-radius: 50%;
  margin-right: 15px;
  flex-shrink: 0;
  overflow: hidden;
  border: 1px solid var(--hairline);
  box-shadow: 0 4px 12px rgba(0,0,0,0.4);
}

.cover-wrap.placeholder {
  background: var(--panel-bg-hover);
}

.cover-wrap.spinning {
  animation: spin 5s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.cover-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.details {
  min-width: 0;
}

.title {
  font-size: 13.5px;
  font-weight: 700;
  color: var(--text-main);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.artist {
  font-size: 12px;
  color: var(--text-sub);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  margin-top: 2px;
}

.title.muted, .artist.muted {
  color: var(--text-faint);
}

.player-controls {
  display: flex;
  flex-direction: column;
  align-items: center;
  width: 40%;
}

.buttons {
  display: flex;
  align-items: center;
  gap: 22px;
  margin-bottom: 8px;
}

.control-btn {
  background: none;
  border: none;
  color: var(--text-sub);
  font-size: 16px;
  cursor: pointer;
  transition: color 0.2s ease, transform 0.15s ease;
}

.control-btn:hover:not(:disabled) {
  color: var(--text-main);
  transform: scale(1.08);
}

.control-btn:disabled {
  opacity: 0.3;
  cursor: default;
}

.shuffle-btn,
.repeat-btn {
  position: relative;
  width: 30px;
  height: 30px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 9px;
  border: 1px solid var(--hairline-soft);
  background: transparent;
  color: var(--text-sub);
  cursor: pointer;
  transition: background 0.25s ease, color 0.25s ease, border-color 0.25s ease,
    transform 0.15s ease, box-shadow 0.25s ease;
}

.shuffle-icon,
.repeat-btn svg {
  width: 15px;
  height: 15px;
}

.repeat-one {
  font-family: var(--font-mono);
  font-weight: 700;
  font-size: 12px;
}

.shuffle-btn:hover:not(.active),
.repeat-btn:hover:not(.active) {
  color: var(--text-main);
  border-color: var(--hairline);
  background: rgba(255, 255, 255, 0.05);
}

.shuffle-btn:active,
.repeat-btn:active {
  transform: scale(0.9);
}

.shuffle-btn.active,
.repeat-btn.active {
  color: #100d08;
  border-color: transparent;
  background: linear-gradient(135deg, var(--gold-bright), var(--gold));
  box-shadow: 0 4px 14px rgba(232, 184, 109, 0.35);
  transform: scale(1.04);
}

.shuffle-btn.active:hover,
.repeat-btn.active:hover {
  transform: scale(1.1);
}

.play-btn {
  width: 34px;
  height: 34px;
  border-radius: 50%;
  border: none;
  cursor: pointer;
  background: linear-gradient(135deg, var(--gold-bright), var(--gold));
  color: #100d08;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 13px;
  transition: transform 0.15s ease;
}

.play-btn:hover:not(:disabled) {
  transform: scale(1.06);
}

.play-btn:disabled {
  opacity: 0.35;
  cursor: default;
}

.play-icon {
  margin-left: 2px;
}

.progress-container {
  display: flex;
  align-items: center;
  width: 100%;
  gap: 10px;
}

.time {
  font-family: var(--font-mono);
  font-size: 11px;
  color: var(--text-faint);
  width: 34px;
  text-align: center;
  flex-shrink: 0;
}

input[type="range"] {
  -webkit-appearance: none;
  appearance: none;
  height: 4px;
  border-radius: 2px;
  background: linear-gradient(to right, var(--gold) 0%, var(--gold) var(--fill, 0%), rgba(255,255,255,0.12) var(--fill, 0%), rgba(255,255,255,0.12) 100%);
  cursor: pointer;
  outline: none;
}

input[type="range"]::-webkit-slider-thumb {
  -webkit-appearance: none;
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background: var(--gold-bright);
  box-shadow: 0 0 0 3px rgba(232, 184, 109, 0.15);
  cursor: pointer;
  opacity: 0;
  transition: opacity 0.15s ease;
}

.progress-bar:hover::-webkit-slider-thumb,
.volume-bar:hover::-webkit-slider-thumb {
  opacity: 1;
}

.progress-bar {
  flex: 1;
}

.volume-control {
  width: 30%;
  display: flex;
  justify-content: flex-end;
  align-items: center;
  gap: 8px;
}

.queue-toggle {
  background: none;
  border: none;
  color: var(--text-sub);
  font-size: 14px;
  cursor: pointer;
  padding: 4px 6px;
  border-radius: 6px;
  transition: color 0.15s ease, background 0.15s ease;
}

.queue-toggle:hover {
  color: var(--text-main);
  background: rgba(255, 255, 255, 0.06);
}

.vol-icon {
  background: none;
  border: none;
  font-size: 13px;
  opacity: 0.8;
  cursor: pointer;
  padding: 4px;
  border-radius: 6px;
  transition: opacity 0.15s ease, background 0.15s ease;
}

.vol-icon:hover {
  opacity: 1;
  background: rgba(255, 255, 255, 0.06);
}

.volume-bar {
  width: 90px;
}

@media (max-width: 720px) {
  .expand-hint {
    display: none;
  }
}

/* ===== Mobile: bỏ cột volume, thu gọn cover + controls để vừa 1 hàng ===== */
@media (max-width: 640px) {
  .player-bar {
    padding: 0 10px;
    gap: 8px;
  }

  .song-info {
    width: auto;
    flex: 1 1 auto;
    margin-left: 0;
    padding: 6px 4px;
  }

  .cover-wrap {
    width: 40px;
    height: 40px;
    margin-right: 10px;
  }

  .details {
    max-width: 34vw;
  }

  .player-controls {
    width: auto;
    flex: 0 0 auto;
  }

  .buttons {
    gap: 14px;
    margin-bottom: 0;
  }

  /* Trên mobile chỉ giữ nút Play/Prev/Next; ẩn thanh tua + shuffle/repeat để tránh chật,
     người dùng vẫn tua được qua màn hình Đang phát toàn màn hình (NowPlayingView) */
  .progress-container,
  .shuffle-btn,
  .repeat-btn {
    display: none;
  }

  .volume-control {
    width: auto;
    flex: 0 0 auto;
    gap: 4px;
  }

  .volume-bar {
    display: none;
  }
}

@media (max-width: 380px) {
  .details {
    max-width: 26vw;
  }

  .queue-toggle {
    display: none;
  }
}
</style>