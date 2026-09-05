# INT-04: Seamless Wallet API - Provider Guide
*Version 1.0 - The Great Decoupling*

This document defines how external Game Providers (e.g. M&M Games) interact with the Casinoking Platform.
Providers must never manage user balances directly.

## 1. Authentication
All requests from Provider to Platform must include a pre-shared API Key:
`Authorization: Bearer <PROVIDER_API_KEY>`

## 2. Endpoints
The Platform exposes the following endpoints to the Provider:

### POST /api/v1/seamless/wallet/reserve
Reserve funds for a bet.
**Body:** `{"player_id": "uuid", "amount": 10.0, "currency": "EUR", "game_session_id": "uuid"}`
**Response:** `{"transaction_id": "uuid", "balance_after": 90.0}`

### POST /api/v1/seamless/wallet/commit
Commit a previously reserved bet (the player loses) or settle a win.
**Body:** `{"player_id": "uuid", "transaction_id": "uuid", "win_amount": 25.0}`
**Response:** `{"balance_after": 115.0}`

### POST /api/v1/seamless/wallet/rollback
Cancel a reservation (the game crashed or bet was rejected).
**Body:** `{"player_id": "uuid", "transaction_id": "uuid"}`
**Response:** `{"balance_after": 100.0}`
