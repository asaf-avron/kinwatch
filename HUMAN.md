# Human unblockers (Kinwatch / KIN)

Agents cannot complete these. They are the only steps that block a real Ring/AWS demo after Paperclip provision.

## Identity (done in provision, human follow-up)

1. **Add `asaf-avron/kinwatch` to fine-grained PAT `personal-paperclip-oracle`.** Until that allowlist update, Oracle agents can `git clone` this **public** repo but cannot push or open PRs with the PAT. Host `gh` must stay `insiteu-bot` — never `gh auth login` on Oracle.
2. Confirm Paperclip secret `cursor-api-key` on KIN is the Gmail Cursor key (`asafavron@gmail.com`), **not** host `/opt/milepo-oracle/.env` (`asafa.insiteu@gmail.com`). Copied from CIN; SHA-256 of the value matches CIN and PKN. `/v0/me` returns `asafavron@gmail.com`. A CEO heartbeat on 17 Sep 2026 still failed with Cursor CLI `The provided API key is invalid` — same fingerprint as CIN, so this is a Cursor CLI/key-type issue to fix on the Gmail account, not a SYN-key mixup.
3. Confirm `~/.kinwatch/github.env` is chmod 600 and the same PAT as CIN/PKN. **Add `asaf-avron/kinwatch` to PAT `personal-paperclip-oracle`** so Oracle agents can push/PR. Public clone already works.

## Accounts (you)

| Item | Why | Status |
| --- | --- | --- |
| Devpost entry at https://amazonappdev2026.devpost.com/ | Required to submit by 23 Oct 2026 12:00 PT | Human |
| AWS $150 credit form (closes 21 Oct 12:00 PT) | Bedrock / AgentCore / Polly spend | Human |
| Ring Developer Playground token | Week-1 live API without Appstore cert | Human |
| Ring Developer Portal app: HMAC key, client id/secret, webhook URL | One-way linking + signed webhooks | Human |
| Ring app on a phone for HMAC once / device names | Certification-shaped linking | Human |
| YouTube/Vimeo public video, English, &lt;3 min, no stock music | Stage 2 artifact | Human records; script in `VIDEO.md` |
| Optional: US Alexa+ Preview / toolkit | Real add-on; **must not** block the simulator | Human |

## After you have secrets

Put them in `/opt/kinwatch` host env or a systemd drop-in — not in git:

- `RING_ACCESS_TOKEN` / refresh
- `RING_HMAC_KEY`
- `RING_CLIENT_ID` / `RING_CLIENT_SECRET`
- AWS credentials for Bedrock + DynamoDB

Then set `KINWATCH_USE_FIXTURES=false`.
