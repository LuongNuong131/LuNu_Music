<!-- src/components/CommandPalette.vue -->
<template>
  <Teleport to="body">
    <Transition name="cmd-fade">
      <div v-if="visible" class="cmd-overlay" @click.self="emit('close')">
        <div class="cmd-box" role="dialog" aria-modal="true">
          <div class="cmd-input-row">
            <span class="cmd-search-icon">⌕</span>
            <input
              ref="inputRef"
              v-model="query"
              type="text"
              class="cmd-input"
              placeholder="Tìm bài hát, playlist, hoặc gõ lệnh..."
              @keydown="onKeydown"
            />
            <span class="cmd-kbd">Esc</span>
          </div>

          <div class="cmd-results" v-if="results.length">
            <button
              v-for="(item, i) in results"
              :key="item.key"
              class="cmd-item"
              :class="{ active: i === activeIndex }"
              @mouseenter="activeIndex = i"
              @click="select(item)"
            >
              <span class="cmd-item-icon" :class="item.type">{{ iconFor(item) }}</span>
              <span class="cmd-item-main">
                <span class="cmd-item-title">{{ item.title }}</span>
                <span v-if="item.subtitle" class="cmd-item-sub">{{ item.subtitle }}</span>
              </span>
              <span class="cmd-item-tag">{{ tagFor(item) }}</span>
            </button>
          </div>

          <div class="cmd-empty" v-else>
            <p>Không tìm thấy gì cho "{{ query }}"</p>
          </div>

          <div class="cmd-footer">
            <span><span class="cmd-kbd small">↑↓</span> chọn</span>
            <span><span class="cmd-kbd small">Enter</span> thực hiện</span>
            <span><span class="cmd-kbd small">Ctrl K</span> mở/đóng</span>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { ref, computed, watch, nextTick } from 'vue';

const props = defineProps({
  visible: { type: Boolean, default: false },
  songs: { type: Array, default: () => [] },
  playlists: { type: Array, default: () => [] }
});

const emit = defineEmits(['close', 'play-song', 'open-playlist', 'action']);

const query = ref('');
const activeIndex = ref(0);
const inputRef = ref(null);

const normalize = (str) =>
  (str || '')
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .replace(/đ/gi, 'd')
    .toLowerCase();

const quickActions = [
  { key: 'act-home', type: 'action', title: 'Về Trang chủ', action: 'home' },
  { key: 'act-search', type: 'action', title: 'Mở Tìm kiếm', action: 'search' },
  { key: 'act-shuffle', type: 'action', title: 'Bật/tắt Shuffle', action: 'toggle-shuffle' },
  { key: 'act-queue', type: 'action', title: 'Mở Hàng đợi phát', action: 'toggle-queue' }
];

const results = computed(() => {
  const q = normalize(query.value.trim());

  const songItems = props.songs
    .filter((s) => !q || normalize(s.title).includes(q) || normalize(s.artist).includes(q))
    .slice(0, 6)
    .map((s) => ({ key: `song-${s.id}`, type: 'song', title: s.title, subtitle: s.artist, song: s }));

  const playlistItems = props.playlists
    .filter((p) => !q || normalize(p.name).includes(q))
    .slice(0, 4)
    .map((p) => ({ key: `pl-${p.id}`, type: 'playlist', title: p.name, subtitle: `${p.songIds.length} bài hát`, playlist: p }));

  const actionItems = !q
    ? quickActions
    : quickActions.filter((a) => normalize(a.title).includes(q));

  return [...songItems, ...playlistItems, ...actionItems];
});

watch(results, () => { activeIndex.value = 0; });

watch(() => props.visible, async (v) => {
  if (v) {
    query.value = '';
    activeIndex.value = 0;
    await nextTick();
    inputRef.value?.focus();
  }
});

const iconFor = (item) => {
  if (item.type === 'song') return '♪';
  if (item.type === 'playlist') return '▤';
  return '⌘';
};

const tagFor = (item) => {
  if (item.type === 'song') return 'Phát';
  if (item.type === 'playlist') return 'Mở';
  return 'Lệnh';
};

const select = (item) => {
  if (item.type === 'song') emit('play-song', item.song);
  else if (item.type === 'playlist') emit('open-playlist', item.playlist);
  else emit('action', item.action);
  emit('close');
};

const onKeydown = (e) => {
  if (e.key === 'ArrowDown') {
    e.preventDefault();
    activeIndex.value = Math.min(activeIndex.value + 1, results.value.length - 1);
  } else if (e.key === 'ArrowUp') {
    e.preventDefault();
    activeIndex.value = Math.max(activeIndex.value - 1, 0);
  } else if (e.key === 'Enter') {
    e.preventDefault();
    const item = results.value[activeIndex.value];
    if (item) select(item);
  } else if (e.key === 'Escape') {
    emit('close');
  }
};
</script>

<style scoped>
.cmd-overlay {
  position: fixed;
  inset: 0;
  z-index: 180;
  background: rgba(5, 4, 3, 0.55);
  display: flex;
  justify-content: center;
  padding-top: 14vh;
}

.cmd-box {
  width: 560px;
  max-width: 92vw;
  max-height: 60vh;
  display: flex;
  flex-direction: column;
  background: linear-gradient(180deg, var(--panel-bg) 0%, #100d08 100%);
  border: 1px solid var(--hairline);
  border-radius: 14px;
  box-shadow: 0 30px 80px rgba(0, 0, 0, 0.6);
  overflow: hidden;
  height: fit-content;
}

.cmd-input-row {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 16px 18px;
  border-bottom: 1px solid var(--hairline-soft);
  flex-shrink: 0;
}

.cmd-search-icon {
  color: var(--gold-dim);
  font-size: 16px;
}

.cmd-input {
  flex: 1;
  border: none;
  background: none;
  outline: none;
  color: var(--text-main);
  font-family: var(--font-body);
  font-size: 15px;
}

.cmd-input::placeholder {
  color: var(--text-faint);
}

.cmd-kbd {
  font-family: var(--font-mono);
  font-size: 10px;
  color: var(--text-faint);
  border: 1px solid var(--hairline);
  border-radius: 5px;
  padding: 3px 6px;
}

.cmd-results {
  overflow-y: auto;
  padding: 8px;
}

.cmd-item {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 12px;
  background: none;
  border: none;
  text-align: left;
  padding: 9px 10px;
  border-radius: 9px;
  cursor: pointer;
}

.cmd-item.active {
  background: rgba(232, 184, 109, 0.1);
}

.cmd-item-icon {
  width: 26px;
  height: 26px;
  border-radius: 7px;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  background: rgba(255, 255, 255, 0.05);
  color: var(--text-sub);
}

.cmd-item-icon.song { color: var(--gold); }
.cmd-item-icon.playlist { color: var(--gold-bright); }
.cmd-item-icon.action { color: var(--text-sub); }

.cmd-item-main {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
}

.cmd-item-title {
  font-size: 13.5px;
  font-weight: 600;
  color: var(--text-main);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.cmd-item-sub {
  font-size: 11.5px;
  color: var(--text-faint);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.cmd-item-tag {
  font-family: var(--font-mono);
  font-size: 9.5px;
  letter-spacing: 0.5px;
  text-transform: uppercase;
  color: var(--text-faint);
  flex-shrink: 0;
}

.cmd-empty {
  padding: 30px 18px;
  text-align: center;
  color: var(--text-faint);
  font-size: 13px;
}

.cmd-footer {
  display: flex;
  gap: 16px;
  padding: 10px 16px;
  border-top: 1px solid var(--hairline-soft);
  font-size: 11px;
  color: var(--text-faint);
  flex-shrink: 0;
}

.cmd-kbd.small {
  font-size: 9px;
  padding: 2px 5px;
  margin-right: 4px;
}

.cmd-fade-enter-active, .cmd-fade-leave-active {
  transition: opacity 0.18s ease;
}
.cmd-fade-enter-from, .cmd-fade-leave-to {
  opacity: 0;
}
.cmd-fade-enter-active .cmd-box, .cmd-fade-leave-active .cmd-box {
  transition: transform 0.18s ease;
}
.cmd-fade-enter-from .cmd-box, .cmd-fade-leave-to .cmd-box {
  transform: translateY(-10px) scale(0.98);
}
</style>