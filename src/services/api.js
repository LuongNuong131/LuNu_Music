// Nếu cấu hình VITE_API_URL trên Vercel thì dùng nó, không thì mặc định localhost
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

// --- AUTH & USERS ---
export const login = async (username, password) => {
  const res = await fetch(`${API_BASE_URL}/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password })
  });
  return await res.json();
};

export const getUsers = async () => {
  const res = await fetch(`${API_BASE_URL}/users`);
  return await res.json();
};

export const addUser = async (username, password, role) => {
  const res = await fetch(`${API_BASE_URL}/users/add`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password, role })
  });
  return await res.json();
};

export const deleteUser = async (id) => {
  const res = await fetch(`${API_BASE_URL}/users/${id}`, { method: 'DELETE' });
  return await res.json();
};

// --- SONGS ---
export const getSongs = async () => {
  try {
    const response = await fetch(`${API_BASE_URL}/songs`);
    if (!response.ok) throw new Error('Network error');
    return await response.json();
  } catch (error) {
    console.error("Lỗi lấy danh sách nhạc:", error);
    return [];
  }
};

export const searchYoutube = async (query) => {
  try {
    const response = await fetch(`${API_BASE_URL}/songs/search_youtube?query=${encodeURIComponent(query)}`);
    return await response.json();
  } catch (error) {
    console.error("Lỗi tìm kiếm YouTube:", error);
    return { success: false, message: "Lỗi kết nối server!" };
  }
};

export const addSong = async (videoId) => {
  try {
    const response = await fetch(`${API_BASE_URL}/songs/add`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ video_id: videoId }),
    });
    return await response.json();
  } catch (error) {
    console.error("Lỗi khi thêm bài hát:", error);
    throw error;
  }
};

export const deleteSong = async (id) => {
  const res = await fetch(`${API_BASE_URL}/songs/${id}`, { method: 'DELETE' });
  return await res.json();
};