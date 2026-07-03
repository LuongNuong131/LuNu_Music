<!-- src/App.vue -->
<template>
  <!-- <router-view /> là nơi Vue Router sẽ hiển thị các component (Login.vue hoặc PlayerView.vue) -->
  <router-view />
  <!-- Toast đặt ở gốc app để dùng chung được cho mọi trang -->
  <Toast />
</template>

<script setup>
// Component gốc hiện tại rất gọn gàng, không cần logic gì phức tạp ở đây cả.
// Mọi logic sẽ được xử lý riêng rẽ ở từng View. Theme tổng (màu, font) nằm ở src/style.css
import Toast from './components/Toast.vue';
</script>

<style>
/* CSS Reset cơ bản để web không bị viền trắng mặc định của trình duyệt */
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: var(--font-body, 'Manrope', sans-serif);
  background-color: var(--bg-color, #0b0a08);
  color: var(--text-main, #f5f0e6);
  overflow: hidden; /* Ngăn scroll toàn trang để app giống như một ứng dụng desktop */
}
</style>