-- LuNu Music: database-backed playlists.
-- Run once in the Supabase SQL Editor before deploying the backend.
BEGIN;
CREATE TABLE IF NOT EXISTS public.user_playlists (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
  name text NOT NULL CHECK (char_length(name) BETWEEN 1 AND 80),
  description text NOT NULL DEFAULT '' CHECK (char_length(description) <= 160),
  song_ids jsonb NOT NULL DEFAULT '[]'::jsonb CHECK (jsonb_typeof(song_ids) = 'array'),
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS user_playlists_user_updated_idx
  ON public.user_playlists (user_id, updated_at DESC);
COMMIT;
