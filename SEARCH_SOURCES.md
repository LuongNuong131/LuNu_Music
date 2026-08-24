# Search fallback sources

The search fallback investigation consulted the following public documentation:

1. Piped API documentation: https://docs.piped.video/docs/api-documentation/
   It documents unauthenticated API endpoints and states that public API instances should be selected dynamically from the Piped instance list.

2. Piped public instance list: https://github.com/TeamPiped/Piped/wiki/Instances/408b500c3e205e95a197d42b33345c1f207ba62b
   It lists public API hostnames, but live probes from the sandbox returned 502/522/connection failures for the tested instances, so no public Piped instance was hardcoded into production.

3. Invidious public instance guidance: https://docs.invidious.io/instances/
   It warns that public instances are short-lived/unreliable and that unlisted instances should be treated as untrustworthy; tested instances were unavailable or endpoint-disabled, so they were not integrated.

Local evidence showed yt-dlp succeeds for `cao ốc 20` in the sandbox, while Render’s YouTube egress can return an HTTP 200 with irrelevant or empty results. YouTube Music structured search and accent-stripped query variants return music-relevant results intermittently, so the backend now tries multiple music-focused variants and retains the existing safe fallback chain.
