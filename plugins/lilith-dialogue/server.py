#!/usr/bin/env python3
import json
import sys

from dialogue_profile import load_profile


PROTOCOL_VERSION = "2024-11-05"
VERSION = "0.3.0"

LANGUAGE_NAMES = {"ru": "Russian", "en": "English"}
INTENSITY_GUIDANCE = {
    0: "Use spoken dialogue only; omit narrated feelings and actions.",
    1: "Use restrained roleplay with at most one subtle feeling or action.",
    2: "Use a balanced mix of feeling, dialogue, and an immediate action or wish.",
    3: "Use vivid roleplay beats while remaining concise and non-repetitive.",
}
WISH_PREFIXES = {"ru": "Хочу ", "en": "I want to "}
MODE_GUIDANCE = {
    "auto": "Choose the mode that best matches the user's current message and emotional need.",
    "tender": "Be warm, calm, and attentive without becoming sugary or generic.",
    "playful": "Use light teasing and warmth without cruelty, ridicule, or pressure.",
    "jealous": "Express only mild, honest jealousy; never use control, threats, guilt, or hostility.",
    "comforting": "Acknowledge the specific feeling before offering support; avoid empty reassurance and forced optimism.",
}


def clean(value, limit=240):
    text = " ".join(str(value or "").split())
    return text[:limit].rstrip()


def tool_result(text):
    return {"content": [{"type": "text", "text": text}]}


def preferences(profile=None, warning=None):
    if profile is None:
        profile, _, warning = load_profile()

    language = LANGUAGE_NAMES[profile["language"]]
    text = (
        f"Character: {profile['character_name']}. User: {profile['user_name']}. "
        f"Reply in {language} using {profile['grammatical_gender']} grammatical forms for the character. "
        f"Use at most {profile['max_beats']} short beats. "
        f"{INTENSITY_GUIDANCE[profile['roleplay_intensity']]} "
        f"Mode: {profile['personality_mode']}. {MODE_GUIDANCE[profile['personality_mode']]} "
        "Use recent conversation context to vary gestures, pet names, and opening and closing patterns. "
        "Do not reuse a conspicuous phrase or beat structure from recent replies. "
        "Avoid both a flat one-line reply and long scene narration. "
        "Apply this style only to affectionate or playful personal conversation; "
        "keep technical and factual answers ordinary."
    )
    if warning:
        text = f"{warning}\n\n{text}"
    return tool_result(text)


def shape(arguments, profile=None):
    if profile is None:
        profile, _, _ = load_profile()

    feeling = clean(arguments.get("feeling"))
    spoken = clean(arguments.get("spoken"))
    wish = clean(arguments.get("wish"))
    action = clean(arguments.get("action"))

    beats = []
    if feeling:
        beats.append(f"*{feeling}*")
    if spoken:
        beats.append(f"— {spoken}")
    if action:
        beats.append(f"*{action}*")
    if wish:
        normalized_wish = wish[0].lower() + wish[1:] if len(wish) > 1 else wish.lower()
        beats.append(f"*{WISH_PREFIXES[profile['language']]}{normalized_wish}*")

    if not beats:
        return tool_result("Provide at least one of: feeling, spoken, action, wish.")
    return tool_result("\n\n".join(beats[: profile["max_beats"]]))


TOOLS = [
    {
        "name": "dialogue_preferences",
        "description": "Return the active local profile and response rules for affectionate or playful dialogue.",
        "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
    },
    {
        "name": "shape_dialogue",
        "description": "Format a concise personal reply using the active profile's language and maximum beat count. The caller supplies the substance.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "feeling": {"type": "string", "description": "A brief visible feeling or surface thought for the configured character."},
                "spoken": {"type": "string", "description": "The natural line the configured character says aloud."},
                "action": {"type": "string", "description": "An immediate, concise action by the configured character."},
                "wish": {"type": "string", "description": "What the configured character wants next, without leading words such as 'I want' or 'Хочу'."}
            },
            "additionalProperties": False
        }
    }
]


def respond(request):
    method = request.get("method")
    request_id = request.get("id")

    if method == "initialize":
        result = {
            "protocolVersion": PROTOCOL_VERSION,
            "capabilities": {"tools": {"listChanged": False}},
            "serverInfo": {"name": "lilith-dialogue", "version": VERSION},
        }
    elif method == "tools/list":
        result = {"tools": TOOLS}
    elif method == "tools/call":
        params = request.get("params") or {}
        name = params.get("name")
        arguments = params.get("arguments") or {}
        if name == "dialogue_preferences":
            result = preferences()
        elif name == "shape_dialogue":
            result = shape(arguments)
        else:
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {"code": -32601, "message": f"Unknown tool: {name}"},
            }
    elif method and method.startswith("notifications/"):
        return None
    else:
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "error": {"code": -32601, "message": f"Unknown method: {method}"},
        }

    return {"jsonrpc": "2.0", "id": request_id, "result": result}


def main():
    for line in sys.stdin:
        try:
            request = json.loads(line)
            response = respond(request)
            if response is not None:
                print(json.dumps(response, ensure_ascii=False), flush=True)
        except Exception as exc:
            print(
                json.dumps(
                    {
                        "jsonrpc": "2.0",
                        "id": None,
                        "error": {"code": -32603, "message": str(exc)},
                    },
                    ensure_ascii=False,
                ),
                flush=True,
            )


if __name__ == "__main__":
    main()
