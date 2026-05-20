# Wave 2 Visual Uniformity Evidence

Generated against frontend port 3100 with deterministic Playwright API mocks.
Each PNG is a side-by-side composite: Mines reference on the left, BOXE current
on the right.

| State | Viewport | Artifact | Verdict |
| --- | --- | --- | --- |
| idle_desktop | 1365x768 | `tests/visual/artifacts/wave2_visual_uniformity_2026-05-20/idle_desktop.png` | Pass with listed residuals |
| active_desktop | 1365x768 | `tests/visual/artifacts/wave2_visual_uniformity_2026-05-20/active_desktop.png` | Pass with listed residuals |
| win_desktop | 1365x768 | `tests/visual/artifacts/wave2_visual_uniformity_2026-05-20/win_desktop.png` | Pass with listed residuals |
| idle_mobile_portrait | 390x844 | `tests/visual/artifacts/wave2_visual_uniformity_2026-05-20/idle_mobile_portrait.png` | Pass with listed residuals |
| active_mobile_portrait | 390x844 | `tests/visual/artifacts/wave2_visual_uniformity_2026-05-20/active_mobile_portrait.png` | Pass with listed residuals |
| landscape_rotation | 844x390 | `tests/visual/artifacts/wave2_visual_uniformity_2026-05-20/landscape_rotation.png` | Pass with listed residuals |

## Residual Pixel Differences

| Area | Verdict | Reason |
| --- | --- | --- |
| Board shape/content | Justified | BOXE board is game-specific and remains WP-G ownership. WP-V does not change `.boxe-pyramid-*`. |
| Settings labels/options | Justified | BOXE has rows/difficulty while Mines has grid size/mines; chip primitive, spacing, and active state now match. |
| Payout ladder values/count | Justified | Multipliers are BOXE-specific runtime payload and ladder styling is WP-G ownership. |
| Game title text | Justified | Product title differs by game; shell/title scale and close affordance are shared. |
| Landscape gate copy | Justified | Existing game copy differs by locale/source; rotation affordance and placement are shared. |
| Rail tool cluster | Fixed | BOXE now renders info, Rome clock, audio trigger, and DEMO/REAL/BONUS mode badge in the Mines rail pattern. |
| BOXE-only RTP/title code/status bar | Fixed | `98% RTP`, `title_code` eyebrow, and round status footer were removed. |

Mines source files were not modified; Mines baseline remains the reference.
