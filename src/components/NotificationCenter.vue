<template>
  <div class="notification-center" :class="{ compact }">
    <button class="notification-trigger" type="button" aria-label="Mở thông báo" :aria-expanded="open" @click="toggle">
      <span>♢</span><b v-if="unreadCount">{{ unreadCount > 9 ? '9+' : unreadCount }}</b>
    </button>
    <Teleport to="body">
      <div v-if="open" class="notification-popover" @click.stop>
        <header class="notification-header">
          <div><span class="eyebrow">LUNU INBOX</span><h2>Thông báo</h2></div>
          <button type="button" class="popover-close" aria-label="Đóng thông báo" @click="open = false">×</button>
        </header>
        <div class="notification-toolbar">
          <button type="button" class="mark-all" :disabled="!unreadCount || loading" @click="markAll">Đọc tất cả</button>
          <button type="button" class="clear-read" :disabled="!readCount || loading" @click="clearRead">Xóa đã đọc</button>
          <button v-if="isAdmin" type="button" class="admin-cleanup" :disabled="loading" @click="cleanupOld">Dọn Inbox cũ</button>
        </div>
        <p v-if="actionMessage" class="notification-action" role="status">{{ actionMessage }}</p>
        <div v-if="schemaUnavailable" class="notification-state migration-hint"><span>!</span><strong>Cần kích hoạt Inbox</strong><p>Chạy migration notifications trong Supabase để nhận thông báo duyệt media.</p></div>
        <div v-else-if="loading && !items.length" class="notification-state">Đang đồng bộ...</div>
        <div v-else-if="!items.length" class="notification-state"><span>◌</span><p>Chưa có thông báo mới.</p></div>
        <div v-else class="notification-list">
          <article v-for="item in items" :key="item.id" class="notification-item" :class="{ unread: !item.is_read }" @click="read(item)">
            <span class="notification-icon">{{ iconFor(item.kind) }}</span>
            <span class="notification-copy"><strong>{{ item.title }}</strong><small>{{ item.body }}</small><time>{{ formatTime(item.created_at) }}</time></span>
            <span v-if="!item.is_read" class="unread-dot" aria-label="Chưa đọc"></span>
            <button type="button" class="notification-delete" aria-label="Xóa thông báo" @click.stop="remove(item)">×</button>
          </article>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue';
import { clearReadNotifications, cleanupNotifications, deleteNotification, getNotifications, markAllNotificationsRead, markNotificationRead } from '../services/api';
import { authState } from '../store/appState';
import { useDialog } from '../composables/useDialog';

const props = defineProps({ compact: { type: Boolean, default: false } });
const compact = computed(() => props.compact);
const open = ref(false); const loading = ref(false); const items = ref([]); const unreadCount = ref(0); const schemaUnavailable = ref(false); const actionMessage = ref(''); let timer = null;
const isAdmin = computed(() => authState.user?.role === 'admin');
const { promptDialog } = useDialog();
const readCount = computed(() => items.value.filter((item) => item.is_read).length);
const sync = async () => { if (schemaUnavailable.value) return; loading.value = true; try { const payload = await getNotifications(); if (payload?.available === false) { schemaUnavailable.value = true; return; } items.value = payload.items || []; unreadCount.value = payload.unread_count || 0; } catch (error) { const detail = String(error?.message || ''); if (detail.includes('public.notifications') || detail.includes('Could not find the table')) schemaUnavailable.value = true; else actionMessage.value = detail || 'Không thể đồng bộ thông báo lúc này.'; } finally { loading.value = false; } };
const toggle = () => { open.value = !open.value; if (open.value) sync(); };
const read = async (item) => { if (item.is_read) return; item.is_read = true; unreadCount.value = Math.max(0, unreadCount.value - 1); try { await markNotificationRead(item.id); } catch { item.is_read = false; unreadCount.value += 1; actionMessage.value = 'Không thể đánh dấu thông báo đã đọc.'; } };
const markAll = async () => { if (!unreadCount.value) return; try { await markAllNotificationsRead(); items.value.forEach((item) => { item.is_read = true; }); unreadCount.value = 0; actionMessage.value = 'Đã đánh dấu tất cả là đã đọc.'; } catch (error) { actionMessage.value = error.message || 'Không thể đánh dấu thông báo.'; } };
const remove = async (item) => { const index = items.value.findIndex((candidate) => candidate.id === item.id); if (index < 0) return; items.value.splice(index, 1); if (!item.is_read) unreadCount.value = Math.max(0, unreadCount.value - 1); try { await deleteNotification(item.id); actionMessage.value = 'Đã xóa thông báo.'; } catch (error) { items.value.splice(index, 0, item); if (!item.is_read) unreadCount.value += 1; actionMessage.value = error.message || 'Không thể xóa thông báo.'; } };
const clearRead = async () => { if (!readCount.value) return; const previous = items.value.slice(); const previousUnread = unreadCount.value; items.value = items.value.filter((item) => !item.is_read); try { const response = await clearReadNotifications(); actionMessage.value = `Đã xóa ${response.deleted_count || previous.length - previousUnread} thông báo đã đọc.`; } catch (error) { items.value = previous; unreadCount.value = previousUnread; actionMessage.value = error.message || 'Không thể xóa thông báo đã đọc.'; } };
const cleanupOld = async () => { const value = await promptDialog('Dọn các thông báo đã đọc cũ hơn bao nhiêu ngày trên toàn hệ thống?', '30', { title: 'Dọn Inbox cũ', confirmLabel: 'Dọn dữ liệu', placeholder: 'Số ngày', danger: true }); if (value === null) return; const days = Number(value); if (!Number.isInteger(days) || days < 1) { actionMessage.value = 'Số ngày không hợp lệ.'; return; } try { const response = await cleanupNotifications(days); actionMessage.value = response.message || `Đã dọn ${response.deleted_count || 0} thông báo.`; await sync(); } catch (error) { actionMessage.value = error.message || 'Không thể dọn Inbox hệ thống.'; } };
const iconFor = (kind) => kind?.includes('approved') ? '✓' : kind?.includes('rejected') || kind?.includes('failed') ? '!' : '✦';
const formatTime = (value) => { if (!value) return ''; try { return new Date(value).toLocaleString('vi-VN', { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' }); } catch { return ''; } };
onMounted(() => { sync(); timer = window.setInterval(sync, 30000); }); onBeforeUnmount(() => { if (timer) window.clearInterval(timer); });
</script>

<style scoped>
.notification-center { position: fixed; z-index: 390; top: 20px; right: 24px; }.notification-center.compact { position: relative; top: auto; right: auto; z-index: 1; width: auto; }.notification-center.compact .notification-trigger { width: 34px; height: 34px; border-radius: 10px; background: rgba(255,255,255,.045); box-shadow: none; }.notification-center.compact .notification-trigger span { font-size: 18px; }.notification-center.compact .notification-trigger b { top: -4px; right: -4px; }.notification-trigger { position: relative; display:grid; place-items:center; width:42px; height:42px; border:1px solid var(--hairline); border-radius:13px; background:rgba(13,16,24,.82); color:var(--gold); cursor:pointer; box-shadow:0 12px 32px rgba(0,0,0,.2); backdrop-filter:blur(12px); }.notification-trigger span { font-size:22px; transform:rotate(45deg); }.notification-trigger b { position:absolute; top:-5px; right:-5px; display:grid; place-items:center; min-width:18px; height:18px; padding:0 4px; border:2px solid #10131c; border-radius:99px; background:var(--crimson); color:#fff; font:8px var(--font-mono); }.notification-popover { position:fixed; top:84px; right:24px; display:flex; flex-direction:column; width:min(420px,calc(100vw - 32px)); max-height:min(650px,calc(100dvh - 90px)); overflow:hidden; border:1px solid var(--hairline); border-radius:17px; background:#141923; box-shadow:0 25px 80px rgba(0,0,0,.45); }.notification-header { display:flex; align-items:flex-start; justify-content:space-between; gap:14px; padding:18px 20px 13px; border-bottom:1px solid var(--hairline-soft); }.eyebrow { margin:0 0 7px; color:var(--gold); font:8px var(--font-mono); letter-spacing:1.7px; }.notification-popover h2 { color:var(--text-main); font:500 24px var(--font-display); }.popover-close { display:grid; place-items:center; flex:none; width:30px; height:30px; border:1px solid var(--hairline); border-radius:9px; background:transparent; color:var(--text-sub); cursor:pointer; font-size:20px; }.notification-toolbar { display:flex; justify-content:flex-end; gap:10px; padding:10px 20px; border-bottom:1px solid var(--hairline-soft); }.mark-all,.clear-read,.admin-cleanup { border:0; background:transparent; color:var(--gold); cursor:pointer; font-size:9px; }.clear-read { color:var(--text-sub); }.admin-cleanup { color:var(--violet); }.mark-all:disabled,.clear-read:disabled,.admin-cleanup:disabled { opacity:.35; cursor:default; }.notification-action { margin:10px 20px 0; color:var(--mint); font-size:10px; line-height:1.45; overflow-wrap:anywhere; }.notification-state { display:grid; justify-items:center; padding:48px 20px; color:var(--text-sub); text-align:center; font-size:11px; }.migration-hint strong { color:var(--text-main); font-size:12px; }.migration-hint p { max-width:280px; margin-top:8px; line-height:1.5; }.notification-state span { margin-bottom:9px; color:var(--gold); font-size:25px; }.notification-list { flex:1; min-height:0; padding:8px; overflow:auto; overscroll-behavior:contain; }.notification-item { position:relative; display:flex; align-items:flex-start; gap:10px; width:100%; box-sizing:border-box; padding:12px 10px; border:1px solid transparent; border-radius:11px; background:transparent; color:var(--text-main); text-align:left; cursor:pointer; }.notification-item:hover,.notification-item.unread { border-color:var(--hairline-soft); background:rgba(255,255,255,.045); }.notification-icon { display:grid; place-items:center; flex:none; width:29px; height:29px; border-radius:9px; background:rgba(245,185,122,.1); color:var(--gold); font-size:13px; }.notification-copy { display:flex; flex:1; flex-direction:column; min-width:0; }.notification-copy strong,.notification-copy small { overflow-wrap:anywhere; word-break:break-word; }.notification-copy strong { font-size:10px; line-height:1.45; }.notification-copy small { margin-top:4px; color:var(--text-sub); font-size:9px; line-height:1.5; }.notification-copy time { margin-top:6px; color:var(--text-faint); font:8px var(--font-mono); }.unread-dot { width:6px; height:6px; flex:none; margin-top:5px; border-radius:50%; background:var(--gold); box-shadow:0 0 9px var(--gold); }.notification-delete { display:grid; place-items:center; flex:none; width:25px; height:25px; border:0; border-radius:7px; background:transparent; color:var(--text-faint); cursor:pointer; font-size:17px; }.notification-delete:hover { background:rgba(255,109,125,.12); color:var(--crimson); }
@media (max-width:760px) { .notification-center { top:10px; right:12px; }.notification-center.compact { top:auto; right:auto; }.notification-popover { top:68px; right:12px; width:calc(100vw - 24px); max-height:calc(100dvh - 78px); border-radius:15px; }.notification-header { padding-inline:15px; }.notification-toolbar { padding-inline:15px; }.notification-action { margin-inline:15px; }.notification-item { padding-inline:8px; } }
</style>
