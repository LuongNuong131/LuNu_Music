import { ref, watch } from 'vue';

const THEME_KEY = 'lunu-theme';
const readInitialTheme = () => {
  if (typeof window === 'undefined') return 'dark';
  const saved = window.localStorage.getItem(THEME_KEY);
  return saved === 'light' || saved === 'dark' ? saved : 'dark';
};

export const themeState = ref(readInitialTheme());

const applyTheme = (theme) => {
  if (typeof document === 'undefined') return;
  document.documentElement.dataset.theme = theme;
  document.documentElement.style.colorScheme = theme;
};

applyTheme(themeState.value);
watch(themeState, (theme) => {
  applyTheme(theme);
  if (typeof window !== 'undefined') window.localStorage.setItem(THEME_KEY, theme);
});

export const toggleTheme = () => {
  themeState.value = themeState.value === 'dark' ? 'light' : 'dark';
};

export const setTheme = (theme) => {
  if (theme === 'light' || theme === 'dark') themeState.value = theme;
};
