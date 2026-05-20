# Wave 3 Error UX Evidence - 2026-05-21

URL: `http://localhost:3200/boxe?title_code=boxe001&mode=demo&embed=1`

Screenshots:
- Runtime 5xx dialog: `tests/visual/artifacts/wave3_error_ux_2026-05-21/boxe_runtime_error_dialog.png`.
- Action 422 dialog: `tests/visual/artifacts/wave3_error_ux_2026-05-21/boxe_action_error_dialog.png`.
- 401 recovery success state: `tests/visual/artifacts/wave3_error_ux_2026-05-21/boxe_401_recovery_after_start.png`.

Route/DOM evidence:
- 401 recovery note: `tests/visual/artifacts/wave3_error_ux_2026-05-21/boxe_401_recovery_note.md`.

Verdict:
- BOXE action/runtime errors use the shared `GameActionError` overlay.
- Backend raw strings are mapped to player-facing copy.
- Demo `401 Invalid bearer token` recovers silently with one retry.