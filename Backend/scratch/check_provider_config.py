import sys
from pathlib import Path

backend_path = Path(__file__).resolve().parent.parent
if str(backend_path) not in sys.path:
    sys.path.insert(0, str(backend_path))

from dotenv import load_dotenv
load_dotenv()

from tts.provider import _provider_config_from_agent_schema
print("Provider config resolved:")
try:
    print(_provider_config_from_agent_schema("tts-test-agent"))
except Exception as e:
    import traceback
    traceback.print_exc()
