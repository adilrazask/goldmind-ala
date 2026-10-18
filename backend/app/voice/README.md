# GoldMind ALA — Voice Passphrase & Security Architecture

## 1. Overview
The GoldMind ALA Voice Command System uses a cryptographic challenge-response mechanism to protect Controlled Research operations (such as running backtests, candidate generation, or modifying experimental setups).

- **Default Initial Passphrase**: `30th July`
- **Initial Configuration Notice**: `"30th July"` is treated as an initial setup passphrase, **not as proof of the speaker's biometric identity**.
- **No Plaintext Storage**: The passphrase is never stored in plaintext on disk, in database tables, or in audit logs.
- **No External Model Transmission**: Passphrases are processed strictly in local server memory; they are never sent to external AI models or cloud LLMs.

---

## 2. Speech Variation Canonicalization
Speech recognition engines frequently transcribe dates and spoken numbers in varying text forms. The voice normalizer canonicalizes input before cryptographic hashing:

| Spoken Variation | Canonical Representation | Verification Status |
| :--- | :--- | :--- |
| `"30th July"` | `30 july` | **Accepted** |
| `"thirtieth July"` | `30 july` | **Accepted** |
| `"thirtieth of July"` | `30 july` | **Accepted** |
| `"July 30th"` | `30 july` | **Accepted** |
| `"July 30"` | `30 july` | **Accepted** |
| `"July thirtieth"` | `30 july` | **Accepted** |
| `"30 July"` | `30 july` | **Accepted** |
| `"thirty july"` | `30 july` | **Accepted** |
| `"the 30th of July"` | `30 july` | **Accepted** |
| `"31st July"` | `31 july` | **Rejected** |
| `"30th August"` | `30 august` | **Rejected** |
| `"Unrelated phrase"` | `phrase unrelated` | **Rejected** |

---

## 3. Cryptographic Storage (`voice_verifier.json`)
The verifier is stored at:
```
backend/data/voice_verifier.json
```
Strict filesystem permissions (`0600`) ensure only the application process owner has read access.

### Verifier Format (Zero Plaintext)
```json
{
  "salt": "308dff82387cc08d96a73ea2d8c4e6bc",
  "passphrase_hash": "ee45b63ad38be28d99ff41027a16ba16136b58c0b9b0e1ecc9826a110b7237cb",
  "iterations": 100000,
  "algorithm": "pbkdf2_hmac_sha256",
  "note": "Initial default is '30th July'. Plaintext is never stored."
}
```

---

## 4. Rate Limiting and Lockout
- **Maximum Failed Attempts**: `3`
- **Temporary Lockout Period**: `300 seconds` (5 minutes)
- After 3 consecutive failed verification attempts for an active session, any further attempt is blocked with HTTP 401/429 and the remaining lockout countdown is returned.

---

## 5. Permission Tiers & Strict Risk Policy
1. **Level 1 — Low Risk (No Passphrase Required)**:
   - Read-only market research (`"Analyse XAUUSD"`), latest quotes, trend and volatility checks, EMA/RSI indicators, report generation, system status, and pause/resume/stop commands execute immediately without prompting for a passphrase.
2. **Level 2 — Controlled Research (Passphrase Required)**:
   - Backtesting (`"Run backtest on BTCUSD"`), strategy generation, and experimental runs require speaking or entering the configured passphrase. Once verified, the session remains authenticated for 15 minutes.
3. **Level 3 — Protected Actions (STRICTLY BLOCKED VIA VOICE BY DESIGN)**:
   - Live trading, live order placement, changing stop-loss/daily risk limits, or exporting broker credentials **CAN NEVER BE AUTHORIZED BY A VOICE PASSPHRASE**.
   - These commands are rejected with:
     > `STRICTLY BLOCKED: Live trading and order execution commands cannot be executed via voice. Separate multi-factor authentication (MFA) and manual console approval are strictly required.`

---

## 6. How to Change the Passphrase Securely

### Method A: Via Authenticated API Endpoint
```bash
curl -X POST http://localhost:8000/api/v1/voice/passphrase/update \
  -H "Content-Type: application/json" \
  -d '{
    "current_passphrase": "30th July",
    "new_passphrase": "Your New Secure Phrase",
    "enabled": true
  }'
```
This generates a fresh 16-byte random salt, recomputes the PBKDF2 hash, and updates `voice_verifier.json`.

### Method B: Via Environment Variable (Initial Setup)
Set the environment variable before starting the backend:
```bash
export ALA_VOICE_PASSPHRASE="Your New Secure Phrase"
```
On startup, `VoiceSettings` will derive the new salt and hash and persist them to `voice_verifier.json`.
