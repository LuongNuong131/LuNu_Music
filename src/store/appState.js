import { reactive, ref } from 'vue';

const USER_KEY = 'lunu_user';
const TOKEN_KEY = 'lunu_access_token';

const readUser = () => {
  try { return JSON.parse(localStorage.getItem(USER_KEY)) || null; }
  catch (error) { localStorage.removeItem(USER_KEY); return null; }
};

export const authState = reactive({
  user: readUser(),
  token: localStorage.getItem(TOKEN_KEY) || '',
  isLoading: false,
  error: '',
});

export const currentView = ref('home');

export const loginUser = (payload) => {
  const user = payload?.user || payload;
  authState.user = user;
  authState.token = payload?.access_token || payload?.token || '';
  authState.error = '';
  localStorage.setItem(USER_KEY, JSON.stringify(user));
  if (authState.token) localStorage.setItem(TOKEN_KEY, authState.token);
};

export const updateAuthUser = (user) => {
  if (!user) return;
  authState.user = { ...authState.user, ...user };
  localStorage.setItem(USER_KEY, JSON.stringify(authState.user));
};

export const logoutUser = () => {
  authState.user = null;
  authState.token = '';
  authState.error = '';
  currentView.value = 'home';
  localStorage.removeItem(USER_KEY);
  localStorage.removeItem(TOKEN_KEY);
};

export const isAuthenticated = () => Boolean(authState.user && authState.token);
