# LuNu Music

> **LuNu Music** là thư viện nghe nhạc offline cá nhân với giao diện dark premium, trình phát nhạc tập trung vào trải nghiệm nghe, queue, tìm kiếm và hệ thống quản lý lyrics lưu trực tiếp trên thiết bị.

![LuNu Music — Now Playing](https://github.com/LuongNuong131/LuNu_Music/raw/master/public/images/ChoCiu.jpg)

## Tổng quan

LuNu Music được thiết kế cho việc nghe các file nhạc đã có sẵn trong thư viện local mà không phụ thuộc vào dịch vụ streaming. Ứng dụng có visual system **Midnight Vinyl** với nền midnight, glass surface, amber/coral accent, vinyl artwork stage và các trạng thái tương tác rõ ràng trên desktop lẫn mobile.

Bên cạnh chức năng nghe nhạc, phiên bản hiện tại có **Lyrics Lab** — một control room để quét, kiểm tra, chỉnh sửa và lưu lyrics riêng theo từng bài. Lyrics được phân loại thành synced LRC, plain lyrics, lyrics lưu local hoặc missing; dữ liệu thủ công và offset được lưu trong `localStorage` của trình duyệt.

## Tính năng chính

| Nhóm | Tính năng |
| --- | --- |
| **Audio player** | Phát/tạm dừng, bài trước/bài tiếp, seek, volume, mute, shuffle, repeat và progress bar. |
| **Offline library** | Thư viện bài hát local, không cần tài khoản streaming hoặc backend để phát nhạc. |
| **Now Playing** | Màn hình immersive với vinyl artwork, visualizer/equalizer, metadata, control deck và lyrics view. |
| **Queue** | Xem hàng đợi, track đang phát và thao tác queue trong drawer riêng. |
| **Search** | Tìm bài hát và nghệ sĩ trong thư viện local theo thời gian thực. |
| **Artists & playlists** | Duyệt theo nghệ sĩ, tạo playlist và tổ chức bộ sưu tập cá nhân. |
| **Lyrics Lab** | Filter inventory lyrics, mở editor, dán LRC/plain text, lưu thủ công và quản lý trạng thái. |
| **LRC sync** | Parse timestamp LRC, highlight dòng hiện tại, tự cuộn và click dòng để seek đến thời điểm tương ứng. |
| **Offset** | Chỉnh lyrics nhanh theo bước ±100 ms trong editor và Now Playing, có giới hạn an toàn và nút reset. |
| **Scan / Fix All** | Quét lyrics theo queue async, hiển thị progress, thống kê, cancel và retry khi provider lỗi. |
| **Responsive** | Sidebar desktop, bottom navigation mobile, mini-player và layout thích ứng theo kích thước màn hình. |

## Tech stack

- **Vue 3** với `<script setup>` và Composition API.
- **Vite** cho development server và production build.
- **Vue Router** cho điều hướng nội bộ.
- **JavaScript ES modules** cho service, composables và dữ liệu local.
- **CSS thuần** với design tokens, responsive media queries và animation.
- **localStorage** cho lyrics thủ công, offset và các state local cần giữ lại trên thiết bị.

## Yêu cầu môi trường

- Node.js 18 trở lên.
- npm 9 trở lên.
- Trình duyệt hiện đại có hỗ trợ HTML5 Audio, ES modules và `localStorage`.

## Cài đặt và chạy local

Clone repository và cài dependencies:

```bash
git clone https://github.com/LuongNuong131/LuNu_Music.git
cd LuNu_Music
npm install
```

Khởi động development server:

```bash
npm run dev
```

Sau đó mở URL mà Vite hiển thị, thường là `http://localhost:5173`.

## Các lệnh thường dùng

| Lệnh | Mục đích |
| --- | --- |
| `npm install` | Cài dependencies. |
| `npm run dev` | Chạy development server với hot reload. |
| `npm run build` | Build production vào thư mục `dist/`. |
| `npm run preview` | Preview bản production sau khi build. |

Trước khi tạo pull request, nên chạy:

```bash
npm run build
git diff --check
```

## Cấu trúc thư mục chính

```text
LuNu_Music/
├── public/
│   ├── audio/                  # Audio assets của thư viện local
│   ├── images/                 # Cover artwork
│   └── ...
├── src/
│   ├── components/
│   │   ├── LyricsManager.vue  # Lyrics Lab: scan, filter, editor, save
│   │   ├── NowPlayingView.vue  # Full-screen player và synced lyrics
│   │   ├── PlayerBar.vue       # Mini-player cố định
│   │   ├── QueuePanel.vue      # Queue drawer
│   │   ├── Sidebar.vue         # Desktop navigation rail
│   │   └── ...
│   ├── composables/
│   │   └── useLyrics.js        # Reactive lyrics state và active line
│   ├── services/
│   │   └── lyricsService.js    # Parse, resolve, cache và provider abstraction
│   ├── data/
│   │   └── songs.js            # Song metadata và audio catalog
│   ├── views/
│   │   ├── Login.vue
│   │   └── PlayerView.vue      # App shell và orchestration player
│   ├── App.vue
│   └── style.css               # Design system và responsive styles
├── index.html
├── package.json
└── vite.config.js
```

## Quy trình sử dụng Lyrics Lab

### 1. Mở Lyrics Lab

Chọn **Lyrics** trong sidebar hoặc mở shortcut Lyrics Lab trên Home. Màn hình sẽ hiển thị inventory của toàn bộ bài hát cùng các chỉ số Synced, Plain, Đã lưu và Cần bổ sung.

### 2. Quét thư viện

Bấm **Scan / Fix All Lyrics** để chạy scan async. Scan không chặn audio player; bạn có thể dừng giữa chừng bằng nút **Dừng quét**. Kết quả được chia thành bài đã có lyrics, bài tìm thấy nội dung, bài cần sửa tay và bài chưa có nguồn.

### 3. Thêm hoặc sửa lyrics

Tại mỗi row, bấm **Thêm lời** hoặc **Sửa**, sau đó dán một trong hai định dạng:

Plain lyrics:

```text
Dòng lời thứ nhất
Dòng lời thứ hai
Dòng lời thứ ba
```

LRC timestamp:

```text
[00:00.00]Dòng lời thứ nhất
[00:05.20]Dòng lời thứ hai
[00:10.40]Dòng lời thứ ba
```

Bấm **Lưu lyrics** để lưu vào thiết bị. Plain lyrics được hiển thị dạng static; LRC được highlight và đồng bộ theo thời gian phát.

### 4. Căn chỉnh offset

Nếu lyrics chạy sớm hoặc trễ, dùng `−` và `＋` trong khu vực **Lyrics offset**. Mỗi lần bấm thay đổi 100 ms. Offset được giữ lại cùng record lyrics của bài hát và có thể đưa về `0 ms` bằng nút **RESET**.

## Kiến trúc lyrics

Luồng xử lý lyrics được tách khỏi UI để có thể mở rộng mà không ảnh hưởng audio player:

```text
Current song
    │
    ▼
useLyrics composable
    │
    ▼
lyricsService.resolveLyrics()
    │
    ├── Local override / manual cache
    ├── Lyrics trong song metadata
    ├── Provider abstraction
    └── Missing / manual fallback
```

`lyricsService.js` chịu trách nhiệm parse LRC/plain text, lưu record và cung cấp điểm nối cho provider. `useLyrics.js` chuyển dữ liệu đó thành state reactive cho Now Playing, bao gồm `isLoading`, `isMissing`, `isSynced`, `activeLyricIndex`, `offsetMs` và các hàm cập nhật offset.

## Dữ liệu local và quyền riêng tư

Lyrics thủ công và offset được lưu trong `localStorage` của trình duyệt, không tự động gửi lên server. Khi xóa dữ liệu site hoặc đổi trình duyệt/thiết bị, các record local này có thể bị mất; nếu lyrics quan trọng, nên giữ bản LRC/plain text gốc bên ngoài ứng dụng.

Ứng dụng hiện không tự động bịa lyrics. Nếu một bài chưa có lyrics trong metadata và chưa có provider được cấu hình, Lyrics Lab sẽ hiển thị trạng thái **Cần bổ sung** để người dùng dán nội dung hợp lệ.

## Thêm lyrics provider

`src/services/lyricsService.js` có abstraction `lookupLyrics(song)` để nối một nguồn lyrics hợp lệ trong tương lai. Khi triển khai provider mới, nên bảo đảm:

1. Provider trả về `content`, `source` và nếu có thể là `format` hoặc timestamp LRC.
2. Request có timeout và xử lý lỗi rõ ràng.
3. Không chặn thao tác phát nhạc hoặc khóa UI.
4. Tuân thủ điều khoản sử dụng, giấy phép và quyền tác giả của nguồn lyrics.
5. Không ghi API key bí mật trực tiếp vào frontend static bundle.

Với provider cần secret hoặc server-side proxy, nên chuyển phần gọi provider sang backend phù hợp thay vì để credential trong mã client.

## Ghi chú về audio assets

Audio và artwork là dữ liệu của thư viện cá nhân. Khi phân phối dự án công khai, hãy kiểm tra quyền sử dụng đối với các file trong `public/audio` và `public/images`, đồng thời thay thế asset demo bằng nội dung mà bạn có quyền phân phối.

## Troubleshooting

### Ứng dụng không phát được audio

Kiểm tra URL trong `src/data/songs.js`, đảm bảo file tồn tại trong `public/audio` và trình duyệt hỗ trợ định dạng audio đó. Một số trình duyệt cũng yêu cầu người dùng click tương tác trước khi cho phép phát.

### Lyrics không tự đồng bộ

Chỉ dòng LRC có timestamp hợp lệ mới được sync. Nếu bạn dán plain lyrics, ứng dụng cố ý hiển thị static text thay vì tự đoán timing. Với LRC chạy lệch, hãy điều chỉnh offset trong editor hoặc Now Playing.

### Dữ liệu lyrics local biến mất

Kiểm tra bạn có đang dùng đúng origin/URL hay không. `localStorage` tách theo origin; đổi port, domain, chế độ trình duyệt hoặc xóa site data sẽ tạo storage mới.

### Build lỗi sau khi chỉnh component

Chạy lại:

```bash
npm run build
git diff --check
```

Sau đó kiểm tra lỗi template Vue, tên event giữa component cha/con và các import trong `src/services` hoặc `src/composables`.

## Đóng góp

1. Tạo branch riêng cho thay đổi.
2. Giữ component nhỏ và tách logic dùng lại vào composables/services.
3. Không đưa secret hoặc credential vào frontend.
4. Kiểm tra desktop và mobile trước khi commit.
5. Chạy `npm run build` và `git diff --check`.
6. Mô tả rõ thay đổi, ảnh hưởng UX và cách kiểm thử trong pull request.

## License

Repository chưa khai báo license chính thức. Nếu muốn public hoặc nhận đóng góp từ bên ngoài, hãy bổ sung file `LICENSE` và quy định rõ quyền sử dụng code, audio, artwork và lyrics trước khi phát hành.

---

Made for personal listening with **LuNu Music**.
