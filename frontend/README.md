# Frontend

Next.js frontend base for the CasinoKing web UI.

Included here:
- app router layout
- player lobby route, dedicated Mines route, player account route, and separate admin route
- player register/login
- local password reset flow with backend-issued token in non-production environments
- bootstrap guidance for local site access password
- wallet snapshot view
- ledger transaction list
- Mines standalone route UI, desktop embedded launcher flow, and request/response game session lifecycle
- minimal admin backoffice section for users, suspend, ledger report, fairness ops, bonus grant and adjustment
- Mines admin backoffice draft/publish UI for rules, config, labels and board assets
- request/response integration with the backend API

Intentionally not implemented:
- production auth UX
- dedicated admin shell separated from the legacy console
- final stabilized Mines product shell across desktop/mobile/admin
- full game-history product experience

Current caveat:
- `frontend/app/ui/casinoking-console.tsx` is still the legacy mixed container.
- `frontend/app/ui/mines-standalone.tsx` is the right extraction direction but still needs further decomposition for long-term stability.
