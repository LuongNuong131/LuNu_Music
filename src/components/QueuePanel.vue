<template>
  <Teleport to="body"
    ><Transition name="queue-reveal"
      ><div v-if="visible" class="queue-overlay" @click.self="emit('close')">
        <aside
          ref="panelRef"
          class="queue-panel"
          role="dialog"
          aria-modal="true"
          aria-labelledby="queue-title"
          tabindex="-1"
        >
          <header class="queue-header">
            <div>
              <h2 id="queue-title">Hàng đợi</h2>
              <p>{{ queue.length }} bài hát tiếp theo</p>
            </div>
            <button class="queue-icon" aria-label="Đóng hàng đợi" @click="emit('close')">
              <X :size="22" />
            </button>
          </header>
          <section v-if="currentSong" class="queue-current">
            <h3>Đang phát</h3>
            <div class="queue-current-song">
              <img :src="songArtwork(currentSong)" :alt="`Bìa ${currentSong.title}`" />
              <div>
                <strong>{{ currentSong.title }}</strong><small>{{ currentSong.artist }}</small>
              </div>
              <AudioLines :size="21" />
            </div>
          </section>
          <div class="queue-section-heading">
            <h3>Tiếp theo</h3>
            <button v-if="queue.length" @click="emit('clear')">
              <Trash2 :size="14" /> Xóa hàng đợi
            </button>
          </div>
          <div v-if="queue.length" class="queue-list">
            <article v-for="(song, index) in queue" :key="`${song.id}-${index}`" class="queue-item">
              <span>{{ String(index + 1).padStart(2, '0') }}</span><button
                class="queued-song"
                @click="emit('play', song)"
                :aria-label="`Phát ${song.title} từ hàng đợi`"
              >
                <img :src="songArtwork(song)" :alt="`Bìa ${song.title}`" loading="lazy" /><span
                  ><strong>{{ song.title }}</strong
                  ><small>{{ song.artist }}</small></span
                ></button
              ><button
                class="queue-icon remove-button"
                :aria-label="`Xóa ${song.title} khỏi hàng đợi`"
                @click="emit('remove', index)"
              >
                <X :size="17" />
              </button>
            </article>
          </div>
          <div v-else class="queue-empty">
            <ListMusic :size="35" />
            <h3>Để âm nhạc tiếp nối.</h3>
            <p>Thêm bài hát từ thư viện để tạo một phiên nghe theo cách của bạn.</p>
          </div>
          <p class="queue-footer">Hàng đợi được lưu trên thiết bị này.</p>
        </aside>
      </div></Transition
    ></Teleport
  >
</template>
<script setup>
import { ref, toRef } from 'vue';
import { AudioLines, ListMusic, Trash2, X } from '@lucide/vue';
import { songArtwork } from '../utils/artwork';
import { useDialogFocus } from '../composables/useDialogFocus';
const props = defineProps({
  visible: Boolean,
  currentSong: Object,
  queue: { type: Array, default: () => [] },
});
const emit = defineEmits(['close', 'remove', 'clear', 'play']);
const panelRef = ref(null);
useDialogFocus(toRef(props, 'visible'), panelRef, () => emit('close'));
</script>
<style scoped>
.queue-overlay {
  position: fixed;
  inset: 0;
  z-index: 320;
  display: flex;
  justify-content: flex-end;
  background: #080b1880;
  backdrop-filter: blur(5px);
}
.queue-panel {
  display: flex;
  flex-direction: column;
  width: min(440px, 100%);
  height: 100dvh;
  padding: 28px 24px 18px;
  border-left: 1px solid var(--hairline);
  background: var(--panel-solid);
  color: var(--text-main);
  outline: none;
}
.queue-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20px;
}
.queue-header h2 {
  font-size: 24px;
  letter-spacing: -0.6px;
}
.queue-header p {
  font-size: 11px;
  color: var(--text-sub);
  margin-top: 9px;
}
.queue-icon {
  display: grid;
  place-items: center;
  flex: none;
  width: 36px;
  height: 40px;
  border: 0;
  border-radius: 9px;
  background: none;
  color: var(--text-sub);
}
.queue-icon:hover {
  background: var(--accent-soft);
  color: var(--gold);
}
.queue-current {
  margin-top: 30px;
}
.queue-current h3,
.queue-section-heading h3 {
  font-size: 12px;
  font-weight: 500;
  color: var(--text-sub);
}
.queue-current-song {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-top: 13px;
  padding: 13px;
  border: 1px solid var(--hairline);
  border-radius: 12px;
  background: var(--accent-soft);
}
.queue-current-song img {
  width: 48px;
  height: 48px;
  border-radius: 8px;
  object-fit: cover;
}
.queue-current-song > div {
  display: grid;
  gap: 8px;
  flex: 1;
  min-width: 0;
}
.queue-current-song strong {
  font-size: 12px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  font-weight: 500;
}
.queue-current-song small {
  font-size: 10px;
  color: var(--text-sub);
}
.queue-current-song > svg {
  color: var(--gold);
  flex: none;
}
.queue-section-heading {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 15px;
  margin: 29px 0 13px;
}
.queue-section-heading button {
  display: flex;
  align-items: center;
  gap: 6px;
  min-height: 34px;
  border: 0;
  background: none;
  color: var(--text-faint);
  font-size: 10px;
}
.queue-section-heading button:hover {
  color: var(--crimson);
}
.queue-list {
  display: flex;
  flex-direction: column;
  gap: 7px;
  flex: 1;
  min-height: 0;
  overflow: auto;
}
.queue-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 0;
}
.queue-item > span {
  font-size: 9px;
  color: var(--text-faint);
  width: 19px;
  flex: none;
}
.queued-song {
  display: flex;
  align-items: center;
  gap: 11px;
  flex: 1;
  min-width: 0;
  border: 0;
  padding: 0;
  background: none;
  color: var(--text-main);
  text-align: left;
}
.queued-song img {
  width: 43px;
  height: 43px;
  border-radius: 8px;
  object-fit: cover;
}
.queued-song > span {
  display: grid;
  gap: 6px;
  min-width: 0;
  flex: 1;
}
.queued-song strong {
  font-size: 11px;
  font-weight: 500;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.queued-song small {
  font-size: 10px;
  color: var(--text-sub);
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
}
.remove-button:hover {
  color: var(--crimson);
}
.queue-empty {
  display: grid;
  justify-items: center;
  align-content: center;
  gap: 16px;
  flex: 1;
  text-align: center;
  padding: 30px 15px;
}
.queue-empty svg {
  color: var(--gold);
}
.queue-empty h3 {
  font-size: 18px;
  font-weight: 500;
}
.queue-empty p {
  font-size: 12px;
  color: var(--text-sub);
  line-height: 1.8;
  max-width: 280px;
}
.queue-footer {
  padding-top: 18px;
  margin-top: 18px;
  border-top: 1px solid var(--hairline);
  font-size: 10px;
  color: var(--text-faint);
}
.queue-reveal-enter-active,
.queue-reveal-leave-active {
  transition: opacity 0.15s;
}
.queue-reveal-enter-active .queue-panel,
.queue-reveal-leave-active .queue-panel {
  transition: transform 0.2s ease;
}
.queue-reveal-enter-from,
.queue-reveal-leave-to {
  opacity: 0;
}
.queue-reveal-enter-from .queue-panel,
.queue-reveal-leave-to .queue-panel {
  transform: translateX(100%);
}
@media (max-width: 760px) {
  .queue-panel {
    padding: 23px 19px 20px;
  }
  .queue-header h2 {
    font-size: 23px;
  }
  .queue-current-song strong {
    font-size: 11px;
  }
}
@media (prefers-reduced-motion: reduce) {
  .queue-reveal-enter-active,
  .queue-reveal-leave-active,
  .queue-reveal-enter-active .queue-panel,
  .queue-reveal-leave-active .queue-panel {
    transition: none;
  }
}
</style>
