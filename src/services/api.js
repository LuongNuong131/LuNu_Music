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
      cover: songData.cover || '',
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

export const searchCinema = async (query) => {
  try { return await request(`/cinema/search_youtube?query=${encodeURIComponent(query)}`); }
  catch (error) { console.error('Lỗi tìm kiếm LuNu Cinema:', error); return { success: false, message: error.message }; }
};

export const addCinemaVideo = async (videoData) => {
  try {
    return await request('/cinema/videos/add', { method: 'POST', body: JSON.stringify({
      video_id: videoData.videoId || videoData.video_id,
      title: videoData.title,
      uploader: videoData.uploader || 'YouTube',
      cover: videoData.cover || '',
      description: videoData.description || '',
    }) });
  } catch (error) {
    console.error('Lỗi thêm video Cinema:', error);
    return { success: false, message: error.message };
  }
};

export const deleteCinemaVideo = (id) => request(`/cinema/videos/${encodeURIComponent(id)}`, { method: 'DELETE' });

export const deleteSong = (id) => request(`/songs/${encodeURIComponent(id)}`, { method: 'DELETE' });

export const importLegacySongs = () => request('/songs/import-legacy', { method: 'POST' });

export const getHealth = () => request('/health');
