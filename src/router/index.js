import { createRouter, createWebHistory } from 'vue-router';
import Login from '../views/Login.vue';
import PlayerView from '../views/PlayerView.vue';
import { authState } from '../store/appState';

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/login', name: 'Login', component: Login },
    { path: '/', name: 'Player', component: PlayerView, meta: { requiresAuth: true } },
    { path: '/:pathMatch(.*)*', redirect: '/' },
  ],
});

router.beforeEach((to) => {
  const isLoggedIn = Boolean(authState.user && authState.token);
  if (to.meta.requiresAuth && !isLoggedIn) return { name: 'Login' };
  if (to.name === 'Login' && isLoggedIn) return { name: 'Player' };
  return true;
});

export default router;
