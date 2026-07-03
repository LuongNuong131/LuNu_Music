<!-- src/components/QueuePanel.vue -->
<template>
  <Teleport to="body">
    <Transition name="slide">
      <div v-if="visible" class="queue-overlay" @click.self="emit('close')">
        <aside class="queue-panel">
          <div class="queue-header">
            <h3>Hàng đợi phát</h3>
            <button class="close-btn" @click="emit('close')" title="Đóng">✕</button>
          </div>

          <div class="queue-section" v-if="currentSong">
            <p class="section-label">Đang phát</p>
            <div class="queue-item now-playing">
              <img :src="currentSong.cover" :alt="currentSong.title" />
              <div class="q-info">
                <div class="q-title">{{ currentSong.title }}</div>
                <div class="q-artist">{{ currentSong.artist }}</div>
              </div>
              <span class="eq"><i></i><i></i><i></i></span>
            </div>
          </div>

          <div class="queue-section">
            <div class="section-head">
              <p class="section-label">Tiếp theo &middot; {{ queue.length }}</p>
              <button v-if="queue.length" class="clear-btn" @click="emit('clear')">Xoá hết</button>
            </div>

            <TransitionGroup name="list" tag="div" class="queue-list" v-if="queue.length">
              <div class="queue-item" v-for="(song, index) in queue" :key="song.id + '-' + index">
                <span class="q-index">{{ index + 1 }}</span>
                <img :src="song.cover" :alt="song.title" />
                <div class="q-info">
                  <div class="q-title">{{ song.title }}</div>
                  <div class="q-artist">{{ song.artist }}</div>
                </div>
                <button class="q-remove" @click="emit('remove', index)" title="Xoá khỏi hàng đợi">✕</button>
              </div>
            </TransitionGroup>

            <p v-else class="empty-hint">Hàng đợi trống. Bấm ⋯ trên một bài hát rồi chọn "Thêm vào hàng đợi" nhé.</p>
          </div>
        </aside>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
defineProps({
  visible: { type: Boolean, default: false },
  currentSong: { type: Object, default: null },
  queue: { type: Array, default: () => [] }
});

const emit = defineEmits(['close', 'remove', 'clear']);
</script>

<style scoped>
.queue-overlay {
  position: fixed;
  inset: 0;
  background: rgba(5, 4, 3, 0.45);
  z-index: 90;
  display: flex;
  justify-content: flex-end;
}

.queue-panel {
  width: 340px;
  height: 100%;
  background: linear-gradient(180deg, var(--panel-bg) 0%, #100d08 100%);
  border-left: 1px solid var(--hairline);
  padding: 22px 18px;
  overflow-y: auto;
  box-shadow: -20px 0 60px rgba(0, 0, 0, 0.45);
}

.queue-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 18px;
}

.queue-header h3 {
  font-family: var(--font-display);
  font-size: 22px;
  font-weight: 400;
  letter-spacing: 0.3px;
  color: var(--text-main);
}

.close-btn {
  background: none;
  border: none;
  color: var(--text-sub);
  font-size: 14px;
  cursor: pointer;
  padding: 6px;
}

.close-btn:hover {
  color: var(--text-main);
}

.queue-section {
  margin-bottom: 22px;
}

.section-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.section-label {
  font-family: var(--font-mono);
  font-size: 10px;
  letter-spacing: 1.5px;
  text-transform: uppercase;
  color: var(--gold-dim);
  margin-bottom: 10px;
}

.clear-btn {
  background: none;
  border: none;
  color: var(--text-faint);
  font-size: 11px;
  cursor: pointer;
  text-decoration: underline;
  margin-bottom: 10px;
}

.clear-btn:hover {
  color: var(--crimson);
}

.queue-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.queue-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px;
  border-radius: 8px;
}

.queue-item:hover {
  background: rgba(255, 255, 255, 0.04);
}

.queue-item.now-playing {
  background: rgba(232, 184, 109, 0.08);
}

.q-index {
  font-family: var(--font-mono);
  font-size: 12px;
  color: var(--text-faint);
  width: 16px;
  flex-shrink: 0;
  text-align: center;
}

.queue-item img {
  width: 38px;
  height: 38px;
  border-radius: 5px;
  object-fit: cover;
  flex-shrink: 0;
}

.q-info {
  min-width: 0;
  flex: 1;
}

.q-title {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-main);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.q-artist {
  font-size: 11.5px;
  color: var(--text-sub);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.q-remove {
  background: none;
  border: none;
  color: var(--text-faint);
  font-size: 12px;
  cursor: pointer;
  padding: 4px;
  opacity: 0;
  transition: opacity 0.15s ease;
  flex-shrink: 0;
}

.queue-item:hover .q-remove {
  opacity: 1;
}

.q-remove:hover {
  color: var(--crimson);
}

.empty-hint {
  font-size: 12.5px;
  color: var(--text-faint);
  line-height: 1.6;
}

.eq {
  display: flex;
  align-items: flex-end;
  gap: 2px;
  height: 14px;
  flex-shrink: 0;
}

.eq i {
  width: 3px;
  background: var(--gold);
  border-radius: 1px;
  animation: eq 0.9s ease-in-out infinite;
}

.eq i:nth-child(1) { height: 40%; animation-delay: -0.6s; }
.eq i:nth-child(2) { height: 100%; animation-delay: -0.3s; }
.eq i:nth-child(3) { height: 65%; animation-delay: 0s; }

@keyframes eq {
  0%, 100% { transform: scaleY(0.4); }
  50% { transform: scaleY(1); }
}

/* Transitions */
.slide-enter-active, .slide-leave-active {
  transition: opacity 0.25s ease;
}
.slide-enter-from, .slide-leave-to {
  opacity: 0;
}
.slide-enter-active .queue-panel, .slide-leave-active .queue-panel {
  transition: transform 0.25s ease;
}
.slide-enter-from .queue-panel, .slide-leave-to .queue-panel {
  transform: translateX(100%);
}

.list-enter-active, .list-leave-active {
  transition: all 0.2s ease;
}
.list-enter-from, .list-leave-to {
  opacity: 0;
  transform: translateX(12px);
}
</style>