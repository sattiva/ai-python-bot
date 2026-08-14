import aiohttp
import io
import shutil
import re
import discord
import imageio_ffmpeg
from utils.providers import get_http_session

def get_ffmpeg_binary() -> str:
    which_path = shutil.which("ffmpeg")
    if which_path:
        return which_path
    try:
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return "ffmpeg"

def filter_speech_text(text: str, filters: dict | None = None) -> str:
    if not filters or not text:
        return text

    cleaned = text

    if filters.get("code", True):
        cleaned = re.sub(r"```[\s\S]*?```", "", cleaned)
        cleaned = re.sub(r"`[^`]*`", "", cleaned)

    if filters.get("asterisks", True):
        cleaned = re.sub(r"\*[^*]+\*", "", cleaned)

    if filters.get("brackets", True):
        cleaned = re.sub(r"\[[^\]]*\]", "", cleaned)

    if filters.get("parentheses", False):
        cleaned = re.sub(r"\([^)]*\)", "", cleaned)

    if filters.get("braces", False):
        cleaned = re.sub(r"\{[^}]*\}", "", cleaned)

    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    if not cleaned and text:
        cleaned = re.sub(r"[`*\[\]{}()]", "", text).strip()
    return cleaned

async def synthesize_speech(
    provider: str,
    api_key: str,
    text: str,
    voice_id: str = "aura-asteria-en",
    filters: dict | None = None
) -> tuple[str | None, bytes | None]:
    if not api_key:
        return f"{provider.capitalize()} API key is missing.", None

    speech_text = filter_speech_text(text, filters)
    if not speech_text:
        return None, None

    provider_lower = provider.lower()

    if provider_lower == "deepgram":
        url = f"https://api.deepgram.com/v1/speak?model={voice_id}&encoding=mp3"
        headers = {
            "Authorization": f"Token {api_key}",
            "Content-Type": "application/json"
        }
        payload = {"text": speech_text}
    elif provider_lower == "openai":
        url = "https://api.openai.com/v1/audio/speech"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "tts-1",
            "voice": voice_id if voice_id else "alloy",
            "input": speech_text
        }
    elif provider_lower == "elevenlabs":
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
        headers = {
            "xi-api-key": api_key,
            "Content-Type": "application/json"
        }
        payload = {
            "text": speech_text,
            "model_id": "eleven_monolingual_v1"
        }
    else:
        return f"Unsupported TTS provider: {provider}", None

    session = get_http_session()
    try:
        async with session.post(url, headers=headers, json=payload, timeout=aiohttp.ClientTimeout(total=30)) as resp:
            if resp.status != 200:
                err_msg = await resp.text()
                return f"{provider.capitalize()} TTS failed (HTTP {resp.status}): {err_msg}", None
            audio_data = await resp.read()
            return None, audio_data
    except Exception as exc:
        return str(exc), None

def create_audio_source(audio_bytes: bytes) -> discord.AudioSource:
    ffmpeg_exe = get_ffmpeg_binary()
    return discord.FFmpegPCMAudio(io.BytesIO(audio_bytes), pipe=True, executable=ffmpeg_exe)
