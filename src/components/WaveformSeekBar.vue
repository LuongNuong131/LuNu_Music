<!-- src/components/WaveformSeekBar.vue -->
<template>
  <div class="wf-wrap">
    <span class="wf-time">{{ formatTime(currentTime) }}</span>

    <!-- Có dữ liệu waveform thật -> vẽ dạng sóng -->
    <div
      v-if="peaks.length && !loading"
      class="wf-bars"
      ref="barsRef"
      @mousedown="startDrag"
      @touchstart="startDrag"
      role="slider"
      :aria-valuenow="Math.round(currentTime)"
      :aria-valuemax="Math.round(duration)"
      tabindex="0"
    >
      <span
        v-for="(p, i) in peaks"
        :key="i"
        class="wf-bar"
        :class="{ played: i / peaks.length <= progress }"
        :style="{ height: `${Math.max(8, p * 100)}%` }"
      ></span>
    </div>

    <!-- Đang giải mã waveform -->
    <div v-else-if="loading" class="wf-loading">
      <span v-for="i in 28" :key="i" class="wf-loading-bar" :style="{ animationDelay: `${i * 0.03}s` }"></span>
    </div>

    <!-- Fallback: không tạo được waveform (lỗi decode/CORS) -> thanh tua thường -->
    <input
      v-else
      type="range"
      class="wf-fallback"
      min="0"
      :max="duration || 0"
      :value="currentTime"
      @input="emit('seek', Number($event.target.value))"
      :style="{ '--fill': `${progress * 100}%` }"
    />

    <span class="wf-time">{{ formatTime(duration) }}</span>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue';

const props = defineProps({
  peaks: { type: Array, default: () => [] },
  loading: { type: Boolean, default: false },
  currentTime: { type: Number, default: 0 },
  duration: { type: Number, default: 0 }
});

const emit = defineEmits(['seek']);

const barsRef = ref(null);
const progress = computed(() => (props.duration ? props.currentTime / props.duration : 0));

// Chấp nhận cả MouseEvent (clientX trực tiếp) lẫn TouchEvent (clientX nằm trong touches[0])
const clientXOf = (e) => (e.touches && e.touches.length ? e.touches[0].clientX : e.clientX);

const fractionFromEvent = (e) => {
  const rect = barsRef.value.getBoundingClientRect();
  const x = Math.min(Math.max(clientXOf(e) - rect.left, 0), rect.width);
  return rect.width ? x / rect.width : 0;
};

const seekToEvent = (e) => {
  if (!props.duration) return;
  emit('seek', fractionFromEvent(e) * props.duration);
};

const startDrag = (e) => {
  if (e.type === 'touchstart') e.preventDefault(); // tránh cuộn trang khi kéo tua trên mobile
  seekToEvent(e);

  const onMove = (ev) => {
    if (ev.type === 'touchmove') ev.preventDefault();
    seekToEvent(ev);
  };
  const onUp = () => {
    window.removeEventListener('mousemove', onMove);
    window.removeEventListener('mouseup', onUp);
    window.removeEventListener('touchmove', onMove);
    window.removeEventListener('touchend', onUp);
  };

  window.addEventListener('mousemove', onMove);
  window.addEventListener('mouseup', onUp);
  window.addEventListener('touchmove', onMove, { passive: false });
  window.addEventListener('touchend', onUp);
};

const formatTime = (time) => {
  if (!time || isNaN(time)) return '0:00';
  const m = Math.floor(time / 60);
  const s = Math.floor(time % 60);
  return `${m}:${s < 10 ? '0' : ''}${s}`;
};
</script>

<style scoped>
.wf-wrap {
  display: flex;
  align-items: center;
  gap: 10px;
  width: 100%;
}

.wf-time {
  font-family: var(--font-mono);
  font-size: 11px;
  color: var(--text-faint);
  width: 34px;
  text-align: center;
  flex-shrink: 0;
}

.wf-bars {
  flex: 1;
  height: 40px;
  display: flex;
  align-items: center;
  gap: 2px;
  cursor: pointer;
  padding: 4px 0;
  touch-action: none;
}

.wf-bar {
  flex: 1;
  min-width: 2px;
  border-radius: 2px;
  background: rgba(245, 240, 230, 0.14);
  transition: background 0.15s ease;
}

.wf-bar.played {
  background: linear-gradient(180deg, var(--gold-bright), var(--gold-dim));
}

.wf-bars:hover .wf-bar {
  background: rgba(245, 240, 230, 0.22);
}

.wf-bars:hover .wf-bar.played {
  background: linear-gradient(180deg, var(--gold-bright), var(--gold));
}

.wf-loading {
  flex: 1;
  height: 40px;
  display: flex;
  align-items: center;
  gap: 2px;
}

.wf-loading-bar {
  flex: 1;
  min-width: 2px;
  height: 30%;
  border-radius: 2px;
  background: rgba(245, 240, 230, 0.1);
  animation: wf-pulse 1s ease-in-out infinite;
}

@keyframes wf-pulse {
  0%, 100% { height: 20%; opacity: 0.5; }
  50% { height: 70%; opacity: 1; }
}

.wf-fallback {
  flex: 1;
  -webkit-appearance: none;
  appearance: none;
  height: 4px;
  border-radius: 2px;
  background: linear-gradient(to right, var(--gold) 0%, var(--gold) var(--fill, 0%), rgba(255, 255, 255, 0.14) var(--fill, 0%), rgba(255, 255, 255, 0.14) 100%);
  cursor: pointer;
  outline: none;
}

.wf-fallback::-webkit-slider-thumb {
  -webkit-appearance: none;
  width: 13px;
  height: 13px;
  border-radius: 50%;
  background: var(--gold-bright);
  box-shadow: 0 0 0 4px rgba(232, 184, 109, 0.15);
  cursor: pointer;
}
</style>