// src/router/index.js
import { createRouter, createWebHistory } from 'vue-router';
import Login from '../views/Login.vue';
import PlayerView from '../views/PlayerView.vue';

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: Login
  },
  {
    path: '/',
    name: 'Player',
    component: PlayerView,
    meta: { requiresAuth: true } // Đánh dấu route này cần phải đăng nhập
  }
];

const router = createRouter({
  history: createWebHistory(),
  routes
});

// Navigation Guard: Logic kiểm tra trước khi chuyển trang
router.beforeEach((to, from, next) => {
  // Kiểm tra trạng thái đăng nhập lưu trong localStorage
  const isLoggedIn = localStorage.getItem('isLoggedIn') === 'true';
  
  if (to.meta.requiresAuth && !isLoggedIn) {
    // Nếu trang yêu cầu đăng nhập mà chưa đăng nhập -> Đá về Login
    next('/login');
  } else if (to.path === '/login' && isLoggedIn) {
    // Nếu đã đăng nhập rồi mà cố tình vào lại Login -> Đá vào trang chủ nghe nhạc
    next('/');
  } else {
    // Hợp lệ thì cho đi tiếp
    next();
  }
});

export default router;