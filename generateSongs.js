// generateSongs.js
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

// Thiết lập đường dẫn cho ES Module
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Trỏ tới thư mục chứa nhạc và file output
const musicDir = path.join(__dirname, 'public', 'music');
const outputFile = path.join(__dirname, 'src', 'data', 'songs.js');

try {
  // Quét toàn bộ file trong thư mục public/music
  const files = fs.readdirSync(musicDir);
  
  // Lọc ra chỉ lấy các file có đuôi .mp3
  const mp3Files = files.filter(file => file.endsWith('.mp3'));

  if (mp3Files.length === 0) {
    console.log('⚠️ Không tìm thấy file .mp3 nào trong thư mục public/music.');
    process.exit();
  }

  // Khởi tạo mảng songs
  const songs = mp3Files.map((file, index) => {
    let title = file.replace('.mp3', '');
    let artist = 'LuNu Collection';

    // Thử tách tên ca sĩ và bài hát nếu tên file có chứa dấu gạch ngang '-'
    if (title.includes('-')) {
      const parts = title.split('-');
      artist = parts[0].trim();
      // Gộp các phần còn lại làm tên bài hát (phòng trường hợp tên bài có chứa dấu '-')
      title = parts.slice(1).join('-').trim();
    }

    return {
      id: index + 1,
      title: title,
      artist: artist,
      // Ảnh cover mặc định cực ngầu, ông có thể đổi link khác nếu muốn
      cover: '/images/ChoCiu.jpg',
      // Nhúng thẳng tên file gốc chưa chỉnh sửa (có khoảng trắng, tiếng Việt) vào url
      url: `/music/${file}`
    };
  });

  // Tạo nội dung hoàn chỉnh cho file songs.js
  const fileContent = `// src/data/songs.js
// ⚠️ FILE NÀY ĐƯỢC TẠO TỰ ĐỘNG BỞI SCRIPT generateSongs.js
// ⚠️ Không nên sửa bằng tay vì khi chạy lại script sẽ bị ghi đè!

export const songs = ${JSON.stringify(songs, null, 2)};
`;

  // Ghi đè vào file src/data/songs.js
  fs.writeFileSync(outputFile, fileContent, 'utf-8');
  console.log(`✅ Tuyệt vời! Đã quét và tự động tạo danh sách ${mp3Files.length} bài hát vào src/data/songs.js!`);
  
} catch (error) {
  console.error('❌ Có lỗi xảy ra:', error.message);
  console.log('💡 Hãy kiểm tra lại xem thư mục public/music đã tồn tại và chứa nhạc chưa nhé!');
}