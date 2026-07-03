// src/main.js
import { createApp } from 'vue';
import App from './App.vue';
import router from './router';
import './style.css'; // File CSS global chứa các biến màu sắc và reset CSS, mình sẽ tạo sau

const app = createApp(App);

// Tích hợp Vue Router vào ứng dụng
app.use(router);

app.mount('#app');