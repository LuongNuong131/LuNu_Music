# AI / Gemini review — 2026-08-28

## Findings from official docs and user attachments

- `gemini-3.7-flash` is a valid GA model ID in the supplied current documentation.
- Gemini Interactions API supports structured output through `response_format` with `type: text`, `mime_type: application/json`, and a JSON schema.
- Gemini 3.7 Flash supports `generation_config.thinking_level`; use `low` for latency-sensitive chat and avoid deprecated sampling parameters such as `temperature`, `top_p`, `top_k`, and `candidate_count`.
- For multi-turn interactions, the current migration guidance recommends server-side `previous_interaction_id` rather than rebuilding a long conversation manually.
- Rate limits are evaluated per project across RPM, TPM, and RPD, not multiplied by the number of API keys. Ten keys are useful for fallback/credential rotation but do not create ten times the quota.
- Current AI implementation uses structured output and catalog validation, but should add thinking level, previous interaction continuity, bounded catalog context, explicit interaction ID return, better error taxonomy, and clearer key/quota observability.

## Security note

The supplied AI Studio HTML contains a key-looking `AIza...` value in page configuration. It was not copied into the project or used. If that value belongs to the user, it should be revoked and regenerated immediately; secrets must remain in the backend environment only.

## Source URLs

- https://ai.google.dev/gemini-api/docs/latest-model
- https://ai.google.dev/gemini-api/docs/structured-output
- https://ai.google.dev/gemini-api/docs/rate-limits
