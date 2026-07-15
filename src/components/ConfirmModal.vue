<!-- src/components/ConfirmModal.vue -->
<template>
  <Teleport to="body">
    <div v-if="visible" class="modal-overlay" @click.self="cancel">
      <div class="modal-card" role="dialog" aria-modal="true">
        <h3 class="modal-title">{{ title }}</h3>
        <p v-if="message" class="modal-message">{{ message }}</p>

        <input
          v-if="mode === 'prompt'"
          ref="inputRef"
          v-model="inputValue"
          type="text"
          class="modal-input"
          :placeholder="placeholder"
          @keyup.enter="confirm"
        />

        <div class="modal-actions">
          <button class="btn-ghost" @click="cancel">{{ cancelLabel }}</button>
          <button
            class="btn-solid"
            :class="{ danger }"
            @click="confirm"
          >{{ confirmLabel }}</button>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { ref, watch, nextTick } from 'vue';

const props = defineProps({
  visible: { type: Boolean, default: false },
  title: { type: String, default: '' },
  message: { type: String, default: '' },
  mode: { type: String, default: 'confirm' }, // 'confirm' | 'prompt'
  initialValue: { type: String, default: '' },
  placeholder: { type: String, default: '' },
  confirmLabel: { type: String, default: 'Xác nhận' },
  cancelLabel: { type: String, default: 'Huỷ' },
  danger: { type: Boolean, default: false }
});

const emit = defineEmits(['confirm', 'cancel']);
const inputValue = ref(props.initialValue);
const inputRef = ref(null);

watch(
  () => props.visible,
  async (isVisible) => {
    if (isVisible) {
      inputValue.value = props.initialValue;
      await nextTick();
      inputRef.value?.focus();
    }
  }
);

const confirm = () => {
  if (props.mode === 'prompt' && !inputValue.value.trim()) return;
  emit('confirm', inputValue.value.trim());
};

const cancel = () => emit('cancel');
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(5, 4, 3, 0.65);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 16px;
  z-index: 100;
}

.modal-card {
  width: 320px;
  max-width: 100%;
  background: linear-gradient(180deg, var(--panel-bg) 0%, #100d08 100%);
  border: 1px solid var(--hairline);
  border-radius: 14px;
  padding: 24px;
  box-shadow: 0 30px 80px rgba(0, 0, 0, 0.55);
}

.modal-title {
  font-family: var(--font-display);
  font-size: 22px;
  font-weight: 400;
  letter-spacing: 0.3px;
  color: var(--text-main);
  margin-bottom: 8px;
}

.modal-message {
  font-size: 13px;
  color: var(--text-sub);
  margin-bottom: 14px;
  line-height: 1.5;
}

.modal-input {
  width: 100%;
  padding: 10px 12px;
  border-radius: 8px;
  border: 1px solid var(--hairline-soft);
  background: rgba(255, 255, 255, 0.03);
  color: var(--text-main);
  font-family: var(--font-body);
  font-size: 14px;
  margin-bottom: 18px;
}

.modal-input:focus {
  outline: none;
  border-color: var(--gold-dim);
  background: rgba(232, 184, 109, 0.05);
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}

.btn-ghost, .btn-solid {
  padding: 9px 16px;
  border-radius: 8px;
  border: none;
  font-size: 13px;
  font-weight: 700;
  cursor: pointer;
  transition: transform 0.15s ease, opacity 0.15s ease;
}

.btn-ghost {
  background: transparent;
  color: var(--text-sub);
  border: 1px solid var(--hairline-soft);
}

.btn-ghost:hover {
  color: var(--text-main);
}

.btn-solid {
  background: linear-gradient(135deg, var(--gold-bright), var(--gold));
  color: #100d08;
}

.btn-solid:hover {
  transform: translateY(-1px);
}

.btn-solid.danger {
  background: linear-gradient(135deg, #cf5b5b, var(--crimson));
  color: #1a0d0d;
}
</style>