from abc import ABC, abstractmethod

class VoiceAPIInterface(ABC):
    @abstractmethod
    def transcribe_audio(self, audio_file_path):
        """Transcribes audio from a file to text."""
        pass

    @abstractmethod
    def synthesize_speech(self, text, output_file_path, voice_id=None):
        """Synthesizes speech from text and saves to a file."""
        pass
