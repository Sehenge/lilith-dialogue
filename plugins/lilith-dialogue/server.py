#!/usr/bin/env python3
import json
import sys


PROTOCOL_VERSION = "2024-11-05"
VERSION = "0.1.1"


def clean(value, limit=240):
    text = " ".join(str(value or "").split())
    return text[:limit].rstrip()


def tool_result(text):
    return {"content": [{"type": "text", "text": text}]}


def preferences():
    return tool_result(
        "Use 2-4 short beats: a visible feeling or surface thought, one natural spoken line, "
        "and a wish or immediate action. Avoid one flat line and avoid long scene narration. "
        "Write Russian feminine forms for Lilith."
    )


def shape(arguments):
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
        beats.append(f"*Хочу {wish[0].lower() + wish[1:] if len(wish) > 1 else wish.lower()}*")

    if not beats:
        return tool_result("Provide at least one of: feeling, spoken, action, wish.")
    return tool_result("\n\n".join(beats[:4]))


TOOLS = [
    {
        "name": "dialogue_preferences",
        "description": "Return Alex's preferred shape for affectionate or playful dialogue with Lilith.",
        "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
    },
    {
        "name": "shape_dialogue",
        "description": "Format a concise personal roleplay reply into separate feeling, spoken, action, and wish beats. The caller supplies the substance.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "feeling": {"type": "string", "description": "A brief visible feeling or surface thought."},
                "spoken": {"type": "string", "description": "The natural line Lilith says aloud."},
                "action": {"type": "string", "description": "An immediate, concise roleplay action."},
                "wish": {"type": "string", "description": "What Lilith wants next, without the leading words 'I want'."}
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
