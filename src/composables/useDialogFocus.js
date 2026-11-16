import { nextTick, onBeforeUnmount, watch } from 'vue';
const dialogs = [];
export function useDialogFocus(visible, element, close) {
  const key = Symbol('dialog');
  let previousFocus;
  const remove = () => {
    const index = dialogs.indexOf(key);
    if (index >= 0) dialogs.splice(index, 1);
    document.removeEventListener('keydown', onKeydown, true);
  };
  const onKeydown = (event) => {
    if (dialogs.at(-1) !== key) return;
    if (event.key === 'Escape') {
      event.preventDefault();
      event.stopPropagation();
      close();
      return;
    }
    if (event.key !== 'Tab') return;
    const controls = [
      ...(element.value?.querySelectorAll(
        'button:not(:disabled),a[href],input:not(:disabled),select,textarea,[tabindex="0"]',
      ) || []),
    ].filter((control) => control.getClientRects().length);
    const first = controls[0],
      last = controls.at(-1);
    if (!first) {
      event.preventDefault();
      element.value?.focus();
      return;
    }
    if (
      event.shiftKey &&
      (document.activeElement === first || !element.value?.contains(document.activeElement))
    ) {
      event.preventDefault();
      last.focus();
    } else if (
      !event.shiftKey &&
      (document.activeElement === last || !element.value?.contains(document.activeElement))
    ) {
      event.preventDefault();
      first.focus();
    }
  };
  watch(visible, async (open) => {
    if (open) {
      previousFocus = document.activeElement;
      await nextTick();
      if (!visible.value) return;
      remove();
      dialogs.push(key);
      document.addEventListener('keydown', onKeydown, true);
      element.value?.focus();
    } else {
      remove();
      if (previousFocus?.isConnected) previousFocus.focus();
    }
  });
  onBeforeUnmount(remove);
}
