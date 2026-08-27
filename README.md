<div align="center">
  <img src="https://capsule-render.vercel.app/api?type=waving&color=0:0f172a,50:7c3aed,100:f5b97a&height=220&section=header&text=LuNu%20Music&fontSize=64&fontColor=ffffff&fontAlignY=38&desc=Listen%20deeply.%20Curate%20your%20own%20room.&descAlignY=60&descSize=17" alt="LuNu Music banner" width="100%" />

  <h1>LuNu Music</h1>
  <p><strong>A premium personal music library and private video tea room.</strong></p>
  <p>
    <a href="https://lunu-music.vercel.app"><img src="https://img.shields.io/badge/Live%20frontend-Vercel-000000?style=for-the-badge&logo=vercel&logoColor=white" alt="Live frontend" /></a>
    <a href="https://github.com/LuongNuong131/LuNu_Music"><img src="https://img.shields.io/badge/GitHub-LuongNuong131-181717?style=for-the-badge&logo=github&logoColor=white" alt="GitHub repository" /></a>
    <a href="https://lunu-music.onrender.com/api/health"><img src="https://img.shields.io/badge/API-Render-46E3B7?style=for-the-badge&logo=render&logoColor=111827" alt="API health" /></a>
  </p>
</div>

> **LuNu Music** là một không gian nghe nhạc cá nhân được xây dựng theo hướng product-first: thư viện bài hát, trình phát toàn cục, lyrics, playlist, quản trị media, đề xuất cộng đồng, thông báo và **LuNu Cinema / Tea Room** cùng tồn tại trong một trải nghiệm thống nhất.

## About the project

LuNu Music bắt đầu từ nhu cầu tạo một thư viện nghe nhạc riêng, sau đó phát triển thành một sản phẩm fullstack có quản lý tài khoản, lưu trữ media và workflow kiểm duyệt. Giao diện theo tinh thần **Midnight Vinyl**: nền tối, glass surface, amber accent, typography giàu cảm xúc và các trạng thái tương tác rõ ràng trên desktop lẫn mobile.

Đây không chỉ là một audio player. Frontend Vue 3 giao tiếp với FastAPI backend; backend xác thực người dùng, đọc/ghi Supabase, xử lý pipeline media bằng yt-dlp/FFmpeg và lưu asset trên Cloudinary. Vì vậy dữ liệu thư viện, quyền admin, trạng thái đề xuất và thông báo có thể được quản lý tập trung thay vì chỉ tồn tại trong trình duyệt.

> **Product direction:** biến việc nghe nhạc và xem video thành một phòng riêng có chủ đích — nhẹ nhàng, kiểm soát được và đủ chuyên nghiệp để tiếp tục mở rộng.

## Product surface

| Khu vực | Trải nghiệm chính |
|---|---|
| **Home / Library** | Duyệt thư viện, tìm kiếm bài hát/nghệ sĩ, Personal Rotation, bài yêu thích và thao tác thêm nhanh vào playlist. |
| **Global player** | PlayerBar cố định, Now Playing, queue, seek, volume, mute, shuffle, repeat và phím tắt. |
| **Lyrics Lab** | Tìm lyrics từ nguồn được hỗ trợ, xem trước, xác nhận, lưu plain text, cập nhật hàng loạt và chỉnh sửa theo từng bài. |
| **Playlist workspace** | Tạo playlist, mô tả, thêm/xóa bài, phát toàn bộ và quản lý các bộ sưu tập nghe cá nhân. |
| **LuNu Cinema** | Tìm video hoặc kênh YouTube, chọn metadata, tải MP4, phát Theater mode và quản lý video đã lưu. |
| **Cinema retention** | Chọn **Lưu lâu dài** hoặc **Xem trong hôm nay**; video tạm có `expires_at` và được cleanup tự động/thủ công. |
| **Media proposals** | User đề xuất bài hát MP3 hoặc video MP4; admin duyệt/từ chối; pipeline và notification được đồng bộ. |
| **Notification Center** | Inbox đọc/chưa đọc, đánh dấu tất cả, xóa từng thông báo, xóa đã đọc và cleanup dữ liệu cũ. |
| **Admin Control Room** | Khôi phục 188 bài legacy, sửa metadata, quản lý user, lyrics, media proposals, Cinema và file Cloudinary. |
| **Responsive UX** | Sidebar desktop, bottom navigation mobile, modal/popup nội bộ, toast, safe-area và layout thích ứng. |

## Architecture

```text
                         ┌────────────────────────┐
                         │  Vue 3 + Vite frontend │
                         │  Vercel                │
                         └───────────┬────────────┘
                                     │ HTTPS / JSON API
                                     ▼
                         ┌────────────────────────┐
                         │ FastAPI backend         │
                         │ Render + Docker         │
                         └───────┬────────┬─────────┘
                                 │        │
                 ┌───────────────┘        └────────────────┐
                 ▼                                        ▼
      ┌────────────────────┐                    ┌────────────────────┐
      │ Supabase           │                    │ Cloudinary         │
      │ users, songs,      │                    │ audio/video assets │
      │ cinema, proposals, │                    │ secure delivery URL│
      │ notifications      │                    └────────────────────┘
      └────────────────────┘
                                 │
                                 ▼
                         ┌────────────────────────┐
                         │ yt-dlp + FFmpeg         │
                         │ source download/media   │
                         │ processing pipeline     │
                         └────────────────────────┘
```

The frontend never receives server secrets. It only receives public media delivery URLs and calls the backend through `VITE_API_URL`. Supabase, Cloudinary, YouTube API configuration, authentication signing and cookies remain server-side on Render.

## Technology stack

<div align="center">
  <img src="https://skillicons.dev/icons?i=vue,vite,javascript,python,fastapi,postgres,supabase,docker,git,github,vercel&perline=11" alt="LuNu Music technology stack" />
</div>

<p align="center">
  <img src="https://img.shields.io/badge/Vue%203-41B883?style=flat-square&logo=vuedotjs&logoColor=white" alt="Vue 3" />
  <img src="https://img.shields.io/badge/Vite-646CFF?style=flat-square&logo=vite&logoColor=white" alt="Vite" />
  <img src="https://img.shields.io/badge/FastAPI-009688?style=flat-square&logo=fastapi&logoColor=white" alt="FastAPI" />
  <img src="https://img.shields.io/badge/Python-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python" />
  <img src="https://img.shields.io/badge/Supabase-3ECF8E?style=flat-square&logo=supabase&logoColor=111827" alt="Supabase" />
  <img src="https://img.shields.io/badge/Cloudinary-3448C5?style=flat-square&logo=cloudinary&logoColor=white" alt="Cloudinary" />
  <img src="https://img.shields.io/badge/Render-46E3B7?style=flat-square&logo=render&logoColor=111827" alt="Render" />
</p>

| Layer | Technologies |
|---|---|
| **Frontend** | Vue 3, Composition API, Vue Router, Vite, JavaScript ES modules, CSS design tokens. |
| **Client state** | Reactive composables, localStorage for playlists/player preferences and selected local states. |
| **Backend** | Python 3.11, FastAPI, Pydantic, Uvicorn, PBKDF2 password hashing and signed LuNu access tokens. |
| **Database** | Supabase Postgres through the Python client and REST/PostgREST. |
| **Media** | yt-dlp, yt-dlp-ejs, Node.js runtime, FFmpeg and Cloudinary video/audio delivery. |
| **Deployment** | Vercel for the frontend, Render Docker service for the backend. |

## Repository layout

```text
LuNu_Music/
├── backend/
│   ├── main.py                  # FastAPI routes, auth, media jobs and integrations
│   ├── Dockerfile               # Render image with Python, FFmpeg and Node runtime
│   ├── requirements.txt         # Backend dependencies
│   └── legacy_catalog.json      # Catalog used to restore the 188 legacy songs
├── public/
│   ├── images/                  # Artwork and default ChoCiu cover
│   └── audio/                   # Local/demo assets when present
├── src/
│   ├── components/              # Player, queue, notifications, modal and shared UI
│   ├── composables/              # Player, playlist, toast, dialog and lyrics logic
│   ├── data/                     # Frontend catalog fallback and local state
│   ├── services/                 # API client and lyrics provider services
│   ├── store/                    # Authentication, view and player state
│   ├── views/                    # Home, Admin, Cinema, Lyrics, Playlist and Proposal screens
│   ├── App.vue                   # Authenticated application shell
│   └── style.css                 # Global design system and responsive rules
├── supabase/
│   ├── media_upgrade.sql         # Song/Cinema media columns and base table
│   ├── cinema_retention.sql      # Temporary Cinema retention and expiration
│   └── media_requests_notifications.sql # Proposals and notification tables
├── DEPLOYMENT.md                 # Detailed Render, Vercel and Supabase deployment notes
├── PRODUCT_UPGRADE_ROADMAP.md    # Product direction and future improvements
├── package.json
└── vite.config.js
```

## Local development

### Frontend

```bash
git clone https://github.com/LuongNuong131/LuNu_Music.git
cd LuNu_Music
npm install
```

Create `.env.local` in the repository root:

```env
VITE_API_URL=http://localhost:8000/api
```

Run Vite:

```bash
npm run dev
```

The frontend is normally available at `http://localhost:5173`.

### Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

For local backend work, configure the server-side variables in the shell or a local environment file that is excluded from Git. Never place these values in `src/`, Vercel frontend variables or committed files.

## Environment variables

### Vercel frontend

Only the public API base URL belongs in Vercel:

```env
VITE_API_URL=https://lunu-music.onrender.com/api
```

Because Vite injects `VITE_*` values at build time, redeploy Vercel after changing this value. Do not add Supabase keys, Cloudinary secrets, auth signing secrets or YouTube cookies to Vercel.

### Render backend

| Variable | Purpose |
|---|---|
| `SUPABASE_URL` | Supabase project URL. |
| `SUPABASE_KEY` | Current server-side Secret/Service Role key; never a frontend publishable key. |
| `CLOUDINARY_CLOUD_NAME` | Cloudinary cloud name. |
| `CLOUDINARY_API_KEY` | Cloudinary server-side API key. |
| `CLOUDINARY_API_SECRET` | Cloudinary server-side API secret. |
| `LUNU_AUTH_SECRET` | Long, stable signing secret for LuNu access tokens. Changing it invalidates existing sessions. |
| `CORS_ORIGINS` | Comma-separated Vercel and local frontend origins. |
| `YOUTUBE_API_KEY` | Recommended server-side key for stable YouTube search. |
| `YOUTUBE_COOKIES_PATH` | Optional path to a YouTube-only Netscape cookie Secret File. |
| `YOUTUBE_COOKIES_B64` | Optional alternative cookie input; avoid when Secret File is available. |
| `LUNU_SONG_START_SEQUENCE` | Optional song sequence start; default is `199`. |
| `LUNU_RENDER_MAX_DOWNLOAD_BYTES` | Cinema source safety limit; default is 450 MiB to protect the Render instance. |
| `LUNU_VIDEO_TRANSCODE_TIMEOUT_SECONDS` | FFmpeg video timeout; default is 900 seconds. |

A healthy backend can be checked at `https://lunu-music.onrender.com/api/health`. The current pipeline marker should include `video_pipeline: preflight-450mb-chunked` after the latest deployment.

## Supabase migrations

Run the migrations in Supabase SQL Editor in this order:

| Order | File | Purpose |
|---:|---|---|
| 1 | `supabase/media_upgrade.sql` | Adds media metadata columns and creates the Cinema table. |
| 2 | `supabase/cinema_retention.sql` | Adds `retention_mode`, `expires_at` and cleanup index. |
| 3 | `supabase/media_requests_notifications.sql` | Creates media proposals and notification tables. |
| 4 | `supabase/user_profiles.sql` | Adds profile and privacy fields used by social features. |
| 5 | `supabase/social_friends.sql` | Adds friend/block relationships and indexes. |
| 6 | `supabase/listening_rooms.sql` | Adds Listening Room and active room memberships. |
| 7 | `supabase/chat_messages.sql` | Adds direct/room conversations, 60-minute message expiry and chat reports. |

The migrations are intended to be idempotent, but they should still be applied deliberately and reviewed against the current schema. The backend uses the server-side key; do not expose that key in the frontend bundle. If an older deployment already applied some files, run only the missing migrations in dependency order and redeploy Render after the final migration.

## Chat retention and realtime behavior

Chat messages are created by the backend with an individual `expires_at` equal to server creation time plus 60 minutes. Reads hide expired rows immediately, and the periodic backend cleanup hard-deletes expired rows from the active Supabase database. This does not guarantee removal from provider backups, infrastructure logs, browser caches, screenshots or other copies outside the active application database.

The Chat Hub uses FastAPI WebSocket for low-latency delivery when the sender and recipient are connected to the same Render instance. The registry is in memory and does not synchronize across instances or restarts, so the frontend keeps a four-second REST polling fallback. The UI labels these modes accurately and does not promise zero latency. Direct chat is re-authorized against current friendship/block/privacy state on every access; room chat also requires current `room_members` membership.

The backend applies a lightweight per-instance limit of 30 messages per user per 60 seconds. A multi-instance deployment should replace this with a Redis or Supabase-RPC distributed limiter before increasing chat volume.

## Media lifecycle and safety

New songs and videos receive stable LuNu media keys. New songs follow the sequence convention beginning after the 188 legacy songs, while Cinema videos use the `VD` prefix. New media uses `/images/ChoCiu.jpg` as the stored default cover; YouTube thumbnails are preview-only search assets.

Cinema supports chunked Cloudinary upload for video files. When the current Cloudinary configuration refuses a file at the 100 MiB endpoint limit, the backend attempts a compatible FFmpeg-compressed version below the safe threshold. This preserves a playable library item, but it does not preserve the original quality or make a plan with a 100 MiB limit accept a 1 GiB file.

Render has an explicit source-download safety limit because a video around 1.93 GiB previously caused the web instance to restart during download. A source above the limit is rejected before expensive downloading. Larger originals should be uploaded through a separate server-side/direct-upload workflow to storage that supports the required size, or processed on a dedicated worker with sufficient disk and memory.

All media operations must respect ownership, authorization, terms of service and copyright. The project should only store content that the operator has permission to download, retain and play.

## Popup and notification UX

LuNu Music uses a shared in-app interaction layer instead of native browser dialogs. `useToast.js` handles transient success/error/info feedback, while `useDialog.js` and `ConfirmModal.vue` handle confirmation and text input flows. Admin deletion, legacy restore, lyrics batch update, proposal moderation, Inbox cleanup, playlist deletion and Cinema deletion therefore remain inside the product visual system.

The global player, Notification Center and modal layers account for mobile navigation, safe-area spacing, viewport height and wrapping long messages. This prevents notification text from being clipped or hidden behind the player and bottom navigation.

## Common workflows

### Restore the 188 legacy songs

After `media_upgrade.sql` is applied and the backend is deployed, an admin can open **Admin → Kho nhạc → Khôi phục 188 bài**. Existing records are skipped safely; missing records are inserted into Supabase so the full legacy library becomes manageable through the admin UI.

### Add a song or Cinema video

An admin searches YouTube, selects a result, edits metadata and starts the media job. The backend downloads an authorized source, processes it, uploads the asset, writes the Supabase record and exposes job status to the frontend. A user follows a similar path through **Đề xuất media**, but the asset is not imported until an admin approves it.

### Use temporary Cinema retention

In Cinema, select **Xem trong hôm nay** before starting the import. The backend stores the expiration at the next midnight in Vietnam time. Cleanup runs periodically while the service is active, on library access and through the admin cleanup action. If Render is sleeping or restarting at the exact expiration time, the cleanup occurs on the next wake-up or library request.

### Manage lyrics

Lyrics can be searched from Admin, reviewed in a popup, confirmed and stored as plain text. Bulk import accepts JSON containing song IDs and lyrics. The audio URL and media key are not changed by lyrics updates.

## Quality checks

Run the following commands before opening a pull request or deploying a significant change:

```bash
npm run build
python3 -m py_compile backend/main.py
git diff --check
```

For backend changes that touch media jobs, also verify the health endpoint, test a small authorized media file first and inspect Render logs for the ordered states: preflight, download, upload/chunk, optional transcode, Cloudinary success and Supabase insert.

## Troubleshooting

### Frontend reports that the backend is unavailable

Check that Vercel has `VITE_API_URL=https://lunu-music.onrender.com/api`, redeploy Vercel after changing it, and confirm Render responds at `/api/health`. Verify `CORS_ORIGINS` contains the exact Vercel origin without an extra path.

### Health endpoint only returns the old two fields

The Render service is running an older image. Confirm the deployed branch is `master`, the service points to `LuongNuong131/LuNu_Music`, and deploy the latest commit. If necessary, use a cache-cleared deploy. The new response must contain `video_pipeline` and `video_download_limit_bytes`.

### A large Cinema video is rejected

This may be an intentional preflight rejection above the Render safety limit, or a Cloudinary plan limit. Choose a lower YouTube quality, use a shorter source, upload from an authorized personal machine through storage that supports the original size, or move the workload to a dedicated worker. Temporary retention only controls deletion timing; it does not increase Render or Cloudinary capacity.

### YouTube returns a challenge or no media stream

A cookie is optional and is not a fix for Cloudinary limits. If authorized content requires an account session, use a fresh YouTube-only Netscape Secret File on Render. Do not paste cookie values into chat, commit them to GitHub or expose them to the frontend. Public content that successfully downloads does not need cookies.

### Login becomes invalid after an auth secret change

Changing `LUNU_AUTH_SECRET` intentionally invalidates old tokens. Clear the site session or use the app logout flow, then sign in again. Keep the value stable between deploys after that.

### Supabase rejects the server key

Use the current server-side Secret/Service Role key in Render only. A future-issued JWT, a stale key or a frontend publishable key can cause authentication/database errors. Replace the server-side value through the provider dashboard without copying it into source control.

## Contributing

LuNu Music is developed as an iterative product. Keep API contracts backward-compatible where possible, place reusable UI behavior in composables, keep secrets server-side and test both desktop and mobile layouts. A useful pull request should describe the user-facing change, migration requirements, environment changes and verification performed.

## License and content

The repository does not currently declare a formal open-source license. Code, artwork, audio, video and lyrics may have different ownership conditions. Before public distribution or third-party deployment, add an explicit `LICENSE` and verify that every media asset is authorized for the intended use.

## Links

| Resource | Link |
|---|---|
| **Live application** | [lunu-music.vercel.app](https://lunu-music.vercel.app) |
| **Backend health** | [lunu-music.onrender.com/api/health](https://lunu-music.onrender.com/api/health) |
| **Source repository** | [github.com/LuongNuong131/LuNu_Music](https://github.com/LuongNuong131/LuNu_Music) |
| **Deployment guide** | [`DEPLOYMENT.md`](./DEPLOYMENT.md) |
| **Product roadmap** | [`PRODUCT_UPGRADE_ROADMAP.md`](./PRODUCT_UPGRADE_ROADMAP.md) |

---

<div align="center">
  <p><strong>Built with care by LuNu.</strong></p>
  <p>Listen deeply. Keep the room yours.</p>
  <img src="https://capsule-render.vercel.app/api?type=waving&color=0:f5b97a,50:7c3aed,100:0f172a&height=100&section=footer" alt="LuNu Music footer" width="100%" />
</div>

<!--
  LuNu Music project README
  Inspired by the presentation language of github.com/LuongNuong131.
-->


## Chat attachments và premium UI

Chat Hub hỗ trợ gửi ảnh JPG/PNG/WebP/GIF và các tệp PDF, TXT, CSV, JSON, ZIP cùng một số định dạng Office. File được gửi qua backend, kiểm tra MIME/magic bytes, giới hạn mặc định 25 MiB mỗi attachment rồi upload lên Cloudinary bằng resource type phù hợp. Metadata attachment được lưu cùng `chat_messages`, broadcast qua WebSocket và được xóa cùng message sau 60 phút; cleanup xóa asset Cloudinary trước khi xóa row database hoạt động.

Để bật tính năng này, chạy `supabase/chat_messages.sql` trước rồi chạy `supabase/chat_attachments.sql` trong Supabase SQL Editor. Frontend không chứa Cloudinary secret. Nếu chưa chạy migration attachment, chat chữ vẫn có thể dùng nhưng gửi/đọc attachment sẽ báo cần bật schema.

LuNu Music cũng có lớp premium visual refresh dùng chung cho workspace: ambient grid, glass hierarchy, focus state, spacing responsive, card elevation, typography rhythm và mobile-safe modal/notification layout. Lớp này không thay đổi audio element, player bar, queue persistence hay media URL.


## Premium visual system và Dark/Light mode

LuNu Music có design system dark premium mặc định và light mode warm editorial. Theme được quản lý trong `src/store/themeState.js`, áp dụng bằng CSS tokens trên `document.documentElement`, lưu vào `localStorage` với key `lunu-theme` và không reload trang hoặc reset player/queue. Desktop có theme switcher trong Sidebar; mobile có quick toggle ở app shell.

Các view dùng chung hierarchy glass surface, warm gold accent, violet identity, mint success, crimson destructive state, typography dễ đọc, focus-visible, responsive spacing và reduced-motion support. `PlayerBar.vue`, audio element và queue logic không thuộc visual redesign này.
