-- LuNu Chat: run once in Supabase SQL Editor.
-- Additive migration; does not alter songs, Cinema, player or queue.
BEGIN;

CREATE TABLE IF NOT EXISTS public.conversations (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  kind text NOT NULL CHECK (kind IN ('direct', 'room')),
  room_id uuid REFERENCES public.listening_rooms(id) ON DELETE CASCADE,
  direct_key text UNIQUE,
  created_by uuid NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  CHECK ((kind = 'room' AND room_id IS NOT NULL AND direct_key IS NULL) OR (kind = 'direct' AND room_id IS NULL AND direct_key IS NOT NULL))
);

CREATE TABLE IF NOT EXISTS public.conversation_members (
  conversation_id uuid NOT NULL REFERENCES public.conversations(id) ON DELETE CASCADE,
  user_id uuid NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
  joined_at timestamptz NOT NULL DEFAULT now(),
  last_read_at timestamptz,
  PRIMARY KEY (conversation_id, user_id)
);

CREATE TABLE IF NOT EXISTS public.chat_messages (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  conversation_id uuid NOT NULL REFERENCES public.conversations(id) ON DELETE CASCADE,
  sender_id uuid NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
  body text NOT NULL CHECK (char_length(btrim(body)) BETWEEN 1 AND 2000),
  created_at timestamptz NOT NULL DEFAULT now(),
  expires_at timestamptz NOT NULL DEFAULT (now() + interval '60 minutes'),
  deleted_at timestamptz,
  deleted_by uuid REFERENCES public.users(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS public.chat_reports (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  message_id uuid NOT NULL REFERENCES public.chat_messages(id) ON DELETE CASCADE,
  reporter_id uuid NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
  reason text NOT NULL CHECK (char_length(btrim(reason)) BETWEEN 1 AND 500),
  status text NOT NULL DEFAULT 'open' CHECK (status IN ('open', 'reviewed', 'dismissed')),
  created_at timestamptz NOT NULL DEFAULT now(),
  reviewed_by uuid REFERENCES public.users(id) ON DELETE SET NULL,
  reviewed_at timestamptz,
  UNIQUE (message_id, reporter_id)
);

CREATE INDEX IF NOT EXISTS conversations_room_idx ON public.conversations (room_id) WHERE room_id IS NOT NULL;
CREATE UNIQUE INDEX IF NOT EXISTS conversations_room_unique ON public.conversations (room_id) WHERE room_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS conversations_updated_idx ON public.conversations (updated_at DESC);
CREATE INDEX IF NOT EXISTS conversation_members_user_idx ON public.conversation_members (user_id, joined_at DESC);
CREATE INDEX IF NOT EXISTS chat_messages_conversation_idx ON public.chat_messages (conversation_id, created_at DESC);
CREATE INDEX IF NOT EXISTS chat_messages_expiry_idx ON public.chat_messages (expires_at);
CREATE INDEX IF NOT EXISTS chat_reports_status_idx ON public.chat_reports (status, created_at DESC);

COMMIT;
