# LuNu Music + LuNu Cinema media upgrade

## Root causes fixed

Render was using a single `bestaudio/best` selector. YouTube sometimes exposed only image formats or incomplete formats after challenge checks, so yt-dlp raised `Requested format is not available`. The backend now uses Node.js plus `yt-dlp-ejs`, multiple player clients, audio-first selectors, FFmpeg conversion, retries, and a clear error when a source exposes no audio stream. For protected videos, Render can receive an authorized Netscape cookies file through `YOUTUBE_COOKIES_B64`; never commit or share cookies.

The 188-song import also sent `legacyId`, which does not exist in the current `songs` schema. The backend now strips unsupported legacy fields before insertion.

## Required Supabase action

Run `supabase/media_upgrade.sql` once in the Supabase SQL Editor. It adds `media_key`, `source_id`, and `cloudinary_public_id` to `songs`, creates uniqueness indexes, and creates `cinema_videos`.

Do not click the 188-song restore action until this migration has completed. After migration, use the admin page to restore the catalog. The legacy URLs are preserved; new songs receive keys such as `19925082026`, and Cinema videos receive keys such as `VD0125082026`.

## Render action

Redeploy the backend from the latest `master` commit. Ensure `ffmpeg` and `nodejs` are installed through `backend/Dockerfile`; requirements now include `yt-dlp>=2026.8.19` and `yt-dlp-ejs>=0.8.0`. If YouTube search should be deterministic, configure `YOUTUBE_API_KEY` with YouTube Data API v3. If a selected video still requires bot verification, configure `YOUTUBE_COOKIES_B64` from an authorized `cookies.txt` export.

## User flow

For music, an admin searches YouTube, selects a result, edits title and artist, and submits. Render downloads audio, converts it to MP3, uploads it to `lunu_music/<media_key>` on Cloudinary, and stores the Cloudinary URL plus source ID and media key in Supabase. For Cinema, the admin opens the LuNu Cinema tab, searches, selects a video, edits title/channel/description, and submits. Render downloads MP4, uploads it to `lunu_cinema/<media_key>`, and stores the metadata in `cinema_videos`.

Deleting a song or Cinema video first deletes the Cloudinary asset and only then deletes the Supabase row. If Cloudinary deletion fails, the database row is retained so the system does not silently create an orphaned asset.

## Verification

The media regression test passed for ID generation, legacy field stripping, yt-dlp options, and Cloudinary public-ID parsing. The Vite production build, Python compilation, and `git diff --check` passed. Docker was not available in the sandbox, so the final Render image must be validated by its next deployment.
