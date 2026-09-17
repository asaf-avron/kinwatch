from __future__ import annotations

from typing import Any

from kinwatch.runtime import KinwatchRuntime


def run_strands_brief(runtime: KinwatchRuntime, utterance: str) -> dict[str, Any]:
    """Strands agent loop when the extra is installed; otherwise a local tool loop."""
    try:
        from strands import Agent
        from strands.models import BedrockModel

        def list_devices() -> dict[str, Any]:
            return runtime.call("list_devices")

        def brief_household() -> dict[str, Any]:
            return runtime.call("brief_household")

        def play_chime() -> dict[str, Any]:
            return runtime.call("play_chime")

        def get_live_view() -> dict[str, Any]:
            return runtime.call("get_live_view", {})

        model = BedrockModel(model_id=runtime.settings.strands_model)
        agent = Agent(
            model=model,
            tools=[list_devices, brief_household, play_chime, get_live_view],
            system_prompt=(
                "You are Kinwatch. Speak plain language. Never mention device IDs. "
                "Never claim you can lock a door. Use tools for household facts."
            ),
        )
        reply = agent(utterance)
        return {"engine": "strands+bedrock", "text": str(reply), "mcp_protocol": "2025-11-25"}
    except Exception:
        return local_agent_loop(runtime, utterance)


def local_agent_loop(runtime: KinwatchRuntime, utterance: str) -> dict[str, Any]:
    text = utterance.lower()
    used: list[str] = []
    if "show" in text or "live" in text or "camera" in text:
        live = runtime.call("get_live_view", {})
        used.append("get_live_view")
        reply = f"Here is the live view of {live.get('device_name', 'the door')}."
    elif "chime" in text or "looking" in text or "coming" in text:
        runtime.call("play_chime", {})
        used.append("play_chime")
        reply = "I told the house you are looking."
    elif "overnight" in text or "happened" in text or "timeline" in text:
        incidents = runtime.call("list_incidents", {})
        used.append("list_incidents")
        n = len(incidents.get("incidents") or [])
        brief = runtime.call("brief_household", {})
        used.append("brief_household")
        reply = f"{brief.get('briefing')} I counted {n} fused incident(s)."
    else:
        brief = runtime.call("brief_household", {})
        used.append("brief_household")
        reply = str(brief.get("briefing") or "I am watching the door.")
    return {"engine": "local-policy", "text": reply, "tools": used, "mcp_protocol": "2025-11-25"}
