-- LuNu user profile foundation: run once in Supabase SQL Editor.
-- Additive migration; existing authentication and media records remain intact.
BEGIN;

ALTER TABLE public.users ADD COLUMN IF NOT EXISTS display_name text;
ALTER TABLE public.users ADD COLUMN IF NOT EXISTS avatar_url text;
ALTER TABLE public.users ADD COLUMN IF NOT EXISTS bio text;
ALTER TABLE public.users ADD COLUMN IF NOT EXISTS updated_at timestamptz NOT NULL DEFAULT now();

UPDATE public.users
SET display_name = COALESCE(NULLIF(display_name, ''), username)
WHERE display_name IS NULL OR display_name = '';

CREATE INDEX IF NOT EXISTS users_display_name_idx
  ON public.users (lower(display_name));

COMMIT;
