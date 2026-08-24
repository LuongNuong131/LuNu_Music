import { reactive, ref } from 'vue';

export const authState = reactive({
  user: JSON.parse(localStorage.getItem('lunu_user')) || null,
});

export const currentView = ref('home'); // 'home' hoặc 'admin'

export const loginUser = (userData) => {
  authState.user = userData;
  localStorage.setItem('lunu_user', JSON.stringify(userData));
};

export const logoutUser = () => {
  authState.user = null;
  currentView.value = 'home';
  localStorage.removeItem('lunu_user');
};