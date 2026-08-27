# PROMPT KIẾN TRÚC DỰ ÁN VÀ UX/UI TOÀN BỘ LUNU MUSIC

Bạn là **Senior Software Architect, Product Designer, UX/UI Lead và Frontend Engineer** được giao nhiệm vụ hiểu, duy trì và tiếp tục phát triển dự án **LuNu Music**. Tài liệu này là bản đặc tả cấu trúc để bạn không chỉ sửa một màn hình riêng lẻ mà phải hiểu toàn bộ hệ thống, mối quan hệ giữa các trang, layout, component, store, API, player, social features và trải nghiệm responsive.

Hãy đọc prompt này cùng source code thực tế. Nếu prompt và source code có khác nhau, hãy ưu tiên source code hiện tại, báo rõ điểm khác biệt và không tự ý phá behavior đang chạy.

---

## 1. Product identity

**LuNu Music** là một digital tea room và social listening platform. Người dùng có thể nghe nhạc, xem Cinema, quản lý playlist, yêu thích bài hát, tìm theo ca sĩ, đọc lyrics, kết bạn, tạo Listening Room và chat với message/attachment tự hết hạn.

LuNu Music không nên được thiết kế như một dashboard CRUD thông thường. Cảm giác sản phẩm cần là:

> Một phòng trà kỹ thuật số cao cấp, tối, yên tĩnh, có chiều sâu, nơi music discovery, private listening và social presence được kết hợp trong một workspace thống nhất.

Sản phẩm có ba ưu tiên song song:

| Ưu tiên | Ý nghĩa |
|---|---|
| Listening first | Người dùng phải phát nhạc nhanh, ổn định và không bị gián đoạn |
| Social but private | Bạn bè, phòng nghe và chat phải có quyền truy cập rõ ràng |
| Premium but usable | Giao diện đẹp, có cá tính nhưng chữ đủ lớn, dễ đọc và dùng tốt trên mobile |

Mọi thay đổi phải ưu tiên **tính ổn định của player/audio/queue** trước các hiệu ứng hoặc refactor thẩm mỹ.

---

## 2. Technical architecture

### 2.1. Stack

| Layer | Technology |
|---|---|
| Frontend | Vue 3, Vite, Composition API, JavaScript |
| Frontend hosting | Vercel |
| Backend | FastAPI, Python 3.11 |
| Backend hosting | Render, Docker |
| Database | Supabase PostgreSQL qua Python client/PostgREST |
| Media storage | Cloudinary |
| Import pipeline | YouTube search, yt-dlp, FFmpeg, Cloudinary |
| Authentication | Custom HMAC signed token lưu trong localStorage |
| Realtime room | FastAPI/API adapter kết hợp persistence và polling |
| Chat realtime | FastAPI WebSocket cùng instance + polling fallback |

Production URLs:

```text
Frontend: https://lunu-music.vercel.app
Backend API: https://lunu-music.onrender.com/api
Repository: https://github.com/LuongNuong131/LuNu_Music
Main branch: master
```

### 2.2. Repository structure

Cây thư mục quan trọng hiện tại:

```text
LuNu_Music/
├── backend/
│   ├── main.py
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── legacy_catalog.json
│   └── ...
├── src/
│   ├── App.vue
│   ├── main.js
│   ├── style.css
│   ├── components/
│   ├── composables/
│   ├── data/
│   ├── services/
│   ├── store/
│   └── views/
├── supabase/
│   ├── media_upgrade.sql
│   ├── user_profiles.sql
│   ├── social_friends.sql
│   ├── listening_rooms.sql
│   ├── media_requests_notifications.sql
│   ├── chat_messages.sql
│   ├── chat_attachments.sql
│   └── ...
├── docs/
├── DEPLOYMENT.md
├── README.md
├── package.json
├── vite.config.js
└── vercel.json
```

### 2.3. Frontend folders

#### `src/App.vue`

App shell trung tâm. App chịu trách nhiệm:

- Xác định trạng thái authenticated/unauthenticated.
- Hiển thị Login khi chưa đăng nhập.
- Mount Sidebar/navigation.
- Mount view hiện tại.
- Mount PlayerBar toàn cục.
- Mount QueuePanel, NowPlaying, Toast, ConfirmModal hoặc dialog layer.
- Mount RoomSyncBridge global để room sync có thể hoạt động xuyên workspace.
- Điều hướng giữa các view mà không làm mất player.

App không được reset player hoặc reload toàn bộ trang khi người dùng đổi view.

#### `src/components/`

| Component | Trách nhiệm |
|---|---|
| `Sidebar.vue` | Navigation desktop và mobile drawer |
| `PlayerBar.vue` | Global audio player, controls, current song và seek |
| `NowPlayingView.vue` | Màn hình bài đang phát / lyrics / artwork |
| `QueuePanel.vue` | Queue hiện tại, reorder hoặc remove nếu behavior hiện có cho phép |
| `WaveformSeekBar.vue` | Seek interaction |
| `RoomSyncBridge.vue` | Adapter room playback opt-in, không phải player UI |
| `NotificationCenter.vue` | Notification dropdown/center và unread state |
| `Toast.vue` | Toast feedback không blocking |
| `ConfirmModal.vue` | Dialog xác nhận nội bộ |
| `CommandPalette.vue` | Tìm nhanh và command actions |
| `LyricsManager.vue` | Quản lý lyrics |
| `DiscordBotSearch.vue` | Tìm/import media theo workflow hiện có |

#### `src/views/`

| View | Mục tiêu |
|---|---|
| `PlayerView.vue` | Trang nghe nhạc chính / discovery / library |
| `MainView.vue` | Nội dung home/library, favorite interactions và các collection chính |
| `PlaylistsView.vue` | Danh sách và chi tiết playlist |
| `ArtistsView.vue` | Danh sách artist và artist-scoped playback |
| `CinemaView.vue` | Video Cinema đã lưu |
| `AccountView.vue` | Profile, avatar, display name, bio, password và privacy |
| `FriendsView.vue` | Search user, friend lifecycle, block và direct-chat CTA |
| `RoomsView.vue` | Tạo/join/leave/close Listening Room, host/member và sync opt-in |
| `ChatView.vue` | Direct/room chat, attachment, expiry, report và context delete |
| `ProposalView.vue` | User proposal cho song/video để Admin duyệt |
| `AdminView.vue` | Kho nhạc, users, lyrics, media pipeline và chat reports |
| `Login.vue` | Authentication entry point |

#### `src/store/`

| Store | Phạm vi state |
|---|---|
| `appState.js` | Auth, current view, global app state |
| `playerState.js` | Core player, current song, queue, history, play/pause/seek |
| `roomSession.js` | Room identity, membership, host, sync opt-in và room state |
| `chatSession.js` | Conversation đang chọn và navigation context |

`playerState.js` là vùng nhạy cảm. Social state không được trộn vào player state nếu không cần thiết.

#### `src/services/`

`api.js` là central HTTP client. Tất cả request phải đi qua API client để có:

- Base URL từ `VITE_API_URL`.
- Authorization token.
- JSON handling đúng.
- Multipart FormData không bị gắn nhầm `Content-Type: application/json`.
- Error normalization thân thiện với người dùng.

Không gọi Supabase hoặc Cloudinary trực tiếp từ frontend.

#### `src/composables/`

- `useLibrary.js`: load và thao tác library.
- `usePlaylists.js`: playlist state và mapping track.
- `useLyrics.js`: lyrics behavior.
- `useToast.js`: toast layer.
- `useDialog.js`: confirm/prompt dialog nội bộ.

---

## 3. App shell và layout hierarchy

### 3.1. Desktop shell

Desktop layout cần có ba vùng:

```text
┌───────────────────────────────────────────────────────────┐
│ Sidebar / Brand / Navigation                               │
│                                                           │
│ Main content workspace                         Notification│
│                                                           │
│                                                           │
├───────────────────────────────────────────────────────────┤
│ Global PlayerBar: artwork · title · controls · progress   │
└───────────────────────────────────────────────────────────┘
```

Sidebar là navigation cố định hoặc bán cố định ở bên trái. Main content phải có max-width hợp lý, không kéo quá rộng khiến typography khó đọc. PlayerBar luôn thuộc app shell và nằm ngoài các view content.

### 3.2. Mobile shell

Mobile không được chỉ hiển thị một trang Home. Cấu trúc bắt buộc:

```text
┌──────────────────────────┐
│ Menu button + page title │
│                          │
│ Main content             │
│                          │
├──────────────────────────┤
│ Compact global player    │
└──────────────────────────┘
```

Khi bấm Menu:

- Mở mobile drawer.
- Có backdrop.
- Có navigation đầy đủ.
- Chọn một mục sẽ đóng drawer.
- Không làm mất bài đang phát.
- Không đẩy player ra ngoài viewport.

### 3.3. Navigation information architecture

Navigation nên chia thành nhóm rõ ràng:

| Nhóm | Mục |
|---|---|
| Listen | Home/Library, Favorites, Playlists, Artists |
| Watch | LuNu Cinema, Tea Room nếu đang bật |
| Social | Friends, Listening Rooms, Chat |
| Account | Profile/Account |
| Admin | Admin Control Room, chỉ hiện với Admin |

Active navigation phải có cả màu, background và indicator; không chỉ đổi màu chữ. Trên mobile, touch target tối thiểu nên khoảng 44px.

---

## 4. Sitemap toàn bộ website

```text
LuNu Music
├── Login
├── Home / Player
│   ├── Library index
│   ├── Search/discovery
│   ├── Favorite toggle
│   ├── Add to playlist
│   ├── Play scoped collection
│   └── Queue access
├── Favorites
│   ├── Favorite summary
│   ├── Play all favorites
│   ├── Play one favorite
│   └── Favorite-only queue
├── Playlists
│   ├── Playlist index
│   ├── Create playlist
│   ├── Playlist detail
│   ├── Add/remove song
│   ├── Play playlist
│   └── Playlist-only queue
├── Artists
│   ├── Artist directory
│   ├── Search artist
│   ├── Artist detail
│   ├── Artist song list
│   └── Artist-only queue
├── Cinema
│   ├── Saved videos
│   ├── Watch video
│   └── Admin media management
├── Friends
│   ├── Search members
│   ├── Incoming requests
│   ├── Outgoing requests
│   ├── Accepted friends
│   ├── Block/privacy controls
│   └── Open direct chat
├── Listening Rooms
│   ├── Room directory
│   ├── Create room
│   ├── Join room
│   ├── Room detail
│   ├── Host controls
│   ├── Member list
│   ├── Playback sync opt-in
│   └── Open room chat
├── Chat
│   ├── Conversation list
│   ├── Direct chat
│   ├── Room chat
│   ├── Text message
│   ├── Image/file attachment
│   ├── Delete own message
│   ├── Report message
│   └── 60-minute expiry state
├── Proposals
│   ├── Search source
│   ├── Song proposal
│   ├── Video proposal
│   └── Proposal status
├── Account
│   ├── Profile
│   ├── Avatar
│   ├── Display name
│   ├── Bio
│   ├── Password
│   └── Privacy
└── Admin Control Room
    ├── Music library
    ├── Lyrics manager
    ├── Media pipeline
    ├── User directory
    ├── Notifications
    ├── Chat reports
    ├── Review/dismiss report
    └── Cleanup old data
```

---

## 5. Đặc tả UX/UI từng trang

### 5.1. Login

Login là cửa vào tối giản, tập trung vào form và brand identity. Không đưa quá nhiều thông tin quản trị vào màn hình này.

Cấu trúc:

```text
Brand mark
Headline ngắn
Username field
Password field
Primary CTA: Đăng nhập
Inline error nếu sai
Loading state khi submit
```

Form phải có label, focus state, disabled state và không dùng native alert.

### 5.2. Home / Player / Library

Đây là trang chính, cần ưu tiên discovery và nghe nhạc.

Cấu trúc đề xuất:

```text
Eyebrow: LUNU LIBRARY
Hero heading / short description
Search or command entry
Quick collections: Favorites / Playlists / Artists / Rooms
Library list hoặc card grid
Mỗi song row:
  cover · title · artist · duration/metadata · favorite · add playlist · play
```

Các action phải dễ nhận biết:

- Play từng bài.
- Add/remove favorite.
- Add vào playlist.
- Mở lyrics.
- Mở queue.
- Không làm mất current song khi thao tác metadata.

Không biến mỗi song row thành quá nhiều nút nhỏ khó bấm trên mobile. Desktop có thể hiển thị secondary actions khi hover; mobile nên hiển thị action menu hoặc nhóm nút rõ ràng.

### 5.3. Favorites

Favorites phải cho người dùng biết đây là một collection độc lập:

```text
Collection header
Tên: Yêu thích
Số lượng bài
CTA: Phát tất cả
Danh sách favorite songs
```

Mọi nút Play trong trang này phải tạo queue chỉ từ favorite list. Không được fallback về toàn library.

Empty state phải hướng dẫn user quay về Library để favorite bài hát, không để một vùng trống không giải thích.

### 5.4. Playlists

Playlist index hiển thị card hoặc row gồm tên playlist, số bài, artwork đại diện và last updated.

Playlist detail gồm:

```text
Back/navigation context
Playlist title + metadata
Play all CTA
Add song CTA
Song list
Remove from playlist action
```

Khi phát playlist, Next/Back chỉ chạy trong playlist đó. Nếu xóa bài đang phát khỏi playlist, player vẫn phải phát an toàn theo contract hiện có và không crash.

### 5.5. Artists

Artists là directory riêng, không chỉ là filter tạm trong Home.

Cấu trúc:

```text
Eyebrow: ARTIST DIRECTORY
Heading: Ca sĩ
Search artist
Artist cards/list
  artist name
  number of tracks
  representative cover/avatar
Artist detail khi chọn
  artist name
  track count
  Play artist
  track list
```

Khi user chọn artist, mọi thao tác Play/Next/Back trong context đó chỉ được chạy bài cùng artist. Khi rời trang hoặc chọn nguồn khác, scope mới được thay thế có chủ đích.

### 5.6. Cinema

Cinema có cảm giác giống một khu xem video riêng trong tea room.

Cấu trúc:

```text
Cinema header
Search/filter nếu có quyền
Video cards
  thumbnail/ChoCiu fallback
  title
  uploader/channel
  duration hoặc metadata nếu có
  Watch CTA
```

Admin có thêm media management và delete. User không được thấy action quản trị nếu không có role.

Video import phải hiển thị trạng thái queued/processing/success/failed. Không làm UI treo vô hạn.

### 5.7. Account

Account Center nên chia thành các section rõ ràng:

```text
Profile hero
  avatar
  display name
  username
  bio
Profile form
  display name
  bio
  avatar upload/url flow
Security section
  change password
Privacy section
  direct-message preference
```

Không hiển thị password hiện tại. Các thao tác nhạy cảm cần inline validation và confirmation khi cần.

### 5.8. Friends

Friends Hub gồm:

```text
Search people
Incoming requests
Outgoing requests
Accepted friends
Blocked users/privacy
```

Mỗi friend row nên có avatar, display name, username, relationship status và CTA phù hợp. Với friend accepted, CTA chính là **Chat**. Với request incoming, CTA là Accept/Reject. Với blocked, không hiện CTA chat.

### 5.9. Listening Rooms

Rooms nên có cảm giác như Discord-lite nhưng tối giản hơn.

Room directory card:

```text
Room name
Host
Member count
Private/public indicator
Join CTA
```

Room detail:

```text
Room header
Host badge
Member list
Current song / synced state
Opt-in sync control
Host controls nếu là host
Leave/close room
Open room chat
```

Không tự động đổi bài người dùng khi vừa join. Phải có affordance rõ như:

```text
Đồng bộ với host
[ Bật đồng bộ playback ]
```

Nếu user chưa opt-in, room chỉ hiển thị state mà không điều khiển player cá nhân.

### 5.10. Chat Hub

Chat layout:

```text
Chat header + realtime status
Conversation list
Active conversation header
Message list
Composer
```

Message bubble cần đọc được trên nền tối. Tên người gửi, thời gian và countdown phải có hierarchy rõ. Body message không dùng `v-html`.

Composer gồm:

- Textarea lớn, dễ đọc.
- Attach button.
- Preview file đang chọn.
- Upload state.
- Send button.
- Error state nếu file quá lớn hoặc MIME không hợp lệ.

Tin nhắn của chính user có thể:

- Bấm nút Xóa trên mobile.
- Nhấn chuột phải trên desktop để mở context menu.
- Xác nhận bằng dialog nội bộ.

Report message mở prompt nội bộ, không dùng browser prompt. User chỉ report được message trong conversation mà họ có quyền truy cập.

Hiển thị rõ nhưng không gây khó chịu:

```text
TỰ XÓA · 60P
còn 54:21
```

Không tạo toast success sau mỗi lần gửi message; message xuất hiện trực tiếp trong list là feedback đủ. Chỉ hiện toast cho lỗi, upload failure hoặc hành động quan trọng.

### 5.11. Proposals

Proposal page phải giải thích trạng thái:

```text
Draft/search
Pending
Processing
Approved
Rejected
Failed
```

User cần biết proposal đã gửi cho Admin, không phải media đã lập tức xuất hiện. File size và loại media phải hiển thị rõ nếu backend đã có dữ liệu.

### 5.12. Admin Control Room

Admin page là control center nhưng vẫn phải dùng cùng visual language.

Tabs chính:

```text
Kho nhạc
Báo cáo
Tài khoản
```

Kho nhạc có import, restore legacy, edit metadata, lyrics và delete.

Báo cáo có:

```text
Open count
Filter status
Report ID
Reporter
Sender
Reason
Reported body
Attachment link nếu còn
Mark reviewed
Dismiss
Delete resolved reports
```

Report đang open không được bị xóa bởi cleanup resolved. Nếu cleanup thành công, danh sách phải refresh và số lượng xóa phải chính xác.

---

## 6. Design system

### 6.1. Visual language

LuNu dùng dark premium visual system:

| Token | Vai trò |
|---|---|
| Deep background | Nền workspace, không đen tuyệt đối |
| Glass surface | Panel, modal, card |
| Warm gold | Primary accent, CTA, active emphasis |
| Violet | Brand identity, avatar, secondary accent |
| Mint | Success, online, accepted, safe state |
| Crimson | Error, delete, destructive action |
| Hairline | Border mảnh, divider |
| Text main | Body/heading chính |
| Text sub | Supporting text |
| Text faint | Metadata/helper |

### 6.2. Typography

Typography phải ưu tiên khả năng đọc:

- Heading display có cá tính nhưng không lạm dụng.
- Body text tối thiểu nên khoảng 13–14px ở desktop nếu là nội dung đọc.
- Mobile body không nên nhỏ hơn 13px.
- Metadata mono có thể nhỏ hơn nhưng không được dùng cho toàn bộ nội dung.
- Line-height body khoảng 1.5–1.7.
- Không dùng uppercase nhỏ cho đoạn văn dài.
- Không để title/artist/filename bị đè; dùng ellipsis có chủ đích.

### 6.3. Components

Button states:

```text
Default
Hover
Focus-visible
Pressed
Disabled
Loading
Destructive
```

Cards cần có hover nhẹ, không dùng animation quá mạnh. Modal phải có backdrop, focus behavior, mobile bottom-sheet hoặc layout co giãn.

Toast chỉ dành cho feedback ngắn, không được che composer hoặc player. Notification list phải có max-width, word wrapping và scroll.

### 6.4. Spacing và responsive breakpoints

Sử dụng spacing nhất quán, không viết margin ngẫu nhiên cho từng component.

Mốc kiểm tra bắt buộc:

| Viewport | Mục tiêu |
|---|---|
| 360px | Điện thoại nhỏ, không overflow |
| 390–430px | Điện thoại phổ biến, composer usable |
| 768px | Tablet, grid và drawer hợp lý |
| 1024px | Laptop nhỏ |
| 1440px | Desktop rộng, content vẫn có max-width |

Mọi page phải xử lý:

- Long title.
- Long artist name.
- Empty state.
- Loading state.
- Error state.
- No avatar/cover fallback.
- Keyboard focus.
- Touch targets.
- Safe area phía dưới cho mobile player.

---

## 7. User flows quan trọng

### Flow nghe nhạc cơ bản

```text
Login
→ Home/Library
→ chọn bài
→ PlayerBar giữ bài đang phát
→ Next/Back theo queue hiện tại
→ đổi page không dừng nhạc
```

### Flow Favorites

```text
Home
→ favorite nhiều bài
→ Favorites
→ Play all
→ queue chỉ chứa favorites
→ Next/Back không ra ngoài favorites
```

### Flow Playlist

```text
Home
→ Add to playlist
→ mở playlist
→ Play all
→ queue chỉ chứa playlist
```

### Flow Artist

```text
Artists
→ search artist
→ chọn artist
→ Play artist
→ queue chỉ chứa bài artist đó
```

### Flow social direct chat

```text
Friends
→ accepted friend
→ Chat
→ direct conversation
→ send text/image/file
→ message xuất hiện
→ report hoặc delete own message
```

### Flow room

```text
Rooms
→ create/join room
→ xem host/member/state
→ opt-in playback sync nếu muốn
→ mở room chat
→ leave/close room
```

### Flow report

```text
Chat
→ report message
→ nhập reason
→ backend authorize
→ insert chat_reports
→ notify Admin
→ Admin mở Báo cáo
→ reviewed hoặc dismissed
→ xóa resolved reports khi cần
```

---

## 8. Frontend architecture rules

1. Không gọi trực tiếp Supabase hoặc Cloudinary từ Vue.
2. Không đưa secret vào bundle frontend.
3. Không reload window cho thao tác CRUD thông thường.
4. Không reset global player khi route/view đổi.
5. Không để view social gọi trực tiếp vào audio element.
6. Dùng store/composable phù hợp thay vì duplicate state.
7. Dùng key ổn định cho `v-for`.
8. Dùng text interpolation an toàn, không dùng `v-html` cho user content.
9. Dùng dialog/toast nội bộ thay cho native browser dialogs.
10. Các nút async phải có disabled/loading state.
11. Các API error phải có fallback message thân thiện.
12. Khi data chưa có migration, UI phải hiển thị trạng thái cần migration thay vì crash.
13. Cần giữ mobile drawer usable sau mỗi navigation.
14. Không làm một global CSS override quá rộng khiến PlayerBar thay đổi ngoài ý muốn.

---

## 9. Backend relationship với UX

UX không được che giấu behavior backend:

| Backend behavior | UI cần thể hiện |
|---|---|
| WebSocket cùng instance | Realtime status đúng, không hứa zero delay |
| Polling fallback | Fallback status khoảng vài giây |
| Message expires_at | Countdown tự xóa |
| Cleanup eventual | Không nói xóa vật lý đúng từng giây |
| Cloudinary upload | Upload/loading/error/rollback state |
| Room membership auth | Không cho member cũ đọc/gửi |
| Direct friendship auth | Không mở chat với người block/chưa accepted |
| Report notification | Admin notification và Admin report tab |
| Rate limit | Message gửi quá nhanh có error rõ |

---

## 10. Các file không được sửa tùy tiện

Đặc biệt bảo vệ:

```text
src/components/PlayerBar.vue
src/store/playerState.js
src/components/NowPlayingView.vue
```

Nếu task không liên quan trực tiếp đến player, không sửa các file này. Trước và sau task phải kiểm tra:

```bash
git diff -- src/components/PlayerBar.vue src/store/playerState.js src/components/NowPlayingView.vue
```

Social, chat, admin và UI redesign không được làm gián đoạn audio hiện tại.

---

## 11. Checklist khi xây hoặc sửa một trang

Trước khi hoàn thành một view, phải kiểm tra:

| Câu hỏi | Đạt? |
|---|---|
| Trang này có loading state chưa? | ☐ |
| Có empty state chưa? | ☐ |
| Có error state chưa? | ☐ |
| Có disabled/loading cho action async chưa? | ☐ |
| Desktop có layout hợp lý chưa? | ☐ |
| Mobile 360px có overflow không? | ☐ |
| Text có đủ lớn và dễ đọc không? | ☐ |
| Long title có phá layout không? | ☐ |
| Có dùng native alert/confirm/prompt không? | ☐ |
| Có ảnh hưởng player không? | ☐ |
| Có dùng `v-html` không? | ☐ |
| Backend đã authorize chưa? | ☐ |
| Có cần migration/documentation không? | ☐ |

---

## 12. Checklist nghiệm thu toàn website

### Navigation

- Desktop sidebar hoạt động.
- Mobile menu mở/đóng đúng.
- Active state đúng.
- Admin navigation chỉ hiện cho Admin.
- Chuyển trang không dừng audio.

### Player

- Play/pause/seek không regression.
- Queue không bị reset khi đổi view.
- Next/Back đúng.
- Scoped queue đúng với Favorites/Playlist/Artist.
- Room sync vẫn opt-in.

### Content

- Library render đúng.
- Cover fallback đúng.
- Lyrics không làm page jump bất ngờ.
- Cinema không làm crash nếu media lỗi.
- Proposal status rõ.

### Social

- Friend request lifecycle đúng.
- Block/privacy có hiệu lực server-side.
- Room member/host đúng.
- Chat conversation đúng.
- Attachment hiển thị an toàn.
- Report đến Admin.

### Admin

- Song CRUD không đổi URL audio.
- User management đúng role.
- Report list có dữ liệu.
- Review/dismiss cập nhật ngay.
- Cleanup resolved report biến mất khỏi list.

### Responsive

- 360px.
- 390px.
- 768px.
- 1024px.
- 1440px.

---

## 13. Quy trình thực hiện task mới

Khi nhận task, hãy làm theo thứ tự:

1. Đọc yêu cầu và xác định trang/component/store/API bị ảnh hưởng.
2. Đọc source code thực tế trước khi viết code.
3. Kiểm tra `git status`, `git diff --stat`, `git log`.
4. Xác định có chạm player boundary hay không.
5. Thiết kế thay đổi nhỏ nhất, ưu tiên additive.
6. Implement theo component architecture hiện tại.
7. Test compile/build và smoke test phù hợp.
8. Test mobile logic và error states.
9. Kiểm tra diff không có secret, cookies hoặc artifact.
10. Ghi rõ migration/manual deploy nếu có.
11. Chỉ commit/push khi test pass.

Các lệnh cơ bản:

```bash
python3 -m py_compile backend/main.py
npm run build
git diff --check
git status --short
```

Nếu task liên quan player, phải test thêm sequence:

```text
Bài 1 → Next → Bài 2 → Back → Bài 1
```

Nếu task liên quan report/chat, phải test thêm:

```text
report mới → notification Admin → Admin review → cleanup resolved → list refresh
```

---

## 14. Format phản hồi sau khi làm việc

Sau mỗi task, trả lời bằng tiếng Việt theo mẫu:

```text
Đã xử lý:
...

Các file/component đã thay đổi:
...

UX/UI thay đổi:
...

Backend/API/schema thay đổi:
...

Kiểm thử đã chạy:
...

Player boundary:
PlayerBar/audio/queue có bị thay đổi hay không.

Commit/push:
...

Việc cần làm thủ công:
Migration, env hoặc deploy nếu có.

Giới hạn còn lại:
...
```

Không nói “đã hoàn thành toàn bộ” nếu mới chỉ build. Không nói realtime zero delay nếu có polling fallback. Không nói xóa mọi dấu vết nếu chỉ xóa active database và Cloudinary asset.

---

## 15. Mệnh lệnh bắt đầu dành cho AI

Hãy bắt đầu bằng việc:

1. Đọc cây thư mục repository.
2. Đọc `App.vue`, `style.css`, `Sidebar.vue`, `PlayerBar.vue`, `playerState.js`, các view liên quan và `api.js`.
3. Vẽ mental model của app shell, global player, navigation, view state, store và backend API.
4. Xác định những phần đang ổn định cần bảo vệ.
5. Đề xuất kế hoạch ngắn trước khi sửa.
6. Thực hiện từng thay đổi nhỏ, kiểm thử từng lớp.

Câu mở đầu mặc định:

> “T sẽ audit cấu trúc repository và toàn bộ app shell trước, đặc biệt bảo vệ PlayerBar/audio/queue. Sau đó t sẽ lập bản đồ ảnh hưởng, sửa theo hướng additive, kiểm tra responsive và chỉ kết luận sau khi build/test thực tế.”
