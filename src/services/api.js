const API_BASE_URL = (import.meta.env.VITE_API_URL || 'http://localhost:8000/api').replace(/\/$/, '');

const readToken = () => localStorage.getItem('lunu_access_token');

const request = async (path, options = {}) => {
  const headers = new Headers(options.headers || {});
  if (!headers.has('Content-Type') && options.body) headers.set('Content-Type', 'application/json');
  const token = readToken();
  if (token) headers.set('Authorization', `Bearer ${token}`);
  const response = await fetch(`${API_BASE_URL}${path}`, { ...options, headers });
  const contentType = response.headers.get('content-type') || '';
  const payload = contentType.includes('application/json') ? await response.json() : await response.text();
  if (!response.ok) {
    const message = typeof payload === 'object' && payload?.detail ? payload.detail : 'Yêu cầu không thành công.';
    const error = new Error(message);
    error.status = response.status;
    throw error;
  }
  return payload;
};

export const getApiBaseUrl = () => API_BASE_URL;

export const login = (username, password) => request('/login', {
  method: 'POST',
  body: JSON.stringify({ username, password }),
});

export const getUsers = async () => {
  try { return await request('/users'); }
  catch (error) { console.error('Lỗi lấy users:', error); return []; }
};

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

export const addSong = async (videoId) => {
  try { return await request('/songs/add', { method: 'POST', body: JSON.stringify({ video_id: videoId }) }); }
  catch (error) { console.error('Lỗi thêm bài hát:', error); return { success: false, message: error.message }; }
};

export const deleteSong = (id) => request(`/songs/${encodeURIComponent(id)}`, { method: 'DELETE' });

export const getHealth = () => request('/health');
