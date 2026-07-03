<!-- src/components/NowPlayingView.vue -->
<!--
  Màn hình "Đang phát" toàn màn hình — điểm nhấn thị giác chính của app.
  Component này thuần hiển thị (presentational): mọi state âm thanh thật
  (audioRef, AnalyserNode...) vẫn nằm ở PlayerBar.vue, ở đây chỉ nhận props/emit.
-->
<template>
  <Teleport to="body">
    <Transition name="np-fade">
      <div v-if="visible" class="np-overlay">
        <!-- Nền mờ lấy từ ảnh cover, tạo chiều sâu -->
        <div class="np-bg" :style="{ backgroundImage: `url(${currentSong?.cover})` }"></div>
        <div class="np-bg-tint"></div>

        <button class="np-close" @click="emit('close')" title="Thu nhỏ (Esc)">⌄</button>

        <div class="np-body">
          <div class="np-stage">
            <!-- Đĩa than xoay + ảnh cover ở giữa -->
            <div class="np-vinyl" :class="{ spinning: isPlaying }">
              <div class="np-vinyl-grooves"></div>
              <img v-if="currentSong" :src="currentSong.cover" class="np-cover" :alt="currentSong.title" />
            </div>

            <!-- Visualizer phản ứng theo tần số âm thanh thật (Web Audio API) -->
            <div class="np-visualizer" aria-hidden="true">
              <span
                v-for="(v, i) in visualizerData"
                :key="i"
                class="np-bar"
                :style="{ height: barHeight(v) }"
              ></span>
            </div>
          </div>

          <div class="np-meta">
            <p class="np-eyebrow">{{ isPlaying ? 'Đang phát' : 'Tạm dừng' }}</p>
            <h1 class="np-title">{{ currentSong?.title || 'Chưa phát bài nào' }}</h1>
            <p class="np-artist">{{ currentSong?.artist || 'Chọn một track để bắt đầu' }}</p>
          </div>

          <div class="np-progress">
            <span class="np-time">{{ formatTime(currentTime) }}</span>
            <input
              type="range"
              class="np-range"
              min="0"
              :max="duration || 0"
              :value="currentTime"
              @input="emit('seek', Number($event.target.value))"
              :disabled="!currentSong"
              :style="{ '--fill': progressPct + '%' }"
            />
            <span class="np-time">{{ formatTime(duration) }}</span>
          </div>

          <div class="np-controls">
            <button
              class="np-icon-btn"
              :class="{ active: isShuffle }"
              @click="emit('toggle-shuffle')"
              title="Shuffle"
            >
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                <polyline points="16 3 21 3 21 8"></polyline>
                <line x1="4" y1="20" x2="21" y2="3"></line>
                <polyline points="21 16 21 21 16 21"></polyline>
                <line x1="15" y1="15" x2="21" y2="21"></line>
                <line x1="4" y1="4" x2="9" y2="9"></line>
              </svg>
            </button>

            <button class="np-round-btn" @click="emit('prev')" :disabled="!currentSong" title="Previous (←)">⏮</button>

            <button class="np-play-btn" @click="emit('toggle-play')" :disabled="!currentSong" title="Play/Pause (Space)">
              <span v-if="isPlaying">⏸</span>
              <span v-else class="play-icon">▶</span>
            </button>

            <button class="np-round-btn" @click="emit('next')" :disabled="!currentSong" title="Next (→)">⏭</button>

            <button
              class="np-icon-btn"
              :class="{ active: repeatMode !== 'off' }"
              @click="emit('toggle-repeat')"
              :title="repeatLabel"
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

          <p class="np-hint">Phím tắt: Space phát/dừng · ← → chuyển bài · M tắt tiếng</p>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { computed } from 'vue';

const props = defineProps({
  visible: { type: Boolean, default: false },
  currentSong: { type: Object, default: null },
  isPlaying: { type: Boolean, default: false },
  isShuffle: { type: Boolean, default: false },
  repeatMode: { type: String, default: 'off' }, // 'off' | 'all' | 'one'
  currentTime: { type: Number, default: 0 },
  duration: { type: Number, default: 0 },
  visualizerData: { type: Array, default: () => [] }
});

const emit = defineEmits([
  'close', 'toggle-play', 'next', 'prev', 'toggle-shuffle', 'toggle-repeat', 'seek'
]);

const repeatLabel = computed(() => {
  if (props.repeatMode === 'one') return 'Lặp lại: 1 bài';
  if (props.repeatMode === 'all') return 'Lặp lại: tất cả';
  return 'Lặp lại: tắt';
});

const progressPct = computed(() =>
  props.duration ? (props.currentTime / props.duration) * 100 : 0
);

const barHeight = (v) => `${Math.max(6, (v / 255) * 100)}%`;

const formatTime = (time) => {
  if (!time || isNaN(time)) return '0:00';
  const m = Math.floor(time / 60);
  const s = Math.floor(time % 60);
  return `${m}:${s < 10 ? '0' : ''}${s}`;
};
</script>

<style scoped>
.np-overlay {
  position: fixed;
  inset: 0;
  z-index: 150;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background: var(--bg-color);
}

.np-bg {
  position: absolute;
  inset: -40px;
  background-size: cover;
  background-position: center;
  filter: blur(60px) saturate(1.3) brightness(0.55);
  transform: scale(1.15);
}

.np-bg-tint {
  position: absolute;
  inset: 0;
  background:
    radial-gradient(90% 60% at 50% 100%, rgba(11, 10, 8, 0.4) 0%, rgba(11, 10, 8, 0.92) 100%),
    linear-gradient(180deg, rgba(11, 10, 8, 0.55) 0%, rgba(11, 10, 8, 0.85) 100%);
}

.np-close {
  position: relative;
  z-index: 2;
  align-self: center;
  margin-top: 18px;
  width: 40px;
  height: 26px;
  border-radius: 999px;
  border: 1px solid var(--hairline);
  background: rgba(255, 255, 255, 0.04);
  color: var(--text-sub);
  font-size: 15px;
  cursor: pointer;
  transition: color 0.15s ease, background 0.15s ease;
}

.np-close:hover {
  color: var(--text-main);
  background: rgba(255, 255, 255, 0.08);
}

.np-body {
  position: relative;
  z-index: 2;
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 20px 24px 40px;
  gap: 22px;
}

.np-stage {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.np-vinyl {
  width: min(300px, 42vh);
  height: min(300px, 42vh);
  border-radius: 50%;
  background: repeating-radial-gradient(circle at center, #1a1712 0px, #1a1712 2px, #0d0b08 3px, #0d0b08 4px);
  border: 1px solid var(--hairline);
  box-shadow: 0 30px 80px rgba(0, 0, 0, 0.6);
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
}

.np-vinyl.spinning {
  animation: np-spin 9s linear infinite;
}

@keyframes np-spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.np-cover {
  width: 44%;
  height: 44%;
  border-radius: 50%;
  object-fit: cover;
  border: 3px solid rgba(245, 240, 230, 0.08);
  box-shadow: 0 0 0 1px var(--hairline-soft), 0 10px 26px rgba(0, 0, 0, 0.5);
}

.np-visualizer {
  display: flex;
  align-items: flex-end;
  justify-content: center;
  gap: 4px;
  height: 44px;
  margin-top: 22px;
  width: min(260px, 60vw);
}

.np-bar {
  flex: 1;
  min-width: 3px;
  max-width: 8px;
  border-radius: 3px 3px 0 0;
  background: linear-gradient(180deg, var(--gold-bright), var(--gold-dim));
  transition: height 0.08s linear;
}

.np-meta {
  text-align: center;
  max-width: 480px;
}

.np-eyebrow {
  font-family: var(--font-mono);
  font-size: 10.5px;
  letter-spacing: 2px;
  text-transform: uppercase;
  color: var(--gold-dim);
  margin-bottom: 8px;
}

.np-title {
  font-family: var(--font-display);
  font-size: 34px;
  font-weight: 400;
  letter-spacing: 0.4px;
  color: var(--text-main);
  line-height: 1.15;
}

.np-artist {
  margin-top: 6px;
  font-size: 14px;
  color: var(--text-sub);
}

.np-progress {
  width: min(420px, 82vw);
  display: flex;
  align-items: center;
  gap: 10px;
}

.np-time {
  font-family: var(--font-mono);
  font-size: 11px;
  color: var(--text-faint);
  width: 34px;
  text-align: center;
  flex-shrink: 0;
}

.np-range {
  flex: 1;
  -webkit-appearance: none;
  appearance: none;
  height: 4px;
  border-radius: 2px;
  background: linear-gradient(to right, var(--gold) 0%, var(--gold) var(--fill, 0%), rgba(255, 255, 255, 0.14) var(--fill, 0%), rgba(255, 255, 255, 0.14) 100%);
  cursor: pointer;
  outline: none;
}

.np-range::-webkit-slider-thumb {
  -webkit-appearance: none;
  width: 13px;
  height: 13px;
  border-radius: 50%;
  background: var(--gold-bright);
  box-shadow: 0 0 0 4px rgba(232, 184, 109, 0.15);
  cursor: pointer;
}

.np-controls {
  display: flex;
  align-items: center;
  gap: 26px;
}

.np-icon-btn {
  background: none;
  border: none;
  color: var(--text-sub);
  width: 30px;
  height: 30px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: color 0.2s ease, transform 0.15s ease;
}

.np-icon-btn svg {
  width: 17px;
  height: 17px;
}

.np-icon-btn:hover {
  color: var(--text-main);
}

.np-icon-btn.active {
  color: var(--gold);
}

.repeat-one {
  font-family: var(--font-mono);
  font-weight: 700;
  font-size: 13px;
}

.np-round-btn {
  background: none;
  border: none;
  color: var(--text-main);
  font-size: 22px;
  cursor: pointer;
  transition: transform 0.15s ease, opacity 0.15s ease;
}

.np-round-btn:hover:not(:disabled) {
  transform: scale(1.1);
}

.np-round-btn:disabled {
  opacity: 0.3;
  cursor: default;
}

.np-play-btn {
  width: 62px;
  height: 62px;
  border-radius: 50%;
  border: none;
  cursor: pointer;
  background: linear-gradient(135deg, var(--gold-bright), var(--gold));
  color: #100d08;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 22px;
  box-shadow: 0 12px 30px rgba(232, 184, 109, 0.3);
  transition: transform 0.15s ease;
}

.np-play-btn:hover:not(:disabled) {
  transform: scale(1.05);
}

.np-play-btn:disabled {
  opacity: 0.4;
  cursor: default;
}

.play-icon {
  margin-left: 3px;
}

.np-hint {
  font-family: var(--font-mono);
  font-size: 10.5px;
  letter-spacing: 0.5px;
  color: var(--text-faint);
  margin-top: 4px;
}

.np-fade-enter-active,
.np-fade-leave-active {
  transition: opacity 0.28s ease;
}
.np-fade-enter-from,
.np-fade-leave-to {
  opacity: 0;
}
.np-fade-enter-active .np-body,
.np-fade-leave-active .np-body {
  transition: transform 0.28s ease, opacity 0.28s ease;
}
.np-fade-enter-from .np-body,
.np-fade-leave-to .np-body {
  transform: translateY(16px);
  opacity: 0;
}

@media (max-width: 720px) {
  .np-title { font-size: 26px; }
  .np-controls { gap: 18px; }
}
</style>