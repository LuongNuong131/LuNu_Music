# UI smoke test checkpoint

Local Vite dev server opened at `http://localhost:5173/login` and rendered the redesigned login screen correctly. The page showed the LuNu brand, premium dark/glass layout, Vietnamese copy, account/password fields, and submit button. Browser console had no runtime output or exceptions at the checkpoint.

Authenticated preview session rendered the redesigned dashboard successfully: premium hero card, sidebar navigation, admin/lyrics tabs, empty-library state, and fixed player all appeared. With the backend intentionally not running in the local smoke test, the UI correctly displayed an audio error status instead of throwing a console exception or becoming blank.

Lyrics Lab also rendered correctly. Console showed only the expected `Failed to fetch` from `GET http://localhost:8000/api/songs` because no local backend was started; there was no Vue render exception. This is an environment connectivity warning, and the UI presented a graceful empty state.
