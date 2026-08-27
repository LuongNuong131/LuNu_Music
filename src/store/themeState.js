import { reactive, ref, watch } from 'vue';

const THEME_KEY = 'lunu-theme';
const DEFAULT_AURORA = {
  primary: '245, 185, 122',
  secondary: '155, 140, 255',
  accent: '130, 229, 195',
  glow: '245, 185, 122',
};

const readInitialTheme = () => {
  if (typeof window === 'undefined') return 'dark';
  const saved = window.localStorage.getItem(THEME_KEY);
  return saved === 'light' || saved === 'dark' ? saved : 'dark';
};

export const themeState = ref(readInitialTheme());
export const auroraState = reactive({ ...DEFAULT_AURORA, source: 'default' });
let extractionToken = 0;

const rgba = (rgb, alpha) => `rgba(${rgb}, ${alpha})`;

const applyAurora = () => {
  if (typeof document === 'undefined') return;
  const root = document.documentElement;
  root.style.setProperty('--aurora-primary', rgba(auroraState.primary, 1));
  root.style.setProperty('--aurora-secondary', rgba(auroraState.secondary, 1));
  root.style.setProperty('--aurora-accent', rgba(auroraState.accent, 1));
  root.style.setProperty('--aurora-glow', rgba(auroraState.glow, 1));
  root.style.setProperty('--aurora-mesh-one', rgba(auroraState.primary, 0.24));
  root.style.setProperty('--aurora-mesh-two', rgba(auroraState.secondary, 0.18));
  root.style.setProperty('--aurora-mesh-three', rgba(auroraState.accent, 0.13));
  root.style.setProperty('--glass-bg', themeState.value === 'dark' ? 'rgba(13, 16, 25, 0.62)' : 'rgba(255, 252, 246, 0.68)');
};

const applyTheme = (theme) => {
  if (typeof document === 'undefined') return;
  document.documentElement.dataset.theme = theme;
  document.documentElement.style.colorScheme = theme;
  applyAurora();
};

const luminance = ([r, g, b]) => (0.2126 * r + 0.7152 * g + 0.0722 * b) / 255;
const rgbString = ([r, g, b]) => `${r}, ${g}, ${b}`;
const clamp = (value) => Math.max(0, Math.min(255, Math.round(value)));
const shift = (rgb, amount) => rgb.map((channel) => clamp(channel + amount));

const extractDominantColors = (source) => new Promise((resolve) => {
  if (typeof window === 'undefined' || typeof Image === 'undefined' || !source) {
    resolve(null);
    return;
  }
  const image = new Image();
  image.crossOrigin = 'anonymous';
  image.onload = () => {
    try {
      const canvas = document.createElement('canvas');
      const size = 24;
      canvas.width = size;
      canvas.height = size;
      const context = canvas.getContext('2d', { willReadFrequently: true });
      if (!context) return resolve(null);
      context.drawImage(image, 0, 0, size, size);
      const pixels = context.getImageData(0, 0, size, size).data;
      const buckets = new Map();
      for (let index = 0; index < pixels.length; index += 16) {
        const alpha = pixels[index + 3];
        if (alpha < 170) continue;
        const color = [pixels[index], pixels[index + 1], pixels[index + 2]];
        const key = color.map((channel) => Math.round(channel / 24) * 24).join(',');
        const weight = 1 + Math.max(0, 0.62 - luminance(color));
        buckets.set(key, (buckets.get(key) || 0) + weight);
      }
      const ranked = [...buckets.entries()].sort((a, b) => b[1] - a[1]).slice(0, 4).map(([key]) => key.split(',').map(Number));
      if (!ranked.length) return resolve(null);
      const primary = ranked[0];
      const secondary = ranked[1] || shift(primary, 38);
      const accent = ranked[2] || shift(primary, 66);
      resolve({ primary: rgbString(primary), secondary: rgbString(secondary), accent: rgbString(accent), glow: rgbString(shift(primary, 18)) });
    } catch {
      resolve(null);
    }
  };
  image.onerror = () => resolve(null);
  image.src = source;
});

applyTheme(themeState.value);
watch(themeState, (theme) => {
  applyTheme(theme);
  if (typeof window !== 'undefined') window.localStorage.setItem(THEME_KEY, theme);
});

watch(auroraState, applyAurora, { deep: true });

export const setAuroraFromCover = async (source) => {
  const token = ++extractionToken;
  const palette = await extractDominantColors(source);
  if (token !== extractionToken) return;
  Object.assign(auroraState, palette || { ...DEFAULT_AURORA, source: 'fallback' });
  auroraState.source = palette ? 'cover' : 'fallback';
  applyAurora();
};

export const resetAurora = () => {
  extractionToken += 1;
  Object.assign(auroraState, { ...DEFAULT_AURORA, source: 'default' });
  applyAurora();
};

export const toggleTheme = () => {
  themeState.value = themeState.value === 'dark' ? 'light' : 'dark';
};

export const setTheme = (theme) => {
  if (theme === 'light' || theme === 'dark') themeState.value = theme;
};
