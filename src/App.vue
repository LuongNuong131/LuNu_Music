<!-- src/App.vue -->
<template>
  <!-- <router-view /> là nơi Vue Router sẽ hiển thị các component (Login.vue hoặc PlayerView.vue) -->
  <router-view />
</template>

<script setup>
// Component gốc hiện tại rất gọn gàng, không cần logic gì phức tạp ở đây cả.
// Mọi logic sẽ được xử lý riêng rẽ ở từng View.
</script>

<style>
/* CSS Reset cơ bản để web không bị viền trắng mặc định của trình duyệt */
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
  background-color: #121212; /* Tone màu dark theme tối giản */
  color: #ffffff;
  overflow: hidden; /* Ngăn scroll toàn trang để app giống như một ứng dụng desktop */
}
</style>