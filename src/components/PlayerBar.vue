<template>
  <footer class="player-bar" :class="{ 'has-error': state.error }">
    <button v-if="state.currentSong" class="now-track" @click="state.nowPlayingVisible = true" aria-label="Mở trình phát toàn màn hình">
      <div class="mini-art" :class="{ spinning: state.isPlaying }"><img :src="state.currentSong.cover || '/images/ChoCiu.jpg'" :alt="state.currentSong.title" /><span class="mini-art-ring"></span></div>
      <div class="track-details"><strong class="track-title">{{ state.currentSong.title }}</strong><span class="track-artist">{{ state.currentSong.artist }}</span></div>
      <span class="expand-hint">↗</span>
    </button>
    <div v-else class="now-track empty"><div class="mini-art placeholder">♪</div><div class="track-details"><strong class="track-title muted">Chọn một bài để bắt đầu</strong><span class="track-artist">LuNu Music · personal library</span></div></div>

    <div class="player-controls">
      <div class="control-row">
        <button class="icon-control optional" :class="{ active: state.shuffle }" @click="toggleShuffle" title="Phát ngẫu nhiên" aria-label="Phát ngẫu nhiên">⇄</button>
        <button class="icon-control" @click="previous" :disabled="!state.currentSong" title="Bài trước" aria-label="Bài trước">|◀</button>
        <button class="play-btn" @click="togglePlay" :disabled="!state.currentSong" aria-label="Phát hoặc tạm dừng"><span v-if="state.isLoading">…</span><span v-else-if="state.isPlaying">Ⅱ</span><span v-else>▶</span></button>
        <button class="icon-control" @click="next" :disabled="!state.currentSong" title="Bài tiếp" aria-label="Bài tiếp">▶|</button>
        <button class="icon-control optional" :class="{ active: state.repeatMode !== 'off' }" @click="toggleRepeat" title="Chế độ lặp" aria-label="Chế độ lặp"><span v-if="state.repeatMode === 'one'">↻¹</span><span v-else>↻</span></button>
      </div>
      <div class="progress-container"><span class="time">{{ formatTime(state.currentTime) }}</span><input type="range" class="progress-bar" min="0" :max="state.duration || 0" :value="state.currentTime" @input="seek($event.target.value)" :disabled="!state.currentSong" :style="progressStyle" aria-label="Tiến trình bài hát" /><span class="time">{{ formatTime(state.duration) }}</span></div>
      <p v-if="state.error" class="player-error" role="status">{{ state.error }}</p>
    </div>

    <div class="player-actions"><button class="queue-toggle" :class="{ active: state.queueVisible }" @click="state.queueVisible = true" title="Hàng đợi" aria-label="Mở hàng đợi">☷</button><button class="volume-icon" @click="toggleMute" title="Tắt hoặc bật tiếng" aria-label="Tắt hoặc bật tiếng">{{ state.muted || state.volume === 0 ? '○' : '◖' }}</button><input type="range" class="volume-bar" min="0" max="1" step="0.01" :value="state.muted ? 0 : state.volume" @input="setVolume($event.target.value)" :style="volumeStyle" aria-label="Âm lượng" /><span class="quality-pill">HI-FI</span></div>

    <audio v-if="state.currentSong?.url" ref="audioRef" :src="state.currentSong.url" preload="metadata" @timeupdate="onTimeUpdate" @loadedmetadata="onLoadedMetadata" @waiting="handleAudioWaiting" @canplay="handleAudioCanPlay" @error="handleAudioError" @ended="handleAudioEnded"></audio>
  </footer>
</template>

<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue';
import { usePlayer, setAudioElement, handleAudioLoaded, handleAudioTimeUpdate, handleAudioWaiting, handleAudioCanPlay, handleAudioError, handleAudioEnded, shouldPlayerAutoplay } from '../store/playerState';

const { state, togglePlay, seek, setVolume, toggleMute, toggleShuffle, toggleRepeat, next, previous } = usePlayer();
const audioRef = ref(null);

onMounted(() => setAudioElement(audioRef.value));
onBeforeUnmount(() => setAudioElement(null));

watch(() => state.currentSong?.url, async (url) => {
  await nextTick();
  setAudioElement(audioRef.value);
  if (!audioRef.value) return;
  audioRef.value.load();
  if (!url) audioRef.value.pause();
});

const onTimeUpdate = () => handleAudioTimeUpdate(audioRef.value?.currentTime || 0);
const onLoadedMetadata = () => handleAudioLoaded(audioRef.value?.duration || 0);
const progressStyle = computed(() => ({ '--fill': `${state.duration ? (state.currentTime / state.duration) * 100 : 0}%` }));
const volumeStyle = computed(() => ({ '--fill': `${(state.muted ? 0 : state.volume) * 100}%` }));
const formatTime = (time) => { if (!Number.isFinite(time) || time < 0) return '0:00'; const minutes = Math.floor(time / 60); const seconds = Math.floor(time % 60); return `${minutes}:${String(seconds).padStart(2, '0')}`; };
</script>

<style scoped>
.player-bar { position: relative; z-index: 40; display: flex; align-items: center; justify-content: space-between; gap: 24px; min-height: 88px; padding: 13px clamp(16px, 2.7vw, 38px); border-top: 1px solid var(--hairline); background: rgba(11, 13, 19, .88); backdrop-filter: blur(22px); }.now-track { display: flex; align-items: center; min-width: 0; width: 29%; padding: 6px 8px; margin-left: -8px; border: 0; border-radius: 14px; background: transparent; color: inherit; text-align: left; cursor: pointer; }.now-track:hover { background: var(--glass); }.now-track.empty { cursor: default; }.mini-art { position: relative; width: 52px; height: 52px; flex: 0 0 auto; margin-right: 13px; border: 1px solid rgba(245,185,122,.4); border-radius: 14px; overflow: hidden; box-shadow: 0 10px 28px rgba(0,0,0,.28); }.mini-art.spinning { border-radius: 50%; animation: spin 8s linear infinite; }.mini-art img { width: 100%; height: 100%; object-fit: cover; }.mini-art-ring { position: absolute; inset: 6px; border: 1px solid rgba(255,255,255,.26); border-radius: inherit; }.placeholder { display: grid; place-items: center; background: linear-gradient(135deg, rgba(245,185,122,.16), rgba(155,140,255,.16)); color: var(--gold); font-size: 22px; }.track-details { display: flex; flex-direction: column; min-width: 0; }.track-title, .track-artist { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }.track-title { color: var(--text-main); font-size: 12px; font-weight: 700; }.track-title.muted { color: var(--text-sub); }.track-artist { margin-top: 5px; color: var(--text-sub); font-size: 10px; }.expand-hint { margin-left: 12px; color: var(--gold); opacity: 0; }.now-track:hover .expand-hint { opacity: 1; }.player-controls { display: flex; flex: 1; flex-direction: column; align-items: center; min-width: 260px; max-width: 560px; }.control-row { display: flex; align-items: center; gap: clamp(11px, 1.6vw, 23px); margin-bottom: 9px; }.icon-control, .queue-toggle, .volume-icon { display: flex; align-items: center; justify-content: center; width: 30px; height: 30px; padding: 0; border: 0; border-radius: 9px; background: transparent; color: var(--text-sub); cursor: pointer; font: 700 12px var(--font-mono); }.icon-control:hover, .icon-control.active, .queue-toggle:hover, .queue-toggle.active { color: var(--gold); background: rgba(245,185,122,.1); }.play-btn { display: grid; place-items: center; width: 42px; height: 42px; border: 0; border-radius: 50%; background: linear-gradient(135deg, var(--gold-bright), var(--gold)); color: #161017; box-shadow: 0 8px 24px rgba(245,185,122,.2); cursor: pointer; font-weight: 800; }.play-btn:hover:not(:disabled) { transform: scale(1.07); box-shadow: 0 12px 32px rgba(245,185,122,.35); }.play-btn:disabled, .icon-control:disabled { cursor: not-allowed; opacity: .4; }.progress-container { display: flex; align-items: center; width: 100%; gap: 10px; }.time { width: 34px; color: var(--text-faint); text-align: center; font: 9px var(--font-mono); }.progress-bar, .volume-bar { -webkit-appearance: none; appearance: none; height: 4px; border-radius: 999px; background: linear-gradient(to right, var(--gold) 0%, var(--gold) var(--fill, 0%), rgba(255,255,255,.11) var(--fill, 0%), rgba(255,255,255,.11) 100%); cursor: pointer; }.progress-bar { flex: 1; }.progress-bar::-webkit-slider-thumb, .volume-bar::-webkit-slider-thumb { -webkit-appearance: none; width: 12px; height: 12px; border: 2px solid var(--bg-deep); border-radius: 50%; background: var(--gold-bright); opacity: 0; transition: opacity .15s; }.progress-bar:hover::-webkit-slider-thumb, .volume-bar:hover::-webkit-slider-thumb { opacity: 1; }.player-error { width: 100%; margin: 5px 0 0; color: var(--crimson); text-align: center; font-size: 10px; }.player-actions { display: flex; align-items: center; justify-content: flex-end; gap: 7px; width: 29%; }.volume-icon { font-size: 19px; }.volume-bar { width: 82px; }.quality-pill { border: 1px solid rgba(130,229,195,.2); border-radius: 6px; padding: 4px 6px; color: var(--mint); font: 8px var(--font-mono); letter-spacing: .7px; }audio { display: none; }@media (max-width: 760px) { .optional, .volume-bar, .volume-icon, .quality-pill { display: none; }.player-bar { gap: 12px; min-height: 76px; padding: 10px 13px; }.now-track { width: auto; flex: 1; margin: 0; padding: 0; }.mini-art { width: 43px; height: 43px; margin-right: 9px; border-radius: 11px; }.track-title { font-size: 11px; }.track-artist { font-size: 9px; }.player-controls { min-width: 41px; max-width: none; flex: 0 0 auto; }.control-row { margin: 0; }.control-row .icon-control:not(:nth-child(4)) { display: none; }.control-row .icon-control:nth-child(4) { display: flex; }.play-btn { width: 42px; height: 42px; }.progress-container { display: none; }.player-actions { width: auto; }.expand-hint { display: none; } }@media (max-width: 360px) { .track-artist { display: none; }.mini-art { width: 39px; height: 39px; } }
</style>
