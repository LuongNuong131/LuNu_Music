const API_BASE_URL = (import.meta.env.VITE_API_URL || 'http://localhost:8000/api').replace(/\/$/, '');

import { logoutUser } from '../store/appState';

const readToken = () => localStorage.getItem('lunu_access_token');

const request = async (path, options = {}) => {
  const headers = new Headers(options.headers || {});
  if (!headers.has('Content-Type') && options.body && !(options.body instanceof FormData)) headers.set('Content-Type', 'application/json');
  const token = readToken();
  if (token) headers.set('Authorization', `Bearer ${token}`);
  let response;
  try {
    response = await fetch(`${API_BASE_URL}${path}`, { ...options, headers });
  } catch (cause) {
    const error = new Error(`Không thể kết nối backend tại ${API_BASE_URL}. Kiểm tra Render đang hoạt động và Vercel đang dùng đúng VITE_API_URL.`);
    error.code = 'NETWORK_ERROR';
    error.cause = cause;
    throw error;
  }
  const contentType = response.headers.get('content-type') || '';
  const payload = contentType.includes('application/json') ? await response.json() : await response.text();
  if (!response.ok) {
    const detail = typeof payload === 'object' ? payload?.detail : null;
    const message = Array.isArray(detail)
      ? detail.map((item) => {
        const field = Array.isArray(item?.loc) ? item.loc.filter((part) => part !== 'body').join('.') : '';
        return `${field ? `${field}: ` : ''}${item?.msg || 'Dữ liệu không hợp lệ.'}`;
      }).join(' · ')
      : typeof detail === 'string'
        ? detail
        : detail?.message || payload?.message || 'Yêu cầu không thành công.';
    const error = new Error(message);
    error.status = response.status;
    if (response.status === 401 && token && path !== '/login') {
      logoutUser();
      error.code = 'AUTH_EXPIRED';
      window.dispatchEvent(new CustomEvent('lunu-auth-expired'));
    }
    throw error;
  }
  return payload;
};

export const getApiBaseUrl = () => API_BASE_URL;

export const login = (username, password) => request('/login', {
  method: 'POST',
  body: JSON.stringify({ username, password }),
});

export const getUsers = () => request('/users');

export const addUser = (username, password, role = 'user') => request('/users/add', {
  method: 'POST',
  body: JSON.stringify({ username, password, role }),
});

export const deleteUser = (id) => request(`/users/${encodeURIComponent(id)}`, { method: 'DELETE' });

export const getSongs = async () => {
  try { return await request('/songs'); }
  catch (error) { console.error('Lỗi lấy danh sách nhạc:', error); return []; }
};

export const searchYoutube = async (query) => {
  try { return await request(`/songs/search_youtube?query=${encodeURIComponent(query)}`); }
  catch (error) { console.error('Lỗi tìm kiếm YouTube:', error); return { success: false, message: error.message }; }
};

export const addSong = async (songData) => {
  try {
    const payload = typeof songData === 'string' ? { video_id: songData, title: '', artist: '' } : {
      video_id: songData.videoId || songData.video_id,
      title: songData.title,
      artist: songData.artist,
      cover: songData.cover || '/images/ChoCiu.jpg',
      lyrics: songData.lyrics || '',
    };
    return await request('/songs/add', { method: 'POST', body: JSON.stringify(payload) });
  } catch (error) {
    console.error('Lỗi thêm bài hát:', error);
    return { success: false, message: error.message };
  }
};

export const getImportJob = (jobId) => request(`/songs/import-jobs/${encodeURIComponent(jobId)}`);

export const getCinemaVideos = () => request('/cinema/videos');

export const searchCinema = async (query, mode = 'video') => {
  try { return await request(`/cinema/search_youtube?query=${encodeURIComponent(query)}&mode=${encodeURIComponent(mode)}`); }
  catch (error) { console.error('Lỗi tìm kiếm LuNu Cinema:', error); return { success: false, message: error.message }; }
};

export const addCinemaVideo = async (videoData) => {
  try {
    return await request('/cinema/videos/add', { method: 'POST', body: JSON.stringify({
      video_id: videoData.videoId || videoData.video_id,
      title: videoData.title,
      uploader: videoData.uploader || 'YouTube',
      cover: videoData.cover || '/images/ChoCiu.jpg',
      description: videoData.description || '',
      retention_mode: videoData.retentionMode || videoData.retention_mode || 'permanent',
    }) });
  } catch (error) {
    console.error('Lỗi thêm video Cinema:', error);
    return { success: false, message: error.message };
  }
};

export const deleteCinemaVideo = (id) => request(`/cinema/videos/${encodeURIComponent(id)}`, { method: 'DELETE' });
export const cleanupExpiredCinemaVideos = () => request('/cinema/videos/cleanup-expired', { method: 'POST' });

export const searchSongLyrics = (id) => request(`/songs/${encodeURIComponent(id)}/lyrics/search`);

export const updateSongLyricsBulk = (items) => request('/songs/lyrics/bulk', {
  method: 'PATCH',
  body: JSON.stringify({ items }),
});

export const updateSong = (id, metadata) => request(`/songs/${encodeURIComponent(id)}`, {
  method: 'PATCH',
  body: JSON.stringify({ title: metadata.title, artist: metadata.artist, cover: metadata.cover || '/images/ChoCiu.jpg', lyrics: metadata.lyrics || '' }),
});

export const deleteSong = (id) => request(`/songs/${encodeURIComponent(id)}`, { method: 'DELETE' });

export const importLegacySongs = () => request('/songs/import-legacy', { method: 'POST' });

export const createMediaProposal = (proposal) => request('/media-proposals', { method: 'POST', body: JSON.stringify({ kind: proposal.kind, source_id: proposal.sourceId || proposal.source_id, title: proposal.title, artist: proposal.artist || '', uploader: proposal.uploader || 'YouTube', cover: proposal.cover || '/images/ChoCiu.jpg', description: proposal.description || '' }) });
export const getMyMediaProposals = () => request('/media-proposals/mine');
export const getMediaProposals = (status = '') => request(`/media-proposals${status ? `?status=${encodeURIComponent(status)}` : ''}`);
export const deleteMediaProposal = (id) => request(`/media-proposals/${encodeURIComponent(id)}`, { method: 'DELETE' });
export const cleanupMediaProposals = (beforeDays = 30) => request(`/media-proposals/cleanup?before_days=${encodeURIComponent(beforeDays)}`, { method: 'DELETE' });
export const approveMediaProposal = (id) => request(`/media-proposals/${encodeURIComponent(id)}/approve`, { method: 'POST', body: JSON.stringify({}) });
export const rejectMediaProposal = (id, reason = '') => request(`/media-proposals/${encodeURIComponent(id)}/reject`, { method: 'POST', body: JSON.stringify({ reason }) });
export const getNotifications = () => request('/notifications');
export const markNotificationRead = (id) => request(`/notifications/${encodeURIComponent(id)}/read`, { method: 'PATCH' });
export const markAllNotificationsRead = () => request('/notifications/read-all', { method: 'PATCH' });
export const deleteNotification = (id) => request(`/notifications/${encodeURIComponent(id)}`, { method: 'DELETE' });
export const clearReadNotifications = () => request('/notifications/clear-read', { method: 'DELETE' });
export const cleanupNotifications = (beforeDays = 30) => request(`/notifications/cleanup?before_days=${encodeURIComponent(beforeDays)}`, { method: 'DELETE' });

export const getHealth = () => request('/health');

export const getListeningRooms = () => request('/rooms');
export const createListeningRoom = (room) => request('/rooms', { method: 'POST', body: JSON.stringify({ name: room.name, visibility: room.visibility || 'private', max_members: Number(room.max_members) || 8 }) });
export const joinListeningRoom = (inviteCode) => request('/rooms/join', { method: 'POST', body: JSON.stringify({ invite_code: inviteCode }) });
export const getListeningRoom = (id) => request(`/rooms/${encodeURIComponent(id)}`);
export const updateListeningRoomState = (id, state) => request(`/rooms/${encodeURIComponent(id)}/state`, { method: 'PATCH', body: JSON.stringify({ current_song: state.current_song || null, queue: state.queue || [], is_playing: Boolean(state.is_playing), position_seconds: Number(state.position_seconds) || 0, expected_version: state.expected_version ?? null }) });
export const updateListeningRoom = (id, room) => request(`/rooms/${encodeURIComponent(id)}`, { method: 'PATCH', body: JSON.stringify({ name: room.name, visibility: room.visibility || 'private', max_members: Number(room.max_members) || 8 }) });
export const leaveListeningRoom = (id) => request(`/rooms/${encodeURIComponent(id)}/leave`, { method: 'POST' });
export const closeListeningRoom = (id) => request(`/rooms/${encodeURIComponent(id)}/close`, { method: 'POST' });

export const searchUsers = (query) => request(`/users/search?q=${encodeURIComponent(query)}`);
export const getFriends = () => request('/friends');
export const sendFriendRequest = (userId) => request('/friends/requests', { method: 'POST', body: JSON.stringify({ user_id: userId }) });
export const acceptFriendRequest = (id) => request(`/friends/requests/${encodeURIComponent(id)}/accept`, { method: 'POST' });
export const rejectFriendRequest = (id) => request(`/friends/requests/${encodeURIComponent(id)}/reject`, { method: 'POST' });
export const cancelFriendRequest = (id) => request(`/friends/requests/${encodeURIComponent(id)}/cancel`, { method: 'POST' });
export const removeFriend = (userId) => request(`/friends/${encodeURIComponent(userId)}`, { method: 'DELETE' });
export const blockUser = (userId) => request(`/blocks/${encodeURIComponent(userId)}`, { method: 'POST' });
export const unblockUser = (userId) => request(`/blocks/${encodeURIComponent(userId)}`, { method: 'DELETE' });
export const getPrivacySettings = () => request('/me/privacy');
export const updatePrivacySettings = (settings) => request('/me/privacy', { method: 'PATCH', body: JSON.stringify(settings) });

export const getChatConversations = () => request('/chat/conversations');
export const createDirectChat = (userId) => request('/chat/conversations/direct', { method: 'POST', body: JSON.stringify({ user_id: userId }) });
export const createRoomChat = (roomId) => request(`/chat/conversations/room/${encodeURIComponent(roomId)}`, { method: 'POST', body: JSON.stringify({}) });
export const getChatMessages = (conversationId, limit = 100) => request(`/chat/conversations/${encodeURIComponent(conversationId)}/messages?limit=${encodeURIComponent(limit)}`);
export const sendChatMessage = (conversationId, body) => request(`/chat/conversations/${encodeURIComponent(conversationId)}/messages`, { method: 'POST', body: JSON.stringify({ body }) });
export const sendChatAttachment = (conversationId, file, body = '') => { const formData = new FormData(); formData.append('file', file); formData.append('body', body); return request(`/chat/conversations/${encodeURIComponent(conversationId)}/attachments`, { method: 'POST', body: formData }); };
export const deleteChatMessage = (messageId) => request(`/chat/messages/${encodeURIComponent(messageId)}`, { method: 'DELETE' });
export const reportChatMessage = (messageId, reason) => request(`/chat/messages/${encodeURIComponent(messageId)}/report`, { method: 'POST', body: JSON.stringify({ reason }) });
export const cleanupChatMessages = () => request('/chat/cleanup', { method: 'DELETE' });
export const getAdminChatReports = (status = '') => request(`/admin/chat-reports${status ? `?status_filter=${encodeURIComponent(status)}` : ''}`);
export const reviewAdminChatReport = (id, status) => request(`/admin/chat-reports/${encodeURIComponent(id)}`, { method: 'PATCH', body: JSON.stringify({ status }) });
export const cleanupAdminChatReports = (beforeDays = 30) => request(`/admin/chat-reports/cleanup?before_days=${encodeURIComponent(beforeDays)}`, { method: 'DELETE' });

export const getMyProfile = () => request('/me');

export const updateMyProfile = (profile) => request('/me/profile', {
  method: 'PATCH',
  body: JSON.stringify({
    display_name: profile.display_name || '',
    bio: profile.bio || '',
  }),
});

export const changeMyPassword = (currentPassword, newPassword) => request('/me/password', {
  method: 'POST',
  body: JSON.stringify({ current_password: currentPassword, new_password: newPassword }),
});

export const uploadMyAvatar = (file) => {
  const formData = new FormData();
  formData.append('file', file);
  return request('/me/avatar', { method: 'POST', body: formData });
};

export const updateUserProfile = (id, profile) => request(`/users/${encodeURIComponent(id)}/profile`, {
  method: 'PATCH',
  body: JSON.stringify({
    display_name: profile.display_name || '',
    bio: profile.bio || '',
    role: profile.role || 'user',
  }),
});
