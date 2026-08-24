// src/composables/useToast.js
// Hệ thống toast nhỏ gọn, singleton giống usePlaylists.js — không cần thêm thư viện ngoài.

import { ref } from 'vue';

const toasts = ref([]);
let counter = 0;

function showToast(message, { type = 'info', duration = 2800 } = {}) {
  const id = ++counter;
  toasts.value.push({ id, message, type });
  setTimeout(() => dismissToast(id), duration);
  return id;
}

function dismissToast(id) {
  toasts.value = toasts.value.filter((t) => t.id !== id);
}

export function useToast() {
  return { toasts, showToast, dismissToast };
}