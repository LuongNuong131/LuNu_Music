import { reactive, computed } from 'vue';

const QUEUE_KEY = 'lunu_player_queue_v2';
const SETTINGS_KEY = 'lunu_player_settings_v2';

const readJson = (key, fallback) => {
  try {
    const value = JSON.parse(localStorage.getItem(key));
    return value ?? fallback;
  } catch (error) {
    console.warn(`[LuNu] Không thể đọc ${key}:`, error);
    localStorage.removeItem(key);
    return fallback;
  }
};

const settings = readJson(SETTINGS_KEY, {});
const savedQueue = readJson(QUEUE_KEY, { queue: [], originalQueue: [] });

export const playerState = reactive({
  currentSong: null,
  currentIndex: -1,
  queue: Array.isArray(savedQueue.queue) ? savedQueue.queue : [],
  originalQueue: Array.isArray(savedQueue.originalQueue) ? savedQueue.originalQueue : [],
  isPlaying: false,
  currentTime: 0,
  duration: 0,
  volume: Number.isFinite(settings.volume) ? settings.volume : 0.82,
  muted: Boolean(settings.muted),
  shuffle: Boolean(settings.shuffle),
  repeatMode: settings.repeatMode || 'off',
  playbackRate: Number.isFinite(settings.playbackRate) ? settings.playbackRate : 1,
  isLoading: false,
  isBuffering: false,
  error: '',
  queueVisible: false,
  nowPlayingVisible: false,
});

let audioElement = null;
let shouldAutoplay = false;
// Navigation history is separate from the upcoming queue so Back returns to the
// exact song that was just played, including shuffled/scoped collections.
let backHistory = [];
let forwardHistory = [];

const persistSettings = () => {
  localStorage.setItem(SETTINGS_KEY, JSON.stringify({
    volume: playerState.volume,
    muted: playerState.muted,
    shuffle: playerState.shuffle,
    repeatMode: playerState.repeatMode,
    playbackRate: playerState.playbackRate,
  }));
};

const persistQueue = () => {
  localStorage.setItem(QUEUE_KEY, JSON.stringify({
    queue: playerState.queue,
    originalQueue: playerState.originalQueue,
  }));
};

const setMediaError = (error, fallback = 'Không thể phát bài hát này.') => {
  playerState.error = error?.message || fallback;
  playerState.isPlaying = false;
  playerState.isLoading = false;
};

const playAudio = async () => {
  if (!audioElement || !playerState.currentSong) return false;
  playerState.error = '';
  playerState.isLoading = true;
  try {
    await audioElement.play();
    playerState.isPlaying = true;
    playerState.isLoading = false;
    return true;
  } catch (error) {
    setMediaError(error, 'Trình duyệt cần một thao tác tương tác để bắt đầu phát nhạc.');
    return false;
  }
};

const getIndex = (list, song) => list.findIndex((item) => String(item?.id) === String(song?.id));

export const setAudioElement = (element) => {
  audioElement = element;
  if (!audioElement) return;
  audioElement.volume = playerState.volume;
  audioElement.muted = playerState.muted;
  audioElement.playbackRate = playerState.playbackRate;
};

const activateSong = (song, autoplay = true) => {
  if (!song) return;
  playerState.currentSong = song;
  playerState.currentTime = 0;
  playerState.duration = 0;
  playerState.error = '';
  shouldAutoplay = autoplay;
  if (audioElement && shouldAutoplay) window.setTimeout(() => playAudio(), 0);
};

export const playSong = (song, source = [], options = {}) => {
  if (!song) return;
  const requestedCollection = Array.isArray(source) && source.length ? source : playerState.originalQueue;
  const collection = requestedCollection.some((item) => String(item?.id) === String(song.id)) ? requestedCollection : [song, ...requestedCollection];
  const shouldReplaceQueue = options.replaceQueue !== false && Array.isArray(source) && source.length;
  if (shouldReplaceQueue) {
    playerState.originalQueue = [...collection];
    const index = getIndex(collection, song);
    playerState.currentIndex = index >= 0 ? index : 0;
    playerState.queue = collection.filter((item) => String(item.id) !== String(song.id));
    if (playerState.shuffle) playerState.queue.sort(() => Math.random() - 0.5);
    persistQueue();
  } else {
    playerState.currentIndex = getIndex(playerState.originalQueue, song);
  }
  backHistory = [];
  forwardHistory = [];
  activateSong(song, options.autoplay !== false);
};

export const play = () => playAudio();

export const pause = () => {
  audioElement?.pause();
  playerState.isPlaying = false;
};

export const togglePlay = () => {
  if (!playerState.currentSong) return;
  if (playerState.isPlaying) pause();
  else playAudio();
};

export const seek = (time) => {
  const nextTime = Math.max(0, Math.min(Number(time) || 0, playerState.duration || Infinity));
  playerState.currentTime = nextTime;
  if (audioElement) audioElement.currentTime = nextTime;
};

export const setVolume = (value) => {
  const nextVolume = Math.max(0, Math.min(1, Number(value) || 0));
  playerState.volume = nextVolume;
  playerState.muted = nextVolume === 0;
  if (audioElement) {
    audioElement.volume = nextVolume;
    audioElement.muted = playerState.muted;
  }
  persistSettings();
};

export const toggleMute = () => {
  playerState.muted = !playerState.muted;
  if (audioElement) audioElement.muted = playerState.muted;
  persistSettings();
};

export const setPlaybackRate = (rate) => {
  playerState.playbackRate = Number(rate) || 1;
  if (audioElement) audioElement.playbackRate = playerState.playbackRate;
  persistSettings();
};

export const toggleShuffle = () => {
  playerState.shuffle = !playerState.shuffle;
  if (playerState.shuffle) playerState.queue.sort(() => Math.random() - 0.5);
  else if (playerState.currentSong) {
    const current = playerState.currentSong;
    playerState.queue = playerState.originalQueue.filter((item) => String(item.id) !== String(current.id));
  }
  persistSettings();
  persistQueue();
};

export const toggleRepeat = () => {
  const modes = ['off', 'all', 'one'];
  playerState.repeatMode = modes[(modes.indexOf(playerState.repeatMode) + 1) % modes.length];
  persistSettings();
};

export const addToQueue = (song) => {
  if (!song || String(song.id) === String(playerState.currentSong?.id)) return;
  if (!playerState.queue.some((item) => String(item.id) === String(song.id))) {
    playerState.queue.push(song);
    if (!playerState.originalQueue.some((item) => String(item.id) === String(song.id))) playerState.originalQueue.push(song);
    persistQueue();
  }
};

export const playNext = (song) => {
  if (!song) return;
  playerState.queue = playerState.queue.filter((item) => String(item.id) !== String(song.id));
  playerState.queue.unshift(song);
  persistQueue();
};

export const removeFromQueue = (index) => {
  if (index < 0 || index >= playerState.queue.length) return;
  playerState.queue.splice(index, 1);
  persistQueue();
};

export const clearQueue = () => {
  playerState.queue.splice(0, playerState.queue.length);
  persistQueue();
};

export const next = () => {
  if (!playerState.currentSong) return;
  if (playerState.repeatMode === 'one') {
    seek(0);
    playAudio();
    return;
  }
  if (forwardHistory.length) {
    const currentSong = playerState.currentSong;
    const nextSong = forwardHistory.shift();
    if (currentSong) backHistory.push(currentSong);
    playerState.currentIndex = getIndex(playerState.originalQueue, nextSong);
    activateSong(nextSong, true);
    return;
  }
  if (playerState.queue.length) {
    const currentSong = playerState.currentSong;
    const nextSong = playerState.queue.shift();
    if (currentSong) backHistory.push(currentSong);
    playerState.currentIndex = getIndex(playerState.originalQueue, nextSong);
    activateSong(nextSong, true);
    persistQueue();
    return;
  }
  if (playerState.repeatMode === 'all' && playerState.originalQueue.length > 1) {
    const currentId = playerState.currentSong.id;
    const rebuilt = playerState.originalQueue.filter((item) => String(item.id) !== String(currentId));
    playerState.queue = playerState.shuffle ? rebuilt.sort(() => Math.random() - 0.5) : rebuilt;
    next();
    return;
  }
  playerState.isPlaying = false;
  shouldAutoplay = false;
};

export const previous = () => {
  if (!playerState.currentSong) return;
  if (playerState.currentTime > 3) {
    seek(0);
    return;
  }
  if (backHistory.length) {
    const currentSong = playerState.currentSong;
    const previousSong = backHistory.pop();
    if (currentSong) forwardHistory.unshift(currentSong);
    playerState.currentIndex = getIndex(playerState.originalQueue, previousSong);
    activateSong(previousSong, true);
    return;
  }
  const list = playerState.originalQueue.length ? playerState.originalQueue : [playerState.currentSong];
  const index = getIndex(list, playerState.currentSong);
  const previousSong = list[index > 0 ? index - 1 : list.length - 1];
  if (previousSong && String(previousSong.id) !== String(playerState.currentSong.id)) {
    forwardHistory.unshift(playerState.currentSong);
    playerState.currentIndex = getIndex(list, previousSong);
    activateSong(previousSong, true);
  }
};

export const handleAudioLoaded = (duration) => {
  playerState.duration = Number.isFinite(duration) ? duration : 0;
  playerState.isLoading = false;
  if (shouldAutoplay) playAudio();
};

export const handleAudioTimeUpdate = (time) => { playerState.currentTime = time; };
export const handleAudioWaiting = () => { playerState.isBuffering = true; };
export const handleAudioCanPlay = () => { playerState.isBuffering = false; playerState.isLoading = false; };
export const handleAudioError = (error) => setMediaError(error, 'File nhạc không khả dụng hoặc đã bị xoá.');
export const handleAudioEnded = () => next();

export const usePlayer = () => ({
  state: playerState,
  currentSong: computed(() => playerState.currentSong),
  isPlaying: computed(() => playerState.isPlaying),
  playSong,
  play,
  pause,
  togglePlay,
  seek,
  setVolume,
  toggleMute,
  setPlaybackRate,
  toggleShuffle,
  toggleRepeat,
  addToQueue,
  playNext,
  removeFromQueue,
  clearQueue,
  next,
  previous,
});

export const shouldPlayerAutoplay = () => shouldAutoplay;
