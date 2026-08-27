// Toast singleton cho toàn ứng dụng.
// Giữ API showToast(message, { type, duration }) để các feature hiện tại không bị breaking change.
import { ref } from 'vue';

const MAX_TOASTS = 4;
const DEDUPE_WINDOW_MS = 900;
const toasts = ref([]);
const timers = new Map();
let counter = 0;

function normalizeType(type) {
  return ['success', 'error', 'warning', 'info'].includes(type) ? type : 'info';
}

function clearTimer(id) {
  const timer = timers.get(id);
  if (timer) {
    clearTimeout(timer);
    timers.delete(id);
  }
}

function removeToast(id) {
  clearTimer(id);
  toasts.value = toasts.value.filter((toast) => toast.id !== id);
}

function scheduleDismiss(toast, delay = toast.remaining) {
  clearTimer(toast.id);
  if (!Number.isFinite(delay) || delay <= 0) {
    removeToast(toast.id);
    return;
  }
  toast.remaining = delay;
  toast.startedAt = Date.now();
  timers.set(toast.id, setTimeout(() => removeToast(toast.id), delay));
}

function showToast(message, { type = 'info', duration = 2800 } = {}) {
  const text = String(message ?? '').trim();
  if (!text) return null;

  const safeType = normalizeType(type);
  const existing = toasts.value.find(
    (toast) => toast.message === text && toast.type === safeType && Date.now() - toast.createdAt < DEDUPE_WINDOW_MS,
  );
  if (existing) {
    existing.createdAt = Date.now();
    existing.remaining = Math.max(900, Number(duration) || 2800);
    scheduleDismiss(existing);
    return existing.id;
  }

  const safeDuration = Math.max(1200, Number(duration) || 2800);
  const toast = {
    id: ++counter,
    message: text,
    type: safeType,
    duration: safeDuration,
    remaining: safeDuration,
    createdAt: Date.now(),
    startedAt: Date.now(),
    paused: false,
  };

  toasts.value = [...toasts.value, toast];
  scheduleDismiss(toast, safeDuration);

  while (toasts.value.length > MAX_TOASTS) {
    removeToast(toasts.value[0].id);
  }
  return toast.id;
}

function pauseToast(id) {
  const toast = toasts.value.find((item) => item.id === id);
  if (!toast || toast.paused) return;
  const elapsed = Date.now() - toast.startedAt;
  toast.remaining = Math.max(250, toast.remaining - elapsed);
  toast.paused = true;
  clearTimer(id);
}

function resumeToast(id) {
  const toast = toasts.value.find((item) => item.id === id);
  if (!toast || !toast.paused) return;
  toast.paused = false;
  scheduleDismiss(toast, toast.remaining);
}

function dismissToast(id) {
  removeToast(id);
}

export function useToast() {
  return {
    toasts,
    showToast,
    pauseToast,
    resumeToast,
    dismissToast,
  };
}
