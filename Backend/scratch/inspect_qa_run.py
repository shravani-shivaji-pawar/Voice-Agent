import asyncio
import os
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from qa_simulator import QASimulator
from db.db_manager import db

async def main():
    agent_id = "b848f004-1cc1-4c7e-9dd4-749ecfd9c4fc"
    schema_path = f"db/agents/{agent_id}.json"
    
    print(f"Schema path exists: {os.path.exists(schema_path)}")
    
    await db.initialize()
    simulator = QASimulator(db)
    try:
        report = await simulator.run_full_qa_suite(agent_id, schema_path)
        print(f"\nOVERALL SCORE: {report.get('overall_score')}\n")
        print("\nFAILURES:")
        for fail in report.get("failures", []):
            print(fail)
            
        print("\n--- CONVERSATION HISTORIES ---")
        histories = report.get("histories", {})
        for key, history in histories.items():
            print(f"\nScenario: {key}")
            for msg in history:
                print(f"  {msg.get('role').capitalize()}: {msg.get('content')}")
    except Exception as e:
        import traceback
        print(f"CRASH: {e}")
        traceback.print_exc()

asyncio.run(main())
