# Import flow audit — LuNu Music

## User-requested flow

The intended flow is: search YouTube by title, show similar videos, select one, enter the final song title and artist in the web UI, send that metadata with the selected video ID, download the selected video as MP3 with yt-dlp/FFmpeg, upload the MP3 to Cloudinary, save the returned Cloudinary URL plus the user-entered metadata in Supabase, and refresh the library after the background job actually completes.

## Current blockers

| Layer | Current behavior | Impact | Fix |
|---|---|---|---|
| Admin UI | `DiscordBotSearch.vue` sends only `video.id` when clicking “Tải bài này” | There is no title/artist editing step; backend must guess metadata from YouTube | Add selected-video form with editable title and artist |
| Frontend API | `addSong(videoId)` serializes only `{ video_id }` | User-entered metadata cannot reach Render | Send `{ video_id, title, artist, cover, lyrics }` |
| Backend contract | `AddSongRequest` accepts only `video_id` | Request schema rejects/ignores custom metadata | Extend Pydantic model and validate fields |
| Download worker | `process_and_upload_song(video_id)` always uses `info.title` and `info.uploader` | Saved metadata is not the metadata chosen by the user | Pass validated metadata into worker and use it as source of truth |
| Job lifecycle | Background task returns only a generic queued message; frontend refreshes immediately | Library refresh happens before upload/insert finishes and gives no completion status | Add in-memory job registry, `job_id`, status endpoint and frontend polling |
| Cloudinary | Upload uses a filename-derived public ID with overwrite behavior | Duplicate titles can overwrite or produce hard-to-debug collisions | Use deterministic video ID public ID and return secure URL |
| Supabase | Insert happens only inside a background task with no job result exposed | UI cannot distinguish completed upload from failed upload | Persist status in job registry and return structured error |
| Validation | YouTube search result is used without explicit selected metadata validation | Empty/custom malformed title or artist can enter the database | Validate/normalize title and artist with Pydantic |

## Evidence from Render logs

The attached logs show YouTube search succeeds with HTTP 200, while previous CORS problems have already been fixed. The current code path after the search still calls the old add endpoint with only a video ID; no successful `/api/songs/add` completion is present in the supplied logs. This is consistent with the missing metadata form and missing completion/status flow rather than a search failure.

## Implementation target

The new contract will return `202 Accepted` with a `job_id` and `status: queued`. The UI will display the selected video, collect the final title/artist, then poll `/api/songs/import-jobs/{job_id}` until `completed` or `failed`. On completion it will refresh `/api/songs`, making the new item visible with the exact title and artist entered by the user.
