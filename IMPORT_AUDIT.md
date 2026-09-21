# Import flow audit — LuNu Music

## User-requested flow

The stable song-import flow is: search direct-download providers by title, show licensed results, select one, enter the final song title and artist in the web UI, send that metadata with the provider/source ID, download the audio over HTTPS, normalize it with FFmpeg, upload it to Cloudinary, save the returned URL plus metadata in Supabase, and refresh the library after the background job completes. YouTube remains isolated to the legacy/Cinema metadata path and is not the default MP3 source.

## Current blockers

| Layer | Current behavior | Impact | Fix |
|---|---|---|---|
| Admin UI | Search results were YouTube-only | Render/office networks can block YouTube playback/download | Search Jamendo and Internet Archive direct-download results |
| Frontend API | Import payload used a YouTube-only `video_id` contract | Non-YouTube sources could not be imported | Send `{ source_id, provider, title, artist, cover, lyrics }` |
| Backend contract | `AddSongRequest` accepted only `video_id` | Provider/source could not be validated | Validate provider and source ID with Pydantic |
| Download worker | `process_and_upload_song` always called yt-dlp | Every song import inherited YouTube 429/403 failures | Resolve exact provider ID and download only when provider permits it |
| Job lifecycle | Background task returns only a generic queued message; frontend refreshes immediately | Library refresh happens before upload/insert finishes and gives no completion status | Add in-memory job registry, `job_id`, status endpoint and frontend polling |
| Cloudinary | Upload uses a filename-derived public ID with overwrite behavior | Duplicate titles can overwrite or produce hard-to-debug collisions | Use deterministic video ID public ID and return secure URL |
| Supabase | Insert happens only inside a background task with no job result exposed | UI cannot distinguish completed upload from failed upload | Persist status in job registry and return structured error |
| Validation | YouTube search result is used without explicit selected metadata validation | Empty/custom malformed title or artist can enter the database | Validate/normalize title and artist with Pydantic |

## Evidence from Render logs

The supplied logs show YouTube search succeeds with HTTP 200, but every media extraction attempt from Render receives HTTP 429/403. This is a provider/IP limitation, not a missing retry profile. The new song path no longer depends on that extractor; `/api/songs/search_youtube` is retained for legacy/Cinema use, while `/api/songs/search` returns only direct-download provider results.

## Implementation target

The new contract will return `202 Accepted` with a `job_id` and `status: queued`. The UI will display the selected video, collect the final title/artist, then poll `/api/songs/import-jobs/{job_id}` until `completed` or `failed`. On completion it will refresh `/api/songs`, making the new item visible with the exact title and artist entered by the user.
