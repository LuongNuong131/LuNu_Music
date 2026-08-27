# Flagship redesign QA notes — 2026-08-27

## Build

`npm run build` passed after Aurora theme store, synced lyrics service, immersive Now Playing, waveform, modal, toast, Cinema and Playlist TransitionGroup changes. `python3 -m py_compile backend/main.py` and `git diff --check` passed.

## Runtime smoke test

The local app rendered Home successfully under the existing demo session. App shell, grouped navigation, utility bar, Home greeting, recommendation panel and library rendered without visible runtime error. Selecting a recommendation incremented listening history and surfaced the floating player with current artwork, play controls and waveform region. This validated the existing playback activation path while the new presentation layer was mounted.

The browser viewport used for this smoke test was desktop-sized. Responsive behavior is covered by CSS breakpoints and reduced-motion rules; mobile-specific visual inspection remains a follow-up item.

## Known scope boundary

The canvas extractor uses a same-origin/CORS-safe fallback path: remote cover images that block pixel reads fall back to the default palette rather than failing the UI. Word highlighting is an estimated reveal derived from line timing because the current data contract stores line-level LRC timestamps, not word-level timestamps.

## Active playback visual check

Sau khi chọn track đầu tiên, card chuyển sang trạng thái active và nút hiển thị pause; listening history tăng; floating player hiển thị artwork, metadata và progress time. Home shell giữ được layout Aurora/acrylic sau khi playback state thay đổi.

## Immersive Now Playing check

Fullscreen Now Playing overlay opened from `.now-track` with the active cover, vinyl stage, equalizer, metadata, progress scrubber and transport controls. The overlay uses the dark immersive surface and closes through the labeled close control. The browser text layer showed no runtime error; the current demo song had no synced lyrics data, so the plain lyrics fallback path remained available.

## Lyrics mode check

Lyrics mode toggled successfully inside the fullscreen overlay and displayed the centered immersive lyric canvas with the sing-along header, timing surface and transport controls. The local browser console also reported the pre-existing expected backend connection warning at `http://localhost:8000/api` because the backend was not running in this sandbox; no new Vue template/runtime error was introduced by the redesign.
