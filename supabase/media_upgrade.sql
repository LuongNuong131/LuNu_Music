-- LuNu Media upgrade: run once in Supabase SQL Editor.
-- Existing 188 songs keep their current records and URLs.
BEGIN;

ALTER TABLE public.songs ADD COLUMN IF NOT EXISTS media_key text;
ALTER TABLE public.songs ADD COLUMN IF NOT EXISTS source_id text;
ALTER TABLE public.songs ADD COLUMN IF NOT EXISTS cloudinary_public_id text;

CREATE UNIQUE INDEX IF NOT EXISTS songs_source_id_unique
  ON public.songs (source_id)
  WHERE source_id IS NOT NULL;

CREATE UNIQUE INDEX IF NOT EXISTS songs_media_key_unique
  ON public.songs (media_key)
  WHERE media_key IS NOT NULL;

CREATE TABLE IF NOT EXISTS public.cinema_videos (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  media_key text NOT NULL UNIQUE,
  source_id text NOT NULL UNIQUE,
  cloudinary_public_id text NOT NULL,
  title text NOT NULL,
  uploader text NOT NULL DEFAULT 'YouTube',
  url text NOT NULL,
  cover text,
  description text NOT NULL DEFAULT '',
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS cinema_videos_created_at_idx
  ON public.cinema_videos (created_at DESC);

-- Keep this table accessible to the backend service key. If you use RLS with
-- a non-service key, add a policy appropriate to your deployment model.
COMMIT;
