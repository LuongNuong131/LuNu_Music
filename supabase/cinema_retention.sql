-- LuNu Cinema retention modes: run once after media_upgrade.sql.
-- permanent  = keep the Cloudinary asset until an admin deletes it.
-- temporary  = keep it only until expires_at, then cleanup removes Cloudinary first and the row second.
BEGIN;

ALTER TABLE public.cinema_videos
  ADD COLUMN IF NOT EXISTS retention_mode text NOT NULL DEFAULT 'permanent';

ALTER TABLE public.cinema_videos
  ADD COLUMN IF NOT EXISTS expires_at timestamptz;

UPDATE public.cinema_videos
SET retention_mode = 'permanent'
WHERE retention_mode IS NULL OR retention_mode NOT IN ('permanent', 'temporary');

ALTER TABLE public.cinema_videos
  DROP CONSTRAINT IF EXISTS cinema_videos_retention_mode_check;

ALTER TABLE public.cinema_videos
  ADD CONSTRAINT cinema_videos_retention_mode_check
  CHECK (retention_mode IN ('permanent', 'temporary'));

CREATE INDEX IF NOT EXISTS cinema_videos_expiration_idx
  ON public.cinema_videos (expires_at)
  WHERE retention_mode = 'temporary' AND expires_at IS NOT NULL;

COMMIT;
