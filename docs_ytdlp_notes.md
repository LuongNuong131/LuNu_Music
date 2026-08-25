# YouTube extraction notes

- Source: https://github.com/yt-dlp/yt-dlp/wiki/ejs — yt-dlp states that YouTube downloads need an external JavaScript runtime for JavaScript challenges. Supported runtime guidance lists Deno as recommended and Node >=22 as the minimum supported Node version. The guide also describes yt-dlp-ejs and remote components such as `ejs:github`.
- Source: https://github.com/yt-dlp/ejs — yt-dlp-ejs documents runtime requirements: Node >=22 and Deno >=2.3 for the supported EJS setup.
- Source: https://github.com/yt-dlp/yt-dlp/wiki/FAQ — yt-dlp explains that HTTP 429/anti-bot blocks may require fresh browser cookies and a matching user-agent; it also notes that separate audio/video streams may require FFmpeg.
- Application implication: Render must build `backend/Dockerfile` with Node 22. If YouTube returns only images or a challenge for a Render IP, changing format selectors cannot create unavailable audio/video streams; the UI should show a clear state rather than retry silently.
