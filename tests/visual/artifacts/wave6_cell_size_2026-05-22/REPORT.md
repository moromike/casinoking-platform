# Wave 6 BOXE Cell Size Evidence

Status: PASS
Date: 2026-05-22
Base URL: `http://127.0.0.1:3102/boxe?title_code=boxe001&mode=demo`

## Screenshots

| Config | Desktop 1365x768 | Mobile 390x844 | Landscape 844x390 |
| --- | --- | --- | --- |
| 4 rows | `boxe_rows4_desktop.png` | `boxe_rows4_mobile.png` | `boxe_rows4_landscape.png` |
| 8 rows | `boxe_rows8_desktop.png` | `boxe_rows8_mobile.png` | `boxe_rows8_landscape.png` |

## Measurement Summary

| Config | Board width | Max row width | Cell size verdict |
| --- | ---: | ---: | --- |
| 4 rows desktop | 622px | 342px | 62x62px in every row |
| 4 rows mobile | 338px | 186px | 34x34px in every row |
| 4 rows landscape | 320px | 176px | 32x32px in every row |
| 8 rows desktop | 622px | 622px | 62x62px in every row |
| 8 rows mobile | 338px | 338px | 34x34px in every row |
| 8 rows landscape | 320px | 320px | 32x32px in every row |

Detailed raw measurements are in `cell-size-measurements.json`.

## Verdict

BOXE pyramid rows no longer stretch short rows to full width. Cell size is fixed per breakpoint, and the board/container responds as one unit. The pyramid shape remains game-specific per BOXE SPEC section 1.7.
