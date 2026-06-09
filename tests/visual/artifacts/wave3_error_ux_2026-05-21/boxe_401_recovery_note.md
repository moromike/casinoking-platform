# Wave 3 BOXE 401 Recovery Evidence - 2026-05-21

URL: `http://localhost:3200/boxe?title_code=boxe001&mode=demo&embed=1`

Scenario:
- Browser starts with cached `casinoking.access_token=expired-token`.
- First `POST /games/boxe/start` returns `401 Invalid bearer token`.
- BOXE clears cached auth, calls `POST /auth/demo`, then retries the same action once.

Observed route evidence:
- Start authorization sequence: `['Bearer expired-token', 'Bearer fresh-token']`.
- Start idempotency keys: `['43fc675b-7cdc-48ac-aace-62157b66c47f', '43fc675b-7cdc-48ac-aace-62157b66c47f']`.
- Same idempotency key reused: `True`.
- Error dialog count after recovery: `0`.
- Stored token after recovery: `fresh-token`.

Verdict: silent demo auth recovery passed; backend raw `Invalid bearer token` was not rendered.

Screenshot: `tests/visual/artifacts/wave3_error_ux_2026-05-21/boxe_401_recovery_after_start.png`.