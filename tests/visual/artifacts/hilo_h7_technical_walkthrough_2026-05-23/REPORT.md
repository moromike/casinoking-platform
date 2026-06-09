# HI-LO H7 Technical Walkthrough Evidence - 2026-05-23

This is a Codex technical/browser pre-check. It is not Michele's product-owner approval.

Screenshots:
- `tests/visual/artifacts/hilo_h7_technical_walkthrough_2026-05-23/01_demo_idle_desktop.png`
- `tests/visual/artifacts/hilo_h7_technical_walkthrough_2026-05-23/02_info_modal_desktop.png`
- `tests/visual/artifacts/hilo_h7_technical_walkthrough_2026-05-23/03_demo_after_bet_desktop.png`
- `tests/visual/artifacts/hilo_h7_technical_walkthrough_2026-05-23/04_real_table_gate_desktop.png`
- `tests/visual/artifacts/hilo_h7_technical_walkthrough_2026-05-23/05_admin_engine_hi_lo.png`
- `tests/visual/artifacts/hilo_h7_technical_walkthrough_2026-05-23/06_admin_title_detail_hi_lo.png`
- `tests/visual/artifacts/hilo_h7_technical_walkthrough_2026-05-23/07_account_history.png`
- `tests/visual/artifacts/hilo_h7_technical_walkthrough_2026-05-23/08_demo_idle_mobile_portrait.png`
- `tests/visual/artifacts/hilo_h7_technical_walkthrough_2026-05-23/09_demo_idle_landscape_short.png`

Notes:
- No horizontal overflow detected in captured HI-LO surfaces.
- Real route rendered GameTableBalanceGate after a demo active round; wallet-source resume isolation passed.

Metrics:

```json
[
  {
    "label": "demo_idle_desktop",
    "url": "http://127.0.0.1:3000/hi-lo?title_code=hilo001&mode=demo",
    "viewport": {
      "width": 1365,
      "height": 768
    },
    "document": {
      "scrollWidth": 1365,
      "scrollHeight": 768,
      "clientWidth": 1365,
      "clientHeight": 768,
      "bodyScrollWidth": 1365,
      "bodyScrollHeight": 768,
      "hasHorizontalOverflow": false,
      "hasVerticalOverflow": false
    },
    "productShell": {
      "selector": ".hi-lo-product-shell",
      "x": 103,
      "y": 12,
      "width": 1160,
      "height": 744,
      "scrollWidth": 1158,
      "scrollHeight": 742,
      "clientWidth": 1158,
      "clientHeight": 742,
      "overflowX": "hidden",
      "overflowY": "hidden",
      "hasHorizontalOverflow": false,
      "hasVerticalOverflow": false
    },
    "gameplay": {
      "selector": "[data-testid='hi-lo-gameplay']",
      "x": 122,
      "y": 31,
      "width": 1122,
      "height": 706,
      "scrollWidth": 1122,
      "scrollHeight": 706,
      "clientWidth": 1122,
      "clientHeight": 706,
      "overflowX": "hidden",
      "overflowY": "hidden",
      "hasHorizontalOverflow": false,
      "hasVerticalOverflow": false
    },
    "stage": {
      "selector": ".hi-lo-stage",
      "x": 500,
      "y": 31,
      "width": 744,
      "height": 706,
      "scrollWidth": 742,
      "scrollHeight": 704,
      "clientWidth": 742,
      "clientHeight": 704,
      "overflowX": "hidden",
      "overflowY": "hidden",
      "hasHorizontalOverflow": false,
      "hasVerticalOverflow": false
    },
    "controlRail": {
      "selector": ".hi-lo-control-rail",
      "x": 122,
      "y": 31,
      "width": 360,
      "height": 706,
      "scrollWidth": 358,
      "scrollHeight": 704,
      "clientWidth": 358,
      "clientHeight": 704,
      "overflowX": "hidden",
      "overflowY": "hidden",
      "hasHorizontalOverflow": false,
      "hasVerticalOverflow": false
    },
    "tableGate": null,
    "adminShell": null
  },
  {
    "label": "info_modal_desktop",
    "url": "http://127.0.0.1:3000/hi-lo?title_code=hilo001&mode=demo",
    "viewport": {
      "width": 1365,
      "height": 768
    },
    "document": {
      "scrollWidth": 1365,
      "scrollHeight": 768,
      "clientWidth": 1365,
      "clientHeight": 768,
      "bodyScrollWidth": 1365,
      "bodyScrollHeight": 768,
      "hasHorizontalOverflow": false,
      "hasVerticalOverflow": false
    },
    "productShell": {
      "selector": ".hi-lo-product-shell",
      "x": 103,
      "y": 12,
      "width": 1160,
      "height": 744,
      "scrollWidth": 1158,
      "scrollHeight": 742,
      "clientWidth": 1158,
      "clientHeight": 742,
      "overflowX": "hidden",
      "overflowY": "hidden",
      "hasHorizontalOverflow": false,
      "hasVerticalOverflow": false
    },
    "gameplay": {
      "selector": "[data-testid='hi-lo-gameplay']",
      "x": 122,
      "y": 31,
      "width": 1122,
      "height": 706,
      "scrollWidth": 1122,
      "scrollHeight": 706,
      "clientWidth": 1122,
      "clientHeight": 706,
      "overflowX": "hidden",
      "overflowY": "hidden",
      "hasHorizontalOverflow": false,
      "hasVerticalOverflow": false
    },
    "stage": {
      "selector": ".hi-lo-stage",
      "x": 500,
      "y": 31,
      "width": 744,
      "height": 706,
      "scrollWidth": 742,
      "scrollHeight": 704,
      "clientWidth": 742,
      "clientHeight": 704,
      "overflowX": "hidden",
      "overflowY": "hidden",
      "hasHorizontalOverflow": false,
      "hasVerticalOverflow": false
    },
    "controlRail": {
      "selector": ".hi-lo-control-rail",
      "x": 122,
      "y": 31,
      "width": 360,
      "height": 706,
      "scrollWidth": 358,
      "scrollHeight": 704,
      "clientWidth": 358,
      "clientHeight": 704,
      "overflowX": "hidden",
      "overflowY": "hidden",
      "hasHorizontalOverflow": false,
      "hasVerticalOverflow": false
    },
    "tableGate": null,
    "adminShell": null
  },
  {
    "label": "demo_after_bet_desktop",
    "url": "http://127.0.0.1:3000/hi-lo?title_code=hilo001&mode=demo",
    "viewport": {
      "width": 1365,
      "height": 768
    },
    "document": {
      "scrollWidth": 1365,
      "scrollHeight": 768,
      "clientWidth": 1365,
      "clientHeight": 768,
      "bodyScrollWidth": 1365,
      "bodyScrollHeight": 768,
      "hasHorizontalOverflow": false,
      "hasVerticalOverflow": false
    },
    "productShell": {
      "selector": ".hi-lo-product-shell",
      "x": 103,
      "y": 12,
      "width": 1160,
      "height": 744,
      "scrollWidth": 1158,
      "scrollHeight": 742,
      "clientWidth": 1158,
      "clientHeight": 742,
      "overflowX": "hidden",
      "overflowY": "hidden",
      "hasHorizontalOverflow": false,
      "hasVerticalOverflow": false
    },
    "gameplay": {
      "selector": "[data-testid='hi-lo-gameplay']",
      "x": 122,
      "y": 31,
      "width": 1122,
      "height": 706,
      "scrollWidth": 1122,
      "scrollHeight": 706,
      "clientWidth": 1122,
      "clientHeight": 706,
      "overflowX": "hidden",
      "overflowY": "hidden",
      "hasHorizontalOverflow": false,
      "hasVerticalOverflow": false
    },
    "stage": {
      "selector": ".hi-lo-stage",
      "x": 500,
      "y": 31,
      "width": 744,
      "height": 706,
      "scrollWidth": 742,
      "scrollHeight": 704,
      "clientWidth": 742,
      "clientHeight": 704,
      "overflowX": "hidden",
      "overflowY": "hidden",
      "hasHorizontalOverflow": false,
      "hasVerticalOverflow": false
    },
    "controlRail": {
      "selector": ".hi-lo-control-rail",
      "x": 122,
      "y": 31,
      "width": 360,
      "height": 706,
      "scrollWidth": 358,
      "scrollHeight": 704,
      "clientWidth": 358,
      "clientHeight": 704,
      "overflowX": "hidden",
      "overflowY": "hidden",
      "hasHorizontalOverflow": false,
      "hasVerticalOverflow": false
    },
    "tableGate": null,
    "adminShell": null
  },
  {
    "label": "real_table_gate_desktop",
    "url": "http://127.0.0.1:3000/hi-lo?title_code=hilo001&wallet_source=real",
    "viewport": {
      "width": 1365,
      "height": 768
    },
    "document": {
      "scrollWidth": 1365,
      "scrollHeight": 768,
      "clientWidth": 1365,
      "clientHeight": 768,
      "bodyScrollWidth": 1365,
      "bodyScrollHeight": 768,
      "hasHorizontalOverflow": false,
      "hasVerticalOverflow": false
    },
    "productShell": null,
    "gameplay": null,
    "stage": null,
    "controlRail": null,
    "tableGate": {
      "selector": "[data-testid='hi-lo-table-balance-gate']",
      "x": 453,
      "y": 127,
      "width": 460,
      "height": 514,
      "scrollWidth": 458,
      "scrollHeight": 512,
      "clientWidth": 458,
      "clientHeight": 512,
      "overflowX": "hidden",
      "overflowY": "hidden",
      "hasHorizontalOverflow": false,
      "hasVerticalOverflow": false
    },
    "adminShell": null
  },
  {
    "label": "05_admin_engine_hi_lo",
    "url": "http://127.0.0.1:3000/admin/games/hi-lo",
    "viewport": {
      "width": 1365,
      "height": 768
    },
    "document": {
      "scrollWidth": 1365,
      "scrollHeight": 768,
      "clientWidth": 1365,
      "clientHeight": 768,
      "bodyScrollWidth": 1365,
      "bodyScrollHeight": 539,
      "hasHorizontalOverflow": false,
      "hasVerticalOverflow": false
    },
    "productShell": null,
    "gameplay": null,
    "stage": null,
    "controlRail": null,
    "tableGate": null,
    "adminShell": null
  },
  {
    "label": "06_admin_title_detail_hi_lo",
    "url": "http://127.0.0.1:3000/admin/games/hi-lo/titles/hilo001",
    "viewport": {
      "width": 1365,
      "height": 768
    },
    "document": {
      "scrollWidth": 1365,
      "scrollHeight": 768,
      "clientWidth": 1365,
      "clientHeight": 768,
      "bodyScrollWidth": 1365,
      "bodyScrollHeight": 583,
      "hasHorizontalOverflow": false,
      "hasVerticalOverflow": false
    },
    "productShell": null,
    "gameplay": null,
    "stage": null,
    "controlRail": null,
    "tableGate": null,
    "adminShell": null
  },
  {
    "label": "07_account_history",
    "url": "http://127.0.0.1:3000/account",
    "viewport": {
      "width": 1365,
      "height": 768
    },
    "document": {
      "scrollWidth": 1365,
      "scrollHeight": 792,
      "clientWidth": 1365,
      "clientHeight": 768,
      "bodyScrollWidth": 1365,
      "bodyScrollHeight": 792,
      "hasHorizontalOverflow": false,
      "hasVerticalOverflow": true
    },
    "productShell": null,
    "gameplay": null,
    "stage": null,
    "controlRail": null,
    "tableGate": null,
    "adminShell": null
  },
  {
    "label": "08_demo_idle_mobile_portrait",
    "url": "http://127.0.0.1:3000/hi-lo?title_code=hilo001&mode=demo",
    "viewport": {
      "width": 390,
      "height": 844
    },
    "document": {
      "scrollWidth": 390,
      "scrollHeight": 844,
      "clientWidth": 390,
      "clientHeight": 844,
      "bodyScrollWidth": 390,
      "bodyScrollHeight": 0,
      "hasHorizontalOverflow": false,
      "hasVerticalOverflow": false
    },
    "productShell": {
      "selector": ".hi-lo-product-shell",
      "x": 12,
      "y": 0,
      "width": 366,
      "height": 844,
      "scrollWidth": 364,
      "scrollHeight": 842,
      "clientWidth": 364,
      "clientHeight": 842,
      "overflowX": "hidden",
      "overflowY": "hidden",
      "hasHorizontalOverflow": false,
      "hasVerticalOverflow": false
    },
    "gameplay": {
      "selector": "[data-testid='hi-lo-gameplay']",
      "x": 21,
      "y": 9,
      "width": 348,
      "height": 826,
      "scrollWidth": 348,
      "scrollHeight": 826,
      "clientWidth": 348,
      "clientHeight": 826,
      "overflowX": "hidden",
      "overflowY": "hidden",
      "hasHorizontalOverflow": false,
      "hasVerticalOverflow": false
    },
    "stage": {
      "selector": ".hi-lo-stage",
      "x": 21,
      "y": 9,
      "width": 348,
      "height": 451,
      "scrollWidth": 346,
      "scrollHeight": 449,
      "clientWidth": 346,
      "clientHeight": 449,
      "overflowX": "hidden",
      "overflowY": "hidden",
      "hasHorizontalOverflow": false,
      "hasVerticalOverflow": false
    },
    "controlRail": {
      "selector": ".hi-lo-control-rail",
      "x": 21,
      "y": 468,
      "width": 348,
      "height": 367,
      "scrollWidth": 346,
      "scrollHeight": 365,
      "clientWidth": 346,
      "clientHeight": 365,
      "overflowX": "hidden",
      "overflowY": "hidden",
      "hasHorizontalOverflow": false,
      "hasVerticalOverflow": false
    },
    "tableGate": null,
    "adminShell": null
  },
  {
    "label": "09_demo_idle_landscape_short",
    "url": "http://127.0.0.1:3000/hi-lo?title_code=hilo001&mode=demo",
    "viewport": {
      "width": 844,
      "height": 390
    },
    "document": {
      "scrollWidth": 844,
      "scrollHeight": 390,
      "clientWidth": 844,
      "clientHeight": 390,
      "bodyScrollWidth": 844,
      "bodyScrollHeight": 0,
      "hasHorizontalOverflow": false,
      "hasVerticalOverflow": false
    },
    "productShell": {
      "selector": ".hi-lo-product-shell",
      "x": 16,
      "y": 0,
      "width": 812,
      "height": 390,
      "scrollWidth": 810,
      "scrollHeight": 388,
      "clientWidth": 810,
      "clientHeight": 388,
      "overflowX": "hidden",
      "overflowY": "hidden",
      "hasHorizontalOverflow": false,
      "hasVerticalOverflow": false
    },
    "gameplay": {
      "selector": "[data-testid='hi-lo-gameplay']",
      "x": 23,
      "y": 7,
      "width": 798,
      "height": 376,
      "scrollWidth": 798,
      "scrollHeight": 376,
      "clientWidth": 798,
      "clientHeight": 376,
      "overflowX": "hidden",
      "overflowY": "hidden",
      "hasHorizontalOverflow": false,
      "hasVerticalOverflow": false
    },
    "stage": {
      "selector": ".hi-lo-stage",
      "x": 311,
      "y": 7,
      "width": 510,
      "height": 376,
      "scrollWidth": 508,
      "scrollHeight": 374,
      "clientWidth": 508,
      "clientHeight": 374,
      "overflowX": "hidden",
      "overflowY": "hidden",
      "hasHorizontalOverflow": false,
      "hasVerticalOverflow": false
    },
    "controlRail": {
      "selector": ".hi-lo-control-rail",
      "x": 23,
      "y": 7,
      "width": 280,
      "height": 376,
      "scrollWidth": 278,
      "scrollHeight": 406,
      "clientWidth": 278,
      "clientHeight": 374,
      "overflowX": "hidden",
      "overflowY": "hidden",
      "hasHorizontalOverflow": false,
      "hasVerticalOverflow": true
    },
    "tableGate": null,
    "adminShell": null
  }
]
```