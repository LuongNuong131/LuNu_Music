# LuNu Music — Social Listening Platform Audit

> Phạm vi audit: đánh giá kiến trúc hiện tại, các phần đã có, khoảng trống, rủi ro bảo mật và scalability trước khi tiếp tục xây dựng profile, bạn bè, chat realtime và Listening Room hoàn chỉnh.

## A. Kiến trúc hiện tại

LuNu Music đang dùng Vue 3/Vite ở frontend và FastAPI ở backend. Backend hiện là một modular monolith chưa tách module, phần lớn logic nằm trong `backend/main.py`. Dữ liệu nghiệp vụ được lưu trong Supabase PostgreSQL thông qua Python Supabase client và media được lưu trên Cloudinary. YouTube/FFmpeg/yt-dlp được backend dùng cho luồng import media. Frontend deploy trên Vercel, backend deploy trên Render bằng Docker.

Auth hiện tại là token HMAC tự quản lý trong FastAPI, có thời hạn bảy ngày, token được lưu trong localStorage ở frontend. Player và queue cá nhân nằm ở `src/store/playerState.js`, được persist ở localStorage. Đây là ranh giới cần bảo vệ: social layer không được rewrite audio element, PlayerBar, queue cá nhân hoặc logic chuyển bài.

Realtime hiện chưa có WebSocket hoặc Supabase Realtime cho social features. Notification hiện tại chủ yếu dùng API và polling. Import jobs video/audio vẫn có phần lưu trong memory và chạy qua FastAPI background task, nên không phù hợp cho job dài nếu Render restart.

## B. Tính năng hiện có

Repository hiện đã có thư viện 188 bài legacy, restore/manage flow, metadata editing, lyrics plain text, Lyrics Lab, bulk lyrics, player/queue/library, playlist workspace, Cinema/Tea Room, media proposals, notification center, cleanup media và responsive UI. Toast và dialog nội bộ đã thay các native browser dialog.

Các lớp nền profile và Listening Room MVP cũng đã xuất hiện trong những thay đổi gần nhất: Account Center hỗ trợ display name, bio, avatar và đổi mật khẩu; Listening Room hỗ trợ tạo/join bằng invite code, host/member, queue room và nút đồng bộ playback opt-in. Đây mới là foundation/MVP, chưa đáp ứng đầy đủ realtime chat, friend system, automatic playback sync, reconnect và moderation.

## C. Các phần còn thiếu

| Khu vực | Trạng thái hiện tại | Khoảng trống cần hoàn thiện |
|---|---|---|
| Authentication | Login và admin cấp tài khoản | Register policy, refresh/revocation, session list, brute-force protection, account status |
| Profile | Display name, bio, avatar, đổi mật khẩu | Remove avatar, dimension/content validation, last active, privacy settings |
| Friends | Chưa có | Search user, request states, accept/reject/cancel/remove/block/mute |
| Chat | Chưa có realtime chat | Conversations, WebSocket/Realtime, reconnect, ack, ordering, expiry cleanup |
| Rooms | MVP tạo/join/state/polling | Realtime events, synchronized position, queue authority, invite permissions, moderation |
| Admin | User/media management cơ bản | Disable/enable, room moderation, reports, audit log, metrics, role separation |
| Quality | Build/compile và một số smoke test | Unit, integration, security, realtime, E2E và concurrency tests |

## D. Technical debt

`backend/main.py` đang ôm auth, user, media, Cloudinary, yt-dlp, Cinema, proposals, notifications và room logic. Trước mắt chưa cần đổi framework, nhưng nên tách domain logic dần thành `routers`, `services` và `repositories` để giảm nguy cơ sửa một tính năng làm hỏng tính năng khác.

Response API chưa có một error envelope thống nhất; một số nơi trả `message`, một số nơi ném `detail`. Import job còn phụ thuộc memory. Room snapshot hiện phải đọc members rồi đọc users, tạo nguy cơ N+1 khi mở rộng. Queue room đang là JSONB phù hợp MVP nhưng khó reorder/lock/version hóa khi concurrent users tăng.

Frontend đang dùng local reactive state và localStorage. Đây là lựa chọn phù hợp cho player cá nhân, nhưng không nên dùng localStorage làm nguồn sự thật cho room, friendship hoặc chat. Các social state đó phải lấy từ server và có event/version.

## E. Rủi ro bảo mật

| Rủi ro | Mức độ | Hướng xử lý |
|---|---:|---|
| Token tự quản lý trong localStorage | Cao | Giữ tương thích trước mắt, sau đó bổ sung refresh rotation/revocation; cân nhắc HttpOnly cookie khi đủ điều kiện |
| Fallback tương thích plaintext ở login | Cao | Migrate toàn bộ password legacy sang hash rồi loại bỏ fallback plaintext |
| Không có rate limit auth/search/chat | Cao | Thêm rate limit theo IP/user/route và cooldown |
| Upload avatar chỉ kiểm tra MIME client gửi | Cao | Kiểm tra magic bytes, decode ảnh, kích thước pixel, extension và content sau upload |
| Quyền admin có thể sửa role | Cao | Server-side check, cấm mass assignment, bảo vệ last admin và ghi audit log |
| Room authority ở frontend nếu không kiểm tra server | Cao | Mọi state/queue action phải validate membership/role/version ở backend |
| WebSocket chưa có | Cao | Khi thêm phải authenticate connection, kiểm tra room membership và chống replay/stale event |
| Error có thể lộ nội bộ | Trung bình | Production trả mã nghiệp vụ; log server giữ chi tiết nhưng không log token/password/chat không cần thiết |
| Secret/cookie đã từng xuất hiện trong phiên | Cao | Rotate/revoke theo từng provider, không commit hoặc đưa lên Vercel |

## F. Rủi ro scalability

Render web process hiện không phải durable worker. Job dài, file tạm lớn và FFmpeg có thể làm web process restart. Social room không nên phụ thuộc vào background task của web process. Với MVP nhỏ có thể dùng Supabase Realtime và polling fallback; khi có nhiều user cần connection lifecycle, rate limit, event dedupe và worker cleanup rõ ràng.

Không nên ghi playback position mỗi frame. Chỉ ghi event thay đổi như play, pause, seek, next và snapshot định kỳ. Server nên giữ `version` tăng dần; client bỏ qua event cũ. Với room state, cần optimistic concurrency bằng `expected_version` hoặc transaction/RPC.

## G. Database và schema đề xuất

Migration social phải additive, idempotent và không sửa dữ liệu player/media hiện tại. Các bảng đề xuất:

| Bảng | Mục đích chính |
|---|---|
| `user_profiles` hoặc mở rộng `users` | Display name, avatar, bio, privacy, status |
| `friendships` | Một row cho cặp user chuẩn hóa, trạng thái request |
| `blocks` | Block/mute và thời điểm tạo |
| `listening_rooms` | Room identity, host, visibility, status, version |
| `room_members` | Membership, role, joined/last_seen |
| `room_queue_items` | Queue normalized khi vượt MVP JSONB |
| `room_playback_state` | Track, status, position, server timestamp, version |
| `conversations` | Direct hoặc room conversation |
| `messages` | Server timestamps, `expires_at`, content, report state |
| `reports` | Report user/message/room |
| `admin_audit_logs` | Actor, action, target, metadata, timestamp |

Cần có primary key, foreign key, unique constraint chống duplicate, index cho search/request/expiry, cascade policy rõ ràng và không trả message có `expires_at <= now()`.

## H. Realtime architecture hiện tại

Hiện chưa có realtime transport cho social. Polling room mỗi vài giây là fallback chấp nhận được cho MVP nhưng không đạt yêu cầu low-latency. Kiến trúc nên dùng Supabase Realtime cho broadcast/presence hoặc một WebSocket service có authentication rõ ràng. FastAPI vẫn là nơi quyết định quyền và ghi state; client chỉ nhận event và render.

Các event cần version hoặc idempotency gồm `ROOM_PLAYBACK_UPDATED`, `ROOM_QUEUE_UPDATED`, `ROOM_MEMBER_JOINED`, `ROOM_MEMBER_LEFT`, `FRIEND_REQUEST_CREATED`, `FRIEND_REQUEST_ACCEPTED`, `CHAT_MESSAGE_CREATED`, `CHAT_MESSAGE_DELETED` và `ROOM_CLOSED`.

## I. Các điểm mơ hồ cần chốt

Phần lớn yêu cầu có thể quyết định theo best practice. Chỉ còn hai quyết định thực sự ảnh hưởng implementation:

1. **Đăng ký tài khoản:** tiếp tục mô hình admin cấp tài khoản, hay mở self-registration cho mọi người? Với sản phẩm social, mình khuyên mở registration có rate limit và account status, nhưng vẫn giữ admin approval tùy chọn.
2. **Khi user vào room:** tự động đổi player sang bài của room, hay bắt buộc bấm `Đồng bộ với phòng`? Để bảo vệ người đang nghe, mình khuyên bắt buộc opt-in; sau khi opt-in mới tự resync theo room state.

Các quyết định còn lại có thể mặc định như sau: room private mặc định, host rời thì chuyển cho co-host/người tham gia lâu nhất, admin chỉ đọc chat khi có report hợp lệ, tin nhắn hard-delete khỏi database chính sau 60 phút nhưng không cam kết xóa khỏi backup/provider logs.

## J. Recommended architecture

Giữ modular monolith hiện tại, nhưng chia domain thành `auth`, `profiles`, `social`, `rooms`, `chat`, `notifications`, `admin` và `media`. Player giữ nguyên thành core boundary. Social layer giao tiếp với player qua một adapter opt-in nhỏ; không sửa trực tiếp logic audio.

Supabase PostgreSQL là nguồn sự thật cho user/social/room/chat. Supabase Realtime phù hợp giai đoạn đầu cho broadcast và presence; backend vẫn authorize mọi action. Cleanup message nên chạy bằng scheduled worker/cron độc lập hoặc database RPC có thể retry, không dựa riêng vào việc user mở chat.

## K. API structure đề xuất

| Domain | API chính |
|---|---|
| Auth | `/auth/register`, `/auth/login`, `/auth/logout`, `/auth/refresh`, `/auth/sessions` |
| Profile | `/me`, `/me/profile`, `/me/avatar`, `/me/password`, `/me/privacy` |
| Friends | `/users/search`, `/friends/requests`, `/friends`, `/blocks` |
| Chat | `/conversations`, `/conversations/{id}/messages`, `/messages/{id}` |
| Rooms | `/rooms`, `/rooms/{id}`, `/rooms/{id}/members`, `/rooms/{id}/queue`, `/rooms/{id}/playback` |
| Admin | `/admin/users`, `/admin/rooms`, `/admin/reports`, `/admin/audit`, `/admin/metrics` |

Các API cần error envelope thống nhất với `code`, `message`, `request_id`; pagination cho search/list; server-side authorization; không nhận role/owner/user identity từ client như nguồn sự thật.

## L. WebSocket/event contract

Mỗi event nên có dạng:

```json
{
  "event_id": "uuid",
  "type": "ROOM_PLAYBACK_UPDATED",
  "room_id": "uuid",
  "server_timestamp": "2026-08-27T00:00:00Z",
  "version": 12,
  "payload": {}
}
```

Client dedupe theo `event_id`, bỏ qua `version` cũ, reconnect bằng snapshot mới nhất và không tự áp dụng room state vào player nếu user chưa opt-in. Message event phải có server-created timestamp; client timestamp chỉ dùng cho hiển thị tạm thời nếu cần.

## M. Implementation roadmap

| Phase | Phạm vi | Tiêu chí hoàn tất |
|---|---|---|
| 0 | Baseline player, backup, feature flags | Player/queue regression pass |
| 1 | Auth/profile/security foundation | Profile, avatar validation, password flow, account status |
| 2 | Friends/block/privacy/notifications | Không duplicate, server-side permissions |
| 3 | Room membership/host/queue MVP | Create/join/leave/transfer/authority pass |
| 4 | Realtime room state | Reconnect, stale version, drift correction pass |
| 5 | Chat + 60-minute expiry | Server timestamp, expiry filter, hard-delete cleanup |
| 6 | Admin/moderation/audit | RBAC, reports, room controls, audit pass |
| 7 | Security/performance/E2E | Rate limit, upload tests, concurrency/build/docs pass |

Mỗi phase nên là commit/deploy logic riêng. Không gộp player refactor với social feature. Production rollout nên dùng feature flag để tắt social layer nếu lỗi mà không dừng thư viện nghe nhạc.

## N. Trade-offs

Supabase Realtime giúp giảm lượng hạ tầng phải vận hành nhưng cần thiết kế authorization và subscription cẩn thận. WebSocket riêng cho quyền kiểm soát nhiều hơn nhưng tăng chi phí vận hành và vấn đề reconnect. JSONB queue nhanh cho MVP nhưng normalized queue tốt hơn cho concurrent editing. Token localStorage giữ tương thích nhanh nhưng kém an toàn hơn HttpOnly session. Hard-delete active database đáp ứng yêu cầu ứng dụng nhưng không thể bảo đảm xóa vật lý khỏi provider backup, cache hoặc screenshot.

## O. Kết luận audit

Stack hiện tại đủ để xây social listening platform giai đoạn đầu; chưa cần đổi framework hoặc tách microservices. Ranh giới quan trọng nhất là giữ `PlayerBar` và `playerState` bất biến, đưa room state vào một domain riêng, để backend làm authority và dùng versioned events cho realtime.

Trước khi code tiếp, chỉ cần chốt chính sách registration và hành vi player khi user join room. Sau đó nên triển khai theo roadmap, bắt đầu bằng security/profile foundation rồi friends, room realtime và chat expiry. Không nên triển khai chat và playback synchronization trong cùng một commit lớn.
