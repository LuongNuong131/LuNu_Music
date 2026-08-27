-- LuNu Listening Rooms: run once in Supabase SQL Editor.
-- This migration is additive and does not alter songs, player state or Cinema.
BEGIN;

CREATE TABLE IF NOT EXISTS public.listening_rooms (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  name text NOT NULL CHECK (char_length(name) BETWEEN 1 AND 120),
  invite_code text NOT NULL UNIQUE,
  host_id uuid NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
  visibility text NOT NULL DEFAULT 'private' CHECK (visibility IN ('private', 'public')),
  max_members integer NOT NULL DEFAULT 8 CHECK (max_members BETWEEN 2 AND 50),
  status text NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'closed')),
  current_song jsonb,
  queue jsonb NOT NULL DEFAULT '[]'::jsonb,
  is_playing boolean NOT NULL DEFAULT false,
  position_seconds numeric NOT NULL DEFAULT 0,
  state_version bigint NOT NULL DEFAULT 0,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS public.room_members (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  room_id uuid NOT NULL REFERENCES public.listening_rooms(id) ON DELETE CASCADE,
  user_id uuid NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
  role text NOT NULL DEFAULT 'member' CHECK (role IN ('host', 'co_host', 'member', 'listener')),
  joined_at timestamptz NOT NULL DEFAULT now(),
  last_seen_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (room_id, user_id)
);

CREATE INDEX IF NOT EXISTS listening_rooms_status_idx
  ON public.listening_rooms (status, updated_at DESC);
CREATE INDEX IF NOT EXISTS listening_rooms_host_idx
  ON public.listening_rooms (host_id, status);
CREATE INDEX IF NOT EXISTS room_members_user_idx
  ON public.room_members (user_id, last_seen_at DESC);
CREATE INDEX IF NOT EXISTS room_members_room_idx
  ON public.room_members (room_id, joined_at ASC);

COMMIT;
