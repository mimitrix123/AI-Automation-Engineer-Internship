"""Voice-control intent layer. Connect this to an approved speech assistant or local STT/TTS stack."""
from dataclasses import dataclass

@dataclass
class VoiceIntent:
    action: str
    target: str | None = None
    value: str | None = None


def parse_command(text: str) -> VoiceIntent:
    command = text.lower().strip()
    if "turn on" in command and "light" in command:
        return VoiceIntent("set", "light", "on")
    if "turn off" in command and "light" in command:
        return VoiceIntent("set", "light", "off")
    if "temperature" in command:
        return VoiceIntent("read", "temperature")
    return VoiceIntent("unknown")
