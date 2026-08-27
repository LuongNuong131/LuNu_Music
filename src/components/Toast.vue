<template>
  <Teleport to="body">
    <div class="toast-stack" aria-live="polite" aria-atomic="false">
      <TransitionGroup name="toast" tag="div" class="toast-list">
        <article
          v-for="t in toasts"
          :key="t.id"
          class="toast-item"
          :class="`is-${t.type}`"
          role="status"
          @mouseenter="pauseToast(t.id)"
          @mouseleave="resumeToast(t.id)"
          @focusin="pauseToast(t.id)"
          @focusout="resumeToast(t.id)"
        >
          <span class="toast-accent" aria-hidden="true"></span>
          <span class="toast-icon" :class="`icon-${t.type}`" aria-hidden="true">
            {{ iconFor(t.type) }}
          </span>
          <span class="toast-content">
            <strong class="toast-label">{{ labelFor(t.type) }}</strong>
            <span class="toast-msg">{{ t.message }}</span>
          </span>
          <button
            type="button"
            class="toast-close"
            aria-label="Đóng thông báo"
            title="Đóng thông báo"
            @click="dismissToast(t.id)"
          >
            <span aria-hidden="true">×</span>
          </button>
        </article>
      </TransitionGroup>
    </div>
  </Teleport>
</template>

<script setup>
import { useToast } from '../composables/useToast.js';

const { toasts, dismissToast, pauseToast, resumeToast } = useToast();

const iconFor = (type) => {
  if (type === 'success') return '✓';
  if (type === 'error') return '!';
  if (type === 'warning') return '⚠';
  return 'i';
};

const labelFor = (type) => {
  if (type === 'success') return 'Thành công';
  if (type === 'error') return 'Có lỗi xảy ra';
  if (type === 'warning') return 'Lưu ý';
  return 'Thông báo';
};
</script>

<style scoped>
.toast-stack {
  position: fixed;
  left: 50%;
  bottom: calc(112px + env(safe-area-inset-bottom, 0px));
  transform: translateX(-50%);
  z-index: 200;
  width: min(420px, calc(100vw - 24px));
  max-height: min(66vh, 520px);
  pointer-events: none;
}

.toast-list {
  display: flex;
  flex-direction: column;
  align-items: stretch;
  gap: 10px;
  max-height: inherit;
  overflow-y: auto;
  padding: 3px;
  scrollbar-width: none;
}

.toast-list::-webkit-scrollbar {
  display: none;
}

.toast-item {
  --toast-color: var(--gold-bright);
  --toast-soft: rgba(230, 178, 74, 0.14);
  position: relative;
  display: grid;
  grid-template-columns: 4px 30px minmax(0, 1fr) 28px;
  align-items: center;
  gap: 11px;
  min-width: 0;
  padding: 13px 12px 13px 0;
  overflow: hidden;
  pointer-events: auto;
  color: var(--text-main);
  background: linear-gradient(135deg, rgba(39, 31, 22, 0.98), rgba(16, 13, 8, 0.98));
  border: 1px solid color-mix(in srgb, var(--toast-color) 28%, var(--hairline));
  border-radius: 16px;
  box-shadow: 0 22px 58px rgba(0, 0, 0, 0.48), 0 0 28px var(--toast-soft), 0 3px 12px rgba(0, 0, 0, 0.24);
  backdrop-filter: blur(18px);
  isolation: isolate;
}

.toast-item.is-success {
  --toast-color: #8fca8a;
  --toast-soft: rgba(143, 202, 138, 0.14);
}

.toast-item.is-error {
  --toast-color: #e98276;
  --toast-soft: rgba(233, 130, 118, 0.14);
}

.toast-item.is-warning {
  --toast-color: #e9ba65;
  --toast-soft: rgba(233, 186, 101, 0.14);
}

.toast-accent {
  align-self: stretch;
  width: 4px;
  min-height: 30px;
  background: linear-gradient(180deg, color-mix(in srgb, var(--toast-color) 85%, white), var(--toast-color));
  box-shadow: 0 0 18px color-mix(in srgb, var(--toast-color) 52%, transparent);
}

.toast-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 30px;
  height: 30px;
  color: var(--toast-color);
  font-size: 14px;
  font-weight: 800;
  background: var(--toast-soft);
  border: 1px solid color-mix(in srgb, var(--toast-color) 24%, transparent);
  border-radius: 10px;
}

.toast-icon.icon-error {
  font-size: 13px;
}

.toast-icon.icon-warning {
  font-size: 13px;
}

.toast-content {
  display: flex;
  flex-direction: column;
  gap: 3px;
  min-width: 0;
}

.toast-label {
  color: color-mix(in srgb, var(--toast-color) 86%, white);
  font-size: 10px;
  font-weight: 800;
  letter-spacing: 0.1em;
  line-height: 1.2;
  text-transform: uppercase;
}

.toast-msg {
  min-width: 0;
  overflow-wrap: anywhere;
  word-break: break-word;
  color: var(--text-main);
  font-size: 13px;
  font-weight: 600;
  line-height: 1.45;
}

.toast-close {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  padding: 0;
  color: var(--text-muted);
  font-size: 22px;
  font-weight: 300;
  line-height: 1;
  cursor: pointer;
  background: transparent;
  border: 1px solid transparent;
  border-radius: 9px;
  transition: color 180ms var(--spring-soft), background 180ms var(--spring-soft), border-color 180ms var(--spring-soft), transform 180ms var(--spring);
}

.toast-close:hover,
.toast-close:focus-visible {
  color: var(--text-main);
  background: var(--toast-soft);
  border-color: color-mix(in srgb, var(--toast-color) 28%, transparent);
  outline: none;
  transform: scale(1.04);
}

.toast-close:active {
  transform: scale(0.96);
}

.toast-enter-active,
.toast-leave-active,
.toast-move {
  transition: opacity 280ms var(--spring-soft), transform 420ms var(--spring);
}

.toast-enter-from,
.toast-leave-to {
  opacity: 0;
  transform: translateY(18px) scale(.94);
}

.toast-leave-active {
  position: absolute;
  right: 3px;
  left: 3px;
}

@media (max-width: 600px) {
  .toast-stack {
    bottom: calc(104px + env(safe-area-inset-bottom, 0px));
    width: min(420px, calc(100vw - 16px));
  }

  .toast-item {
    grid-template-columns: 4px 28px minmax(0, 1fr) 26px;
    gap: 9px;
    padding-top: 11px;
    padding-bottom: 11px;
    border-radius: 14px;
  }

  .toast-icon {
    width: 28px;
    height: 28px;
  }

  .toast-msg {
    font-size: 12px;
  }
}

@media (prefers-reduced-motion: reduce) {
  .toast-enter-active,
  .toast-leave-active,
  .toast-move,
  .toast-close {
    transition: none;
  }
}
</style>
