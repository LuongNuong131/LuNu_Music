import { reactive } from 'vue';

const state = reactive({
  visible: false,
  title: 'Xác nhận thao tác',
  message: '',
  mode: 'confirm',
  initialValue: '',
  placeholder: '',
  confirmLabel: 'Xác nhận',
  cancelLabel: 'Hủy',
  danger: false,
});

let resolver = null;

const close = (value) => {
  const resolve = resolver;
  resolver = null;
  state.visible = false;
  resolve?.(value);
};

const open = (options = {}) => {
  if (resolver) resolver(false);
  Object.assign(state, {
    visible: true,
    title: options.title || 'Xác nhận thao tác',
    message: options.message || '',
    mode: options.mode || 'confirm',
    initialValue: options.initialValue || '',
    placeholder: options.placeholder || '',
    confirmLabel: options.confirmLabel || 'Xác nhận',
    cancelLabel: options.cancelLabel || 'Hủy',
    danger: Boolean(options.danger),
  });
  return new Promise((resolve) => {
    resolver = resolve;
  });
};

const confirmDialog = (message, options = {}) => open({
  ...options,
  message,
  mode: 'confirm',
});

const promptDialog = (message, initialValue = '', options = {}) => open({
  ...options,
  message,
  initialValue,
  mode: 'prompt',
});

const confirm = (value = '') => close(state.mode === 'prompt' ? value : true);
const cancel = () => close(state.mode === 'prompt' ? null : false);

export function useDialog() {
  return { state, open, confirmDialog, promptDialog, confirm, cancel };
}
