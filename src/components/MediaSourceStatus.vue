<template>
  <section class="media-source-status" aria-label="Trạng thái nguồn nhạc">
    <div class="source-status-title">
      <Activity :size="18" />
      <h3>Nguồn nhạc</h3>
      <button aria-label="Làm mới trạng thái nguồn nhạc" :disabled="loading" @click="refresh">
        <RefreshCw :size="16" />
      </button>
    </div>
    <p v-if="error" role="status">{{ error }}</p>
    <template v-else-if="health"
      ><div class="source-badges">
        <span><Upload :size="14" /> Thêm file từ thiết bị</span
        ><span v-if="health.media_worker?.configured && health.media_worker?.configuration_valid"
          ><Server :size="14" /> Đã cấu hình máy tải riêng</span
        ><span v-if="health.youtube_cooldown_seconds"
          ><Clock3 :size="14" /> YouTube tạm nghỉ
          {{ Math.ceil(health.youtube_cooldown_seconds / 60) }} phút</span
        ><span v-if="health.direct_audio_providers?.jamendo?.configured">Jamendo</span>
      </div>
      <p v-if="health.media_worker?.configuration_valid === false">
        Cấu hình máy tải nhạc chưa hợp lệ. Kiểm tra địa chỉ HTTPS và khóa kết nối.
      </p>
      <p v-else-if="!health.media_worker?.configured">
        YouTube hiện tải qua máy chủ. Khi nguồn yêu cầu xác minh, bạn có thể thêm file từ thiết bị
        hoặc kết nối máy tải riêng.
      </p>
      <p v-else>
        Tác vụ YouTube được gửi đến máy tải riêng. File từ thiết bị và nguồn audio trực tiếp vẫn sẵn
        sàng.
      </p></template
    >
    <p v-else>Đang kiểm tra nguồn nhạc...</p>
  </section>
</template>
<script setup>
import { onMounted, ref } from 'vue';
import { Activity, Clock3, RefreshCw, Server, Upload } from '@lucide/vue';
import { getMediaHealth } from '../services/api';
const health = ref(null);
const error = ref('');
const loading = ref(false);
const refresh = async () => {
  loading.value = true;
  error.value = '';
  try {
    health.value = await getMediaHealth();
  } catch {
    error.value = 'Chưa kiểm tra được nguồn nhạc. Thử làm mới sau.';
  } finally {
    loading.value = false;
  }
};
onMounted(refresh);
</script>
<style scoped>
.media-source-status {
  padding: 17px;
  border: 1px solid var(--hairline);
  border-radius: 12px;
  background: var(--surface-2);
  margin-bottom: 22px;
}
.source-status-title {
  display: flex;
  align-items: center;
  gap: 8px;
  color: var(--gold);
}
.source-status-title h3 {
  font-size: 12px;
  font-weight: 500;
  color: var(--text-main);
  flex: 1;
}
.source-status-title button {
  display: grid;
  place-items: center;
  width: 34px;
  height: 34px;
  background: none;
  border: 0;
  color: var(--text-sub);
}
.source-badges {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin: 10px 0;
}
.source-badges > span {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 10px;
  padding: 6px 8px;
  border-radius: 6px;
  background: var(--accent-soft);
  color: var(--gold);
}
.media-source-status > p {
  font-size: 11px;
  line-height: 1.8;
  color: var(--text-sub);
  margin-top: 9px;
}
</style>
