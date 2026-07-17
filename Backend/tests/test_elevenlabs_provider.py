import os
import sys
import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from tts import provider
from tts import elevenlabs_tts


class ElevenLabsProviderTest(unittest.TestCase):
    def setUp(self):
        self._env = os.environ.copy()

    def tearDown(self):
        os.environ.clear()
        os.environ.update(self._env)
        provider._AGENT_CONFIG_CACHE.clear()

    @patch("elevenlabs.client.ElevenLabs")
    def test_elevenlabs_stream_generation(self, mock_elevenlabs_client):
        # Setup mock client
        mock_client_instance = MagicMock()
        mock_elevenlabs_client.return_value = mock_client_instance
        
        # Mock the chunk iterator returned by client.text_to_speech.convert
        mock_client_instance.text_to_speech.convert.return_value = [b"chunk1", b"chunk2"]
        
        os.environ["ELEVENLABS_API_KEY"] = "fake-key"
        
        # Consume the stream
        chunks = list(elevenlabs_tts.generate_speech_stream(
            text="Hello world",
            voice_id="fake-voice-id",
            model="eleven_flash_v2_5"
        ))
        
        # Filters out empty chunks
        chunks = [c for c in chunks if c]
        
        # Verify convert was called with correct parameters
        mock_client_instance.text_to_speech.convert.assert_called_once()
        kwargs = mock_client_instance.text_to_speech.convert.call_args[1]
        self.assertEqual(kwargs["voice_id"], "fake-voice-id")
        self.assertEqual(kwargs["model_id"], "eleven_flash_v2_5")
        self.assertEqual(kwargs["output_format"], "pcm_24000")
        
        # Verify we got chunks back
        self.assertTrue(len(chunks) > 0)

    def test_missing_api_key_raises_error(self):
        os.environ["ELEVENLABS_API_KEY"] = ""
        
        with self.assertRaises(Exception):
            list(elevenlabs_tts.generate_speech_stream("Hello"))


if __name__ == "__main__":
    unittest.main()
