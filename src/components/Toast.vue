<!-- src/components/Toast.vue -->
<template>
  <Teleport to="body">
    <div class="toast-stack">
      <TransitionGroup name="toast">
        <div
          v-for="t in toasts"
          :key="t.id"
          class="toast-item"
          :class="t.type"
          @click="dismissToast(t.id)"
        >
          <span class="toast-icon">{{ iconFor(t.type) }}</span>
          <span class="toast-msg">{{ t.message }}</span>
        </div>
      </TransitionGroup>
    </div>
  </Teleport>
</template>

<script setup>
import { useToast } from '../composables/useToast.js';

const { toasts, dismissToast } = useToast();

const iconFor = (type) => {
  if (type === 'success') return '✓';
  if (type === 'error') return '✕';
  return '♪';
};
</script>

<style scoped>
.toast-stack {
  position: fixed;
  left: 50%;
  bottom: 112px; /* nằm trên PlayerBar (90px) một khoảng an toàn */
  transform: translateX(-50%);
  z-index: 200;
  display: flex;
  flex-direction: column-reverse;
  align-items: center;
  gap: 8px;
  pointer-events: none;
  width: min(360px, calc(100vw - 24px));
}

.toast-item {
  pointer-events: auto;
  display: flex;
  align-items: center;
  gap: 9px;
  padding: 11px 18px;
  border-radius: 999px;
  background: linear-gradient(135deg, #211c14 0%, #100d08 100%);
  border: 1px solid var(--hairline);
  box-shadow: 0 12px 30px rgba(0, 0, 0, 0.5);
  color: var(--text-main);
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  max-width: 100%;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.toast-icon {
  flex-shrink: 0;
  width: 18px;
  height: 18px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 10px;
  background: linear-gradient(135deg, var(--gold-bright), var(--gold));
  color: #100d08;
}

.toast-item.error .toast-icon {
  background: var(--crimson);
  color: var(--text-main);
}

.toast-msg {
  overflow: hidden;
  text-overflow: ellipsis;
}

.toast-enter-active,
.toast-leave-active {
  transition: all 0.25s ease;
}
.toast-enter-from {
  opacity: 0;
  transform: translateY(10px) scale(0.95);
}
.toast-leave-to {
  opacity: 0;
  transform: translateY(-6px) scale(0.95);
}
</style>