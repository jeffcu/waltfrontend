import os

class VoiceConfig:
    def __init__(self):
        self.openai_api_key = os.environ.get("OPENAI_API_KEY")  # Or get from config file
        self.default_voice_api = "openai"  # Default to OpenAI, can be "google", "aws", etc.
        self.voice_enabled = os.environ.get("WALTX_VOICE_ENABLED", "False").lower() == "true" # Env var to enable/disable
        self.tts_voice_id = os.environ.get("WALTX_TTS_VOICE_ID", "alloy") # Default OpenAI voice

voice_config = VoiceConfig() # Instantiate config
