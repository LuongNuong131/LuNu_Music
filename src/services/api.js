const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

export const login = async (username, password) => {
  try {
    const res = await fetch(`${API_BASE_URL}/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password })
    });
    return await res.json();
  } catch (error) {
    return { success: false, message: "Lỗi kết nối Server" };
  }
};

export const getUsers = async () => {
  try {
    const res = await fetch(`${API_BASE_URL}/users`);
    return await res.json();
  } catch (error) {
    return [];
  }
};

export const addUser = async (username, password, role) => {
  try {
    const res = await fetch(`${API_BASE_URL}/users/add`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password, role })
    });
    return await res.json();
  } catch (error) {
    return { success: false, message: "Lỗi thêm User" };
  }
};

export const deleteUser = async (id) => {
  try {
    const res = await fetch(`${API_BASE_URL}/users/${id}`, { method: 'DELETE' });
    return await res.json();
  } catch (error) {
    return { success: false, message: "Lỗi xoá User" };
  }
};

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
    return { success: false, message: "Lỗi kết nối server khi tải!" };
  }
};

export const deleteSong = async (id) => {
  try {
    const res = await fetch(`${API_BASE_URL}/songs/${id}`, { method: 'DELETE' });
    return await res.json();
  } catch (error) {
    return { success: false, message: "Lỗi xoá bài hát" };
  }
};