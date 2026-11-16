<template>
  <div class="import-console">
    <div class="source-choices" role="group" aria-label="Chọn nguồn nhạc">
      <button
        :class="{ active: source === 'direct' }"
        :aria-pressed="source === 'direct'"
        :disabled="isImporting"
        @click="changeSource('direct')"
      >
        <Music2 :size="17" /> Nguồn audio trực tiếp</button
      ><button
        :class="{ active: source === 'youtube' }"
        :aria-pressed="source === 'youtube'"
        :disabled="isImporting"
        @click="changeSource('youtube')"
      >
        <SquarePlay :size="18" /> YouTube
      </button>
    </div>
    <p class="source-hint">
      {{
        source === 'youtube'
          ? 'Tìm bằng tên bài hát và nghệ sĩ. Chỉ thêm nội dung bạn có quyền sử dụng.'
          : 'Tìm nhạc cho phép tải từ Internet Archive và Jamendo.'
      }}
    </p>
    <form class="search-wrapper" @submit.prevent="handleSearch">
      <label class="search-field"
        ><Search :size="18" /><input
          v-model.trim="searchQuery"
          type="search"
          :placeholder="
            source === 'youtube' ? 'Tìm tên bài hát trên YouTube...' : 'Tìm bài hát hoặc nghệ sĩ...'
          "
          aria-label="Tìm nguồn nhạc"
          :disabled="isSearching || isImporting"
          minlength="2"
          required /></label
      ><button :disabled="isSearching || isImporting || searchQuery.length < 2" class="action-btn">
        <LoaderCircle v-if="isSearching" :size="16" />{{ isSearching ? 'Đang tìm...' : 'Tìm kiếm' }}
      </button>
    </form>
    <p v-if="message" class="status-message" :class="messageType" role="status">{{ message }}</p>
    <div v-if="selectedVideo" class="selected-panel">
      <header>
        <h3>Thông tin bài hát</h3>
        <button
          class="close-btn"
          :disabled="isImporting"
          @click="clearSelection"
          aria-label="Bỏ chọn nguồn"
        >
          <X :size="18" />
        </button>
      </header>
      <div class="selected-video">
        <img :src="thumbnail(selectedVideo)" :alt="selectedVideo.title" />
        <div>
          <strong>{{ selectedVideo.title }}</strong><span>{{
            selectedVideo.artist || selectedVideo.uploader
          }}</span
          ><small>{{
            selectedVideo.provider === 'youtube'
              ? 'YouTube'
              : selectedVideo.provider === 'jamendo'
                ? 'Jamendo'
                : 'Internet Archive'
          }}</small>
        </div>
      </div>
      <form class="metadata-form" @submit.prevent="handleImport">
        <label
          ><span>Tên bài hát</span
          ><input
            v-model.trim="metadata.title"
            required
            maxlength="240"
            :disabled="isImporting" /></label
        ><label
          ><span>Nghệ sĩ</span
          ><input v-model.trim="metadata.artist" required maxlength="160" :disabled="isImporting"
        /></label>
        <div class="form-actions">
          <button type="button" class="cancel-btn" :disabled="isImporting" @click="clearSelection">
            Chọn bài khác</button
          ><button
            class="action-btn"
            :disabled="isImporting || !metadata.title || !metadata.artist"
          >
            <Download :size="16" />{{ isImporting ? importLabel : 'Thêm vào thư viện' }}
          </button>
        </div>
      </form>
    </div>
    <div v-else-if="searchResults.length" class="results-list">
      <article
        v-for="video in searchResults"
        :key="`${video.provider}:${video.source_id}`"
        class="result-item"
      >
        <img :src="thumbnail(video)" :alt="video.title" loading="lazy" />
        <div>
          <h4>{{ video.title }}</h4>
          <p>{{ video.artist || video.uploader || 'Chưa rõ nghệ sĩ' }}</p>
          <small>{{ video.provider }}</small>
        </div>
        <button class="select-btn" @click="selectVideo(video)">Chọn <Plus :size="15" /></button>
      </article>
    </div>
  </div>
</template>
<script setup>
import { onBeforeUnmount, reactive, ref } from 'vue';
import { Download, LoaderCircle, Music2, Plus, Search, X, SquarePlay } from '@lucide/vue';
import { addSong, searchAudioSources } from '../services/api';
import { waitForImport } from '../utils/importJob';
import { songArtwork } from '../utils/artwork';
const emit = defineEmits(['song-added']);
const source = ref('direct'),
  searchQuery = ref(''),
  searchResults = ref([]),
  selectedVideo = ref(null),
  isSearching = ref(false),
  isImporting = ref(false),
  message = ref(''),
  messageType = ref(''),
  importLabel = ref('Đang xử lý...');
const metadata = reactive({ title: '', artist: '', cover: '', lyrics: '' });
let controller = null;
const thumbnail = (video) => songArtwork({ ...video, cover: video.cover || video.thumbnail });
const clearSelection = () => {
  selectedVideo.value = null;
  Object.assign(metadata, { title: '', artist: '', cover: '', lyrics: '' });
};
const changeSource = (value) => {
  source.value = value;
  searchResults.value = [];
  clearSelection();
  message.value = '';
};
const selectVideo = (video) => {
  selectedVideo.value = video;
  Object.assign(metadata, {
    title: video.title || '',
    artist: video.artist || video.uploader || '',
    cover: video.cover || video.thumbnail || '',
    lyrics: '',
  });
  message.value = '';
};
const handleSearch = async () => {
  if (searchQuery.value.length < 2 || isSearching.value) return;
  isSearching.value = true;
  message.value = '';
  searchResults.value = [];
  clearSelection();
  try {
    const response = await searchAudioSources(searchQuery.value, source.value);
    if (!response.success)
      throw new Error(
        response.message || 'Chưa có kết quả. Thử tên bài hát và nghệ sĩ cụ thể hơn.',
      );
    searchResults.value = response.results;
    message.value = `${searchResults.value.length} kết quả. Chọn bài để kiểm tra thông tin.`;
    messageType.value = '';
  } catch (error) {
    message.value = error.message;
    messageType.value = 'error';
  } finally {
    isSearching.value = false;
  }
};
const handleImport = async () => {
  if (!selectedVideo.value || isImporting.value) return;
  isImporting.value = true;
  messageType.value = '';
  importLabel.value = 'Đang xếp hàng...';
  controller = new AbortController();
  try {
    const response = await addSong({
      sourceId: selectedVideo.value.source_id,
      provider: selectedVideo.value.provider,
      ...metadata,
    });
    if (!response.success || !response.job_id)
      throw new Error(response.message || 'Chưa thể bắt đầu thêm nhạc.');
    const job = await waitForImport(response.job_id, {
      signal: controller.signal,
      onProgress: (job) => {
        message.value = job.message || 'Đang xử lý bài hát...';
        importLabel.value = 'Đang thêm nhạc...';
      },
    });
    message.value = `Đã thêm “${job.song?.title || metadata.title}” vào thư viện.`;
    messageType.value = 'success';
    emit('song-added', job.song);
    clearSelection();
    searchResults.value = [];
  } catch (error) {
    if (error.name !== 'AbortError') {
      message.value = error.message;
      messageType.value = 'error';
    }
  } finally {
    isImporting.value = false;
  }
};
onBeforeUnmount(() => controller?.abort());
</script>
<style scoped>
.import-console {
  display: grid;
  gap: 15px;
  padding: 20px;
  border: 1px solid var(--hairline);
  border-radius: 14px;
  background: var(--surface-2);
}
.source-choices {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}
.source-choices button {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 12px;
  border: 1px solid var(--hairline);
  border-radius: 9px;
  background: none;
  color: var(--text-sub);
  font-size: 11px;
}
.source-choices button.active {
  background: var(--accent-soft);
  color: var(--gold);
  border-color: var(--gold);
}
.source-hint {
  font-size: 11px;
  color: var(--text-sub);
  line-height: 1.8;
}
.search-wrapper {
  display: flex;
  gap: 10px;
}
.search-field {
  display: flex;
  align-items: center;
  flex: 1;
  min-width: 0;
  gap: 9px;
  border: 1px solid var(--hairline);
  border-radius: 10px;
  padding: 11px 13px;
  color: var(--text-faint);
}
.search-field:focus-within {
  border-color: var(--gold);
}
.search-field input {
  width: 100%;
  min-width: 0;
  border: 0;
  outline: none;
  background: none;
  color: var(--text-main);
  font-size: 12px;
}
.action-btn,
.select-btn,
.cancel-btn {
  display: inline-flex;
  justify-content: center;
  align-items: center;
  gap: 8px;
  min-height: 41px;
  padding: 10px 14px;
  border: 1px solid var(--hairline);
  border-radius: 9px;
  font-size: 11px;
  background: var(--accent-soft);
  color: var(--gold);
}
.action-btn {
  background: var(--gold);
  color: var(--brand-ink);
  border: 0;
  font-weight: 600;
}
.status-message {
  font-size: 11px;
  line-height: 1.8;
  color: var(--text-sub);
  overflow-wrap: anywhere;
}
.status-message.error {
  color: var(--crimson);
}
.status-message.success {
  color: var(--mint);
}
.selected-panel {
  padding: 17px;
  border: 1px solid var(--hairline);
  border-radius: 10px;
}
.selected-panel header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.selected-panel h3 {
  font-size: 14px;
  font-weight: 500;
}
.close-btn {
  display: grid;
  place-items: center;
  width: 36px;
  height: 36px;
  border: 0;
  background: none;
  color: var(--text-sub);
}
.selected-video {
  display: flex;
  align-items: center;
  gap: 12px;
  margin: 14px 0 22px;
  min-width: 0;
}
.selected-video img {
  width: 75px;
  height: 75px;
  object-fit: cover;
  border-radius: 9px;
}
.selected-video > div {
  display: grid;
  gap: 6px;
  min-width: 0;
}
.selected-video strong {
  font-size: 12px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.selected-video span,
.selected-video small {
  color: var(--text-sub);
  font-size: 10px;
}
.metadata-form {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 14px;
}
.metadata-form label {
  display: grid;
  gap: 9px;
  font-size: 11px;
  color: var(--text-sub);
}
.metadata-form input {
  width: 100%;
  min-width: 0;
  padding: 12px;
  border: 1px solid var(--hairline);
  border-radius: 9px;
  background: var(--glass);
  color: var(--text-main);
}
.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: 9px;
  grid-column: 1/-1;
  flex-wrap: wrap;
}
.results-list {
  display: grid;
  gap: 9px;
  max-height: 440px;
  overflow: auto;
}
.result-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 9px;
  border: 1px solid var(--hairline-soft);
  border-radius: 9px;
}
.result-item img {
  width: 58px;
  height: 58px;
  object-fit: cover;
  border-radius: 7px;
}
.result-item > div {
  flex: 1;
  min-width: 0;
}
.result-item h4 {
  font-size: 12px;
  font-weight: 500;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.result-item p,
.result-item small {
  margin-top: 5px;
  color: var(--text-sub);
  font-size: 10px;
}
.result-item small {
  font-size: 9px;
}
@media (max-width: 600px) {
  .import-console {
    padding: 13px;
  }
  .search-wrapper {
    flex-direction: column;
  }
  .search-field input,
  .metadata-form input {
    font-size: 16px;
  }
  .metadata-form {
    grid-template-columns: 1fr;
  }
  .form-actions > * {
    flex: 1;
  }
  .source-choices {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 6px;
  }
  .source-choices button {
    font-size: 10px;
    justify-content: center;
    padding: 10px 7px;
  }
  .source-choices svg {
    flex: none;
  }
  .result-item {
    gap: 8px;
  }
  .result-item img {
    width: 45px;
    height: 45px;
  }
  .result-item h4 {
    font-size: 10px;
  }
  .select-btn {
    font-size: 10px;
    padding: 8px;
  }
  .selected-panel {
    padding: 12px;
  }
  .metadata-form .form-actions {
    grid-column: 1;
  }
}
</style>
