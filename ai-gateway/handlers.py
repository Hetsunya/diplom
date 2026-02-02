import asyncio


async def handle_message(msg: dict):
    msg_type = msg.get("type")

    if msg_type == "ping":
        print(f"[PING] session={msg['session_id']}")

    elif msg_type == "frame":
        # здесь будет base64 jpeg / bytes
        await handle_frame(msg["payload"])

    elif msg_type == "audio":
        await handle_audio(msg["payload"])

    else:
        print("[WS] message:", msg)


async def handle_frame(payload):
    """
    payload пример:
    {
      "participant_id": "...",
      "frame": "base64..."
    }
    """
    print("[FRAME] received frame")
    # TODO: decode → inference


async def handle_audio(payload):
    print("[AUDIO] received audio chunk")
