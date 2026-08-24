<template>
  <div class="glass-search-container">
    <div class="search-wrapper">
      <input
        v-model="searchQuery"
        @keyup.enter="handleSearch"
        type="text"
        placeholder="Nhập tên bài hát để quét YouTube..."
        class="glass-input"
        :disabled="isSearching || isDownloading"
      />
      <button @click="handleSearch" :disabled="isSearching || isDownloading || !searchQuery.trim()" class="glass-btn">
        <span v-if="isSearching">Đang quét...</span>
        <span v-else>Tìm Kiếm</span>
      </button>
    </div>
    
    <transition name="fade">
      <p v-if="message" class="status-message">{{ message }}</p>
    </transition>

    <div v-if="searchResults && searchResults.length > 0" class="results-list">
      <div v-for="video in searchResults" :key="video?.id" class="result-item">
        <img v-if="video?.id" :src="'https://i.ytimg.com/vi/' + video.id + '/hqdefault.jpg'" alt="thumb" class="video-thumb" />
        
        <div class="video-info">
          <h4 class="video-title" :title="video?.title">{{ video?.title || 'Không có tiêu đề' }}</h4>
          <p class="video-channel">{{ video?.uploader || 'Không rõ' }}</p>
        </div>
        
        <button 
          v-if="video?.id"
          @click="handleDownload(video)" 
          :disabled="isDownloading" 
          class="glass-btn download-btn"
        >
          <span v-if="downloadingId === video.id">Đang tải...</span>
          <span v-else>Tải bài này</span>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import { searchYoutube, addSong } from '../services/api';

const searchQuery = ref('');
const searchResults = ref([]);
const isSearching = ref(false);
const isDownloading = ref(false);
const downloadingId = ref(null);
const message = ref('');

const emit = defineEmits(['song-added']);

const handleSearch = async () => {
  if (!searchQuery.value.trim()) return;

  isSearching.value = true;
  message.value = 'Đang quét danh sách trên YouTube, chờ xíu nha...';
  searchResults.value = [];

  try {
    const res = await searchYoutube(searchQuery.value);
    if (res && res.success) {
      searchResults.value = res.results || [];
      message.value = `Tìm thấy ${searchResults.value.length} kết quả. Ông chọn bài chuẩn để tải đi!`;
    } else {
      message.value = res?.message || 'Không tìm thấy kết quả hoặc bị YouTube chặn.';
    }
  } catch (error) {
    message.value = 'Có lỗi xảy ra khi gọi server!';
  } finally {
    isSearching.value = false;
  }
};

const handleDownload = async (video) => {
  if (!video || !video.id) return;
  
  isDownloading.value = true;
  downloadingId.value = video.id;
  message.value = `Đang bắt đầu tải và đưa bài "${video.title}" lên mây...`;

  try {
    const res = await addSong(video.id);
    message.value = res?.message || 'Đã đưa vào hàng chờ xử lý!';
    
    setTimeout(() => {
      emit('song-added');
      message.value = 'Danh sách nhạc đã được làm mới!';
      searchResults.value = [];
      searchQuery.value = '';
      isDownloading.value = false;
      downloadingId.value = null;
      setTimeout(() => { message.value = ''; }, 3000);
    }, 15000);

  } catch (error) {
    message.value = 'Có lỗi khi gọi lệnh tải!';
    isDownloading.value = false;
    downloadingId.value = null;
  }
};
</script>

<style scoped>
.glass-search-container {
  display: flex;
  flex-direction: column;
  gap: 16px;
  padding: 24px;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 16px;
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  box-shadow: 0 4px 30px rgba(0, 0, 0, 0.1);
  margin-bottom: 24px;
}
.search-wrapper { display: flex; gap: 15px; }
.glass-input { flex: 1; padding: 12px 20px; border-radius: 12px; border: 1px solid rgba(255, 255, 255, 0.2); background: rgba(0, 0, 0, 0.3); color: #fff; font-size: 1rem; outline: none; transition: all 0.3s ease; }
.glass-input:focus { border-color: #1db954; box-shadow: 0 0 10px rgba(29, 185, 84, 0.3); }
.glass-btn { padding: 12px 24px; border-radius: 12px; border: 1px solid rgba(29, 185, 84, 0.5); background: rgba(29, 185, 84, 0.2); color: #1db954; font-weight: bold; font-size: 1rem; cursor: pointer; transition: all 0.3s ease; white-space: nowrap; }
.glass-btn:hover:not(:disabled) { background: rgba(29, 185, 84, 0.8); color: white; box-shadow: 0 0 15px rgba(29, 185, 84, 0.5); }
.glass-btn:disabled { border-color: rgba(255, 255, 255, 0.2); background: rgba(255, 255, 255, 0.05); color: rgba(255, 255, 255, 0.3); cursor: not-allowed; }
.status-message { font-size: 0.95rem; color: #1db954; margin: 0; }
.results-list { display: flex; flex-direction: column; gap: 12px; max-height: 400px; overflow-y: auto; padding-right: 10px; }
.results-list::-webkit-scrollbar { width: 6px; }
.results-list::-webkit-scrollbar-thumb { background: rgba(29, 185, 84, 0.5); border-radius: 6px; }
.result-item { display: flex; align-items: center; gap: 15px; background: rgba(0, 0, 0, 0.3); padding: 12px; border-radius: 12px; border: 1px solid rgba(255, 255, 255, 0.05); transition: all 0.3s ease; }
.result-item:hover { background: rgba(0, 0, 0, 0.5); border-color: rgba(29, 185, 84, 0.3); }
.video-thumb { width: 100px; height: 56px; border-radius: 8px; object-fit: cover; box-shadow: 0 2px 8px rgba(0,0,0,0.5); }
.video-info { flex: 1; min-width: 0; }
.video-title { margin: 0 0 4px 0; font-size: 1rem; color: #fff; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.video-channel { margin: 0; font-size: 0.85rem; color: #b3b3b3; }
.download-btn { padding: 8px 16px; font-size: 0.9rem; }
.fade-enter-active, .fade-leave-active { transition: opacity 0.5s ease; }
.fade-enter-from, .fade-leave-to { opacity: 0; }
</style>