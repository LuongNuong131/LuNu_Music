-- LuNu Music: media proposals + notifications
-- Run once in Supabase SQL Editor after confirming public.users.id is uuid.
BEGIN;

CREATE TABLE IF NOT EXISTS public.media_proposals (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  kind text NOT NULL CHECK (kind IN ('song', 'video')),
  source_id text NOT NULL,
  title text NOT NULL,
  artist text NOT NULL DEFAULT '',
  uploader text NOT NULL DEFAULT 'YouTube',
  cover text NOT NULL DEFAULT '',
  description text NOT NULL DEFAULT '',
  requested_by uuid NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
  requested_by_username text NOT NULL DEFAULT '',
  status text NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'processing', 'approved', 'rejected', 'failed')),
  job_id uuid,
  media_key text,
  file_size_bytes bigint,
  rejection_reason text NOT NULL DEFAULT '',
  reviewed_by uuid REFERENCES public.users(id) ON DELETE SET NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  reviewed_at timestamptz,
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS media_proposals_status_idx ON public.media_proposals (status, created_at DESC);
CREATE INDEX IF NOT EXISTS media_proposals_requester_idx ON public.media_proposals (requested_by, created_at DESC);
CREATE UNIQUE INDEX IF NOT EXISTS media_proposals_active_source_unique
  ON public.media_proposals (source_id)
  WHERE status IN ('pending', 'processing');

CREATE TABLE IF NOT EXISTS public.notifications (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
  title text NOT NULL,
  body text NOT NULL DEFAULT '',
  kind text NOT NULL DEFAULT 'system',
  link text NOT NULL DEFAULT '',
  is_read boolean NOT NULL DEFAULT false,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS notifications_user_created_idx ON public.notifications (user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS notifications_unread_idx ON public.notifications (user_id, is_read) WHERE is_read = false;

COMMIT;
