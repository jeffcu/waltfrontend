import openai
from .voice_interface import VoiceAPIInterface  # Corrected import
import os
import logging

class OpenAI_VoiceAPI(VoiceAPIInterface):
    def __init__(self, openai_api_key=None):
        self.openai_api_key = openai_api_key or os.environ.get("OPENAI_API_KEY")
        if not self.openai_api_key:
            raise ValueError("OpenAI API key is required for Voice API.")
        self.client = openai.Client(api_key=self.openai_api_key)

    def transcribe_audio(self, audio_file_path):
        """Transcribes audio using OpenAI Whisper API."""
        try:
            with open(audio_file_path, "rb") as audio_file:
                transcript = self.client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file
                )
                return transcript.text.strip()
        except Exception as e:
            logging.error(f"OpenAI Whisper API error: {e}")
            raise ValueError(f"Speech-to-text error: {e}") from e


    def synthesize_speech(self, text, output_file_path, voice_id="alloy"): # Default voice
        """Synthesizes speech using OpenAI TTS API."""
        try:
            response = self.client.audio.speech.create(
                model="tts-1", # Or "tts-1-hd" for higher quality, slower
                voice=voice_id, # Use voice_id parameter
                input=text
            )
            response.stream_to_file(output_file_path) # Stream directly to file
            return output_file_path # Return the path to the created audio file
        except Exception as e:
            logging.error(f"OpenAI TTS API error: {e}")
            raise ValueError(f"Text-to-speech error: {e}") from e
