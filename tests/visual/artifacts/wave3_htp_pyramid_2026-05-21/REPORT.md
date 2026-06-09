# Wave 3 HTP Pyramid Evidence - 2026-05-21

URL: `http://localhost:3100/boxe?title_code=boxe001&mode=demo&embed=1`

Screenshots:
- `tests/visual/artifacts/wave3_htp_pyramid_2026-05-21/boxe_htp_gate_overview_desktop.png`
- `tests/visual/artifacts/wave3_htp_pyramid_2026-05-21/boxe_htp_card_1_bet_idle.png`
- `tests/visual/artifacts/wave3_htp_pyramid_2026-05-21/boxe_htp_card_2_pick_mid_progress.png`
- `tests/visual/artifacts/wave3_htp_pyramid_2026-05-21/boxe_htp_card_3_collect_mine_reveal.png`
- `tests/visual/artifacts/wave3_htp_pyramid_2026-05-21/boxe_htp_cards_collage_desktop.png`

Directional mockup comparison:
- `boxe2`: idle pyramid grammar preserved in Bet card with active bottom row.
- `boxe4`/`boxe5`: mid-progress safe path appears bottom-to-top in Pick card.
- `boxe6`/`boxe7`: Collect card shows safe path plus fuchsia mine reveal risk.

DOM evidence:
- Pyramid rows/cells rendered top-down from bottom-to-top data model: `[{'dataRow': '3', 'cells': 2}, {'dataRow': '2', 'cells': 3}, {'dataRow': '1', 'cells': 4}, {'dataRow': '0', 'cells': 5}, {'dataRow': '3', 'cells': 2}, {'dataRow': '2', 'cells': 3}, {'dataRow': '1', 'cells': 4}, {'dataRow': '0', 'cells': 5}, {'dataRow': '3', 'cells': 2}, {'dataRow': '2', 'cells': 3}, {'dataRow': '1', 'cells': 4}, {'dataRow': '0', 'cells': 5}]`.
- Safe/mine public assets used: `['/game-assets/boxe/diamond_green_v001.png', '/game-assets/boxe/diamond_green_v001.png', '/game-assets/boxe/mine_fucsia_002.png', '/game-assets/boxe/diamond_green_v001.png', '/game-assets/boxe/diamond_green_v001.png']`.