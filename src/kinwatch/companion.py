from __future__ import annotations

from functools import lru_cache

from kinwatch.settings import Settings


def speak(text: str, settings: Settings) -> dict[str, str]:
    """Best-effort Polly/Nova speech. Companion always has captions even if AWS is absent."""
    if settings.use_fixtures:
        return {"transcript": text, "audio": "fixture://speech"}
    try:
        import boto3

        polly = boto3.client("polly", region_name=settings.aws_region)
        polly.synthesize_speech(Text=text, OutputFormat="mp3", VoiceId=settings.polly_voice, Engine="neural")
        return {"transcript": text, "audio": "polly"}
    except Exception:
        return {"transcript": text, "audio": "caption-only"}


@lru_cache(maxsize=1)
def companion_html() -> str:
    return COMPANION_HTML


COMPANION_HTML = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Kinwatch companion</title>
  <style>
    :root { color-scheme: dark; }
    body { font-family: system-ui, sans-serif; margin:0; background:#0e1116; color:#f4f1ea; }
    header, main, footer { max-width: 52rem; margin: 0 auto; padding: 1rem 1.25rem; }
    h1 { font-size: 2.1rem; margin: .2rem 0; }
    p, li, button, label { font-size: 1.15rem; line-height: 1.45; }
    button { min-height: 44px; padding: .5rem 1rem; margin: .25rem .25rem .25rem 0; background:#f4f1ea; color:#111; border:0; font-weight: 650; cursor:pointer; }
    button:focus { outline: 3px solid #7dd3fc; outline-offset: 2px; }
    .panel { border: 2px solid #f4f1ea; padding: 1rem; margin: 1rem 0; }
    .offline { font-weight: 700; }
    .offline[data-online="true"] { color:#b7f7c1; }
    .offline[data-online="false"] { color:#ffd18c; }
    textarea { width:100%; min-height: 4rem; font-size: 1.15rem; }
    .skip { position:absolute; left:-999px; }
    .skip:focus { left:1rem; top:1rem; background:#fff; color:#000; padding:.5rem; }
    dialog { background:#0e1116; color:#f4f1ea; border:2px solid #f4f1ea; max-width: 36rem; }
    @media (prefers-reduced-motion: reduce) { * { animation: none !important; transition: none !important; } }
  </style>
</head>
<body>
  <a class="skip" href="#ask">Skip to ask Kinwatch</a>
  <header>
    <p>Kinwatch · simulated Alexa+ host · MCP 2025-11-25</p>
    <h1>What happened at the door?</h1>
    <p>Plain language for the person at home and the family member who is away. Kinwatch cannot lock doors.</p>
    <button type="button" id="skip-tutorial">Skip tutorial</button>
  </header>
  <dialog id="tutorial" open>
    <h2>First visit</h2>
    <p>This companion talks to the same MCP server Alexa+ would. Devices use the names from the Ring app. Privacy zones are never shown.</p>
    <button type="button" id="close-tutorial">Continue</button>
  </dialog>
  <main>
    <section class="panel" aria-labelledby="devices-h">
      <h2 id="devices-h">Household</h2>
      <ul id="devices"><li>Loading devices…</li></ul>
      <p id="empty-devices" hidden>No devices linked yet. Open the Ring app to finish account linking, or run the fixture demo.</p>
    </section>
    <section class="panel" aria-labelledby="brief-h">
      <h2 id="brief-h">Latest brief</h2>
      <p id="brief" role="status">Nothing at the door yet. I am watching.</p>
      <p id="captions" aria-live="polite"></p>
    </section>
    <section class="panel" id="ask" aria-labelledby="ask-h">
      <h2 id="ask-h">Ask Kinwatch</h2>
      <label for="utterance">What do you want to know?</label>
      <textarea id="utterance" maxlength="500">What happened at Mom's?</textarea>
      <div>
        <button type="button" id="say">Speak brief</button>
        <button type="button" id="show">Show me</button>
        <button type="button" id="chime">Tell the house I'm looking</button>
        <button type="button" id="overnight">What happened overnight?</button>
        <button type="button" id="demo">Inject night incident</button>
      </div>
    </section>
    <section class="panel" aria-labelledby="widgets-h">
      <h2 id="widgets-h">MCP Apps</h2>
      <iframe id="widget" title="Kinwatch widget" style="width:100%;min-height:280px;border:0;background:#111"></iframe>
    </section>
    <section class="panel">
      <h2>Data</h2>
      <p>Delete everything Kinwatch stored for this household. Ring settings stay in the Ring app.</p>
      <button type="button" id="delete">Delete household data</button>
    </section>
  </main>
  <footer>
    <p>Not affiliated with Ring or Amazon. Say Ring app / Ring Appstore when you mean those products.</p>
  </footer>
  <script>
    const $ = (id) => document.getElementById(id);
    const closeTutorial = () => { $("tutorial").open = false; localStorage.setItem("kinwatch-tutorial", "1"); };
    $("close-tutorial").onclick = closeTutorial;
    $("skip-tutorial").onclick = closeTutorial;
    if (localStorage.getItem("kinwatch-tutorial")) closeTutorial();

    async function loadDevices() {
      const res = await fetch("/api/devices");
      const data = await res.json();
      const ul = $("devices");
      ul.innerHTML = "";
      if (!data.devices || !data.devices.length) {
        $("empty-devices").hidden = false;
        return;
      }
      $("empty-devices").hidden = true;
      for (const d of data.devices) {
        const li = document.createElement("li");
        const state = d.online ? "online" : "offline";
        li.innerHTML = `<span>${d.name}</span> — <span class="offline" data-online="${d.online}">${state}</span> (${d.kind})`;
        ul.appendChild(li);
      }
    }
    async function brief() {
      const res = await fetch("/api/brief");
      const data = await res.json();
      $("brief").textContent = data.briefing;
      $("captions").textContent = data.briefing;
    }
    async function speak(text) {
      const res = await fetch("/api/utterance", { method:"POST", headers:{"content-type":"application/json"}, body: JSON.stringify({text}) });
      const data = await res.json();
      $("brief").textContent = data.text;
      $("captions").textContent = data.text;
      loadWidget("visitor");
    }
    async function loadWidget(kind) {
      const res = await fetch("/widgets/" + kind);
      const html = await res.text();
      $("widget").srcdoc = html;
    }
    $("say").onclick = () => speak($("utterance").value);
    $("show").onclick = () => { speak("Show me"); loadWidget("live-view"); };
    $("chime").onclick = () => speak("Tell the house I'm looking");
    $("overnight").onclick = () => { speak("What happened overnight?"); loadWidget("timeline"); };
    $("demo").onclick = async () => {
      await fetch("/demo/inject", { method:"POST" });
      await brief();
      loadWidget("timeline");
    };
    $("delete").onclick = async () => {
      await fetch("/api/data", { method:"DELETE" });
      await brief();
      await loadDevices();
    };
    loadDevices();
    brief();
    loadWidget("timeline");
  </script>
</body>
</html>
"""
