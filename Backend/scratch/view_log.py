from pathlib import Path

log_path = Path(__file__).parent.parent / "voice_agent.log"
print(f"Reading logs from {log_path} (exists: {log_path.exists()})")

with open(log_path, "r", encoding="utf-8", errors="ignore") as f:
    lines = f.readlines()
    print("\n".join(lines[-100:]))
