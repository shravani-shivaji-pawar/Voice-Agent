import inspect
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from llm.state_manager import StateManager

print("Methods in StateManager:")
for name, member in inspect.getmembers(StateManager, predicate=inspect.isfunction):
    print(f"- {name}{inspect.signature(member)}")
