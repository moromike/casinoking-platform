# INT-05: Seamless Wallet API - Platform Guide
*Version 1.0 - The Great Decoupling*

This document defines how the Casinoking Platform expects Game Providers to behave.

## 1. Game Launch
The Platform launches games by opening an iframe with a secure launch token:
`<iframe src="https://provider.games.com/launch?token=XYZ"></iframe>`

## 2. Token Validation
The Provider validates the token by calling the Platform:
**GET /api/v1/seamless/auth/validate?token=XYZ**
**Response:** `{"player_id": "uuid", "currency": "EUR", "balance": 100.0}`

## 3. Strict Ledger Enforcement
The Platform will strictly enforce that no `/commit` can occur without a prior `/reserve`.
All transactions must balance to 0 (Double-entry requirement CON-02).
