-- LuNu social foundation: run once in Supabase SQL Editor.
-- Additive migration; does not alter songs, Cinema, player or queue.
BEGIN;

CREATE TABLE IF NOT EXISTS public.friendships (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  requester_id uuid NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
  addressee_id uuid NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
  pair_key text GENERATED ALWAYS AS (
    least(requester_id::text, addressee_id::text) || ':' || greatest(requester_id::text, addressee_id::text)
  ) STORED UNIQUE,
  status text NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'accepted', 'rejected', 'cancelled')),
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  accepted_at timestamptz,
  CHECK (requester_id <> addressee_id)
);

CREATE TABLE IF NOT EXISTS public.blocks (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  blocker_id uuid NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
  blocked_id uuid NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (blocker_id, blocked_id),
  CHECK (blocker_id <> blocked_id)
);

CREATE INDEX IF NOT EXISTS friendships_requester_idx ON public.friendships (requester_id, status, updated_at DESC);
CREATE INDEX IF NOT EXISTS friendships_addressee_idx ON public.friendships (addressee_id, status, updated_at DESC);
CREATE INDEX IF NOT EXISTS blocks_blocker_idx ON public.blocks (blocker_id, blocked_id);
CREATE INDEX IF NOT EXISTS blocks_blocked_idx ON public.blocks (blocked_id, blocker_id);

COMMIT;
