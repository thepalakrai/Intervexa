"""
Azure Speech service - speech-to-text and text-to-speech via direct REST
calls (same approach as ai_service.py - avoids SDK dependency headaches).
"""
import os
import requests

SPEECH_KEY = os.getenv("AZURE_SPEECH_KEY")
SPEECH_REGION = os.getenv("AZURE_SPEECH_REGION", "southeastasia")


def speech_to_text(audio_bytes: bytes, language: str = "en-US") -> str:
    """
    Sends WAV audio bytes to Azure Speech and returns the recognized text.
    Expects 16kHz, 16-bit, mono PCM WAV audio (the standard format the
    browser's MediaRecorder + a quick conversion step will produce).
    """
    if not SPEECH_KEY:
        raise RuntimeError("AZURE_SPEECH_KEY not set. Check your .env file.")

    url = f"https://{SPEECH_REGION}.stt.speech.microsoft.com/speech/recognition/conversation/cognitiveservices/v1"
    params = {"language": language, "format": "simple"}
    headers = {
        "Ocp-Apim-Subscription-Key": SPEECH_KEY,
        "Content-Type": "audio/wav; codecs=audio/pcm; samplerate=16000",
        "Accept": "application/json",
    }

    response = requests.post(url, params=params, headers=headers, data=audio_bytes, timeout=30)
    response.raise_for_status()
    data = response.json()

    if data.get("RecognitionStatus") != "Success":
        return ""
    return data.get("DisplayText", "")


def text_to_speech(text: str, voice: str = "en-US-JennyNeural") -> bytes:
    """
    Converts text to speech and returns MP3 audio bytes.
    """
    if not SPEECH_KEY:
        raise RuntimeError("AZURE_SPEECH_KEY not set. Check your .env file.")

    url = f"https://{SPEECH_REGION}.tts.speech.microsoft.com/cognitiveservices/v1"
    headers = {
        "Ocp-Apim-Subscription-Key": SPEECH_KEY,
        "Content-Type": "application/ssml+xml",
        "X-Microsoft-OutputFormat": "audio-16khz-32kbitrate-mono-mp3",
    }

    ssml = f"""<speak version='1.0' xml:lang='en-US'>
<voice xml:lang='en-US' name='{voice}'>{text}</voice>
</speak>"""

    response = requests.post(url, headers=headers, data=ssml.encode("utf-8"), timeout=30)
    response.raise_for_status()
    return response.content
