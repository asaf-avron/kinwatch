# Kinwatch

The remote family member who never sleeps at the door — a Ring + Alexa+ caretaking copilot for people living alone and the adults who worry about them.

## Agents

CEO and CTO are bootstrapped via Paperclip. Add domain-specific agents as needed.

## Paperclip / Oracle

Oracle and Paperclip allowed **only** for company **KIN / Kinwatch**.
Do not operate on EXCLUDED companies: SYN / Maqom, CIN / CineTrace AI, PKN / PocketNode Core.
Use `.cursor/skills/oracle-connection` for SSH/host facts.
Use `.cursor/skills/paperclip-kin` for KIN board work.
Resolve company at runtime: `issuePrefix == "KIN"`. Never `companies[0]`.

## Product constraints

- Import and call the Ring Partner API (or official Playground fixtures) at runtime. Do not invent lock actuation.
- MCP is Streamable HTTP, protocol **2025-11-25**.
- Privacy zones: never display, analyze, or store that video.
- Devices in the UI use household names, never Ring device IDs.
- No secrets in git.
