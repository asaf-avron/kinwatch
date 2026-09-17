from __future__ import annotations

from html import escape
from typing import Any

from kinwatch.models import Incident, Visitor
from kinwatch.names import strip_ids


def visitor_html(visitor: Visitor | None, incident: Incident | None) -> str:
    name = escape(visitor.name if visitor else "Unknown arrival")
    notes = escape(strip_ids(visitor.notes if visitor else (incident.briefing if incident else "No labeled visitor yet.")))
    vision = escape(incident.vision.summary if incident and incident.vision else "No snapshot classification yet.")
    return f"""<!doctype html>
<html lang="en">
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Visitor</title>
<style>
  body {{ font-family: system-ui, sans-serif; background:#111; color:#f4f1ea; margin:0; padding:1.25rem; }}
  h1 {{ font-size: 1.8rem; margin: 0 0 .5rem; }}
  p {{ font-size: 1.15rem; line-height: 1.45; max-width: 40rem; }}
  .status {{ display:inline-block; padding:.2rem .6rem; border:2px solid #f4f1ea; }}
</style>
<body>
  <h1>{name}</h1>
  <p class="status">{vision}</p>
  <p>{notes}</p>
</body>
</html>
"""


def timeline_html(incidents: list[Incident]) -> str:
    items = []
    for inc in incidents[:12]:
        when = inc.started_at.isoformat()
        title = escape(strip_ids(inc.briefing or inc.title))
        names = escape(", ".join(inc.device_names) or "the door")
        items.append(f"<li><strong>{escape(when)}</strong> — {title} <span>({names})</span></li>")
    body = "".join(items) or "<li>Nothing yet. When the doorbell or door sensor fires, it will show here.</li>"
    return f"""<!doctype html>
<html lang="en">
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Overnight timeline</title>
<style>
  body {{ font-family: system-ui, sans-serif; background:#111; color:#f4f1ea; margin:0; padding:1.25rem; }}
  h1 {{ font-size: 1.8rem; }}
  li {{ font-size: 1.1rem; margin: .6rem 0; line-height: 1.4; }}
</style>
<body>
  <h1>What happened overnight</h1>
  <ol>{body}</ol>
</body>
</html>
"""


def live_view_html(device_name: str, whep_location: str, caption: str) -> str:
    return f"""<!doctype html>
<html lang="en">
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Live view</title>
<style>
  body {{ font-family: system-ui, sans-serif; background:#111; color:#f4f1ea; margin:0; padding:1.25rem; }}
  h1 {{ font-size: 1.8rem; }}
  p {{ font-size: 1.15rem; }}
  .stage {{ background:#1c2230; min-height: 220px; display:flex; align-items:center; justify-content:center; border:2px solid #f4f1ea; }}
  @media (prefers-reduced-motion: reduce) {{ .stage {{ animation: none; }} }}
</style>
<body>
  <h1>Live view — {escape(device_name)}</h1>
  <div class="stage" role="img" aria-label="{escape(caption)}">{escape(caption)}</div>
  <p>WHEP session: {escape(whep_location)}</p>
  <p>Privacy zones are already removed from this view. Zone shapes are not shown.</p>
</body>
</html>
"""


WIDGETS: dict[str, dict[str, Any]] = {
    "visitor": {"uri": "ui://kinwatch/visitor", "name": "Visitor card", "mimeType": "text/html;profile=mcp-app"},
    "timeline": {"uri": "ui://kinwatch/timeline", "name": "Incident timeline", "mimeType": "text/html;profile=mcp-app"},
    "live-view": {"uri": "ui://kinwatch/live-view", "name": "Live view", "mimeType": "text/html;profile=mcp-app"},
}
