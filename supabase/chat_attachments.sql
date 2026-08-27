-- LuNu Chat attachments: run once after supabase/chat_messages.sql.
-- Additive migration; messages still hard-delete after their individual expires_at.
BEGIN;

ALTER TABLE public.chat_messages ADD COLUMN IF NOT EXISTS attachment_url text;
ALTER TABLE public.chat_messages ADD COLUMN IF NOT EXISTS attachment_public_id text;
ALTER TABLE public.chat_messages ADD COLUMN IF NOT EXISTS attachment_resource_type text CHECK (attachment_resource_type IN ('image', 'raw'));
ALTER TABLE public.chat_messages ADD COLUMN IF NOT EXISTS attachment_name text;
ALTER TABLE public.chat_messages ADD COLUMN IF NOT EXISTS attachment_mime text;
ALTER TABLE public.chat_messages ADD COLUMN IF NOT EXISTS attachment_size_bytes bigint CHECK (attachment_size_bytes IS NULL OR attachment_size_bytes > 0);

CREATE INDEX IF NOT EXISTS chat_messages_attachment_idx
  ON public.chat_messages (attachment_public_id)
  WHERE attachment_public_id IS NOT NULL;

COMMIT;
