import asyncio
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from llm.state_manager import StateManager
from llm.llm import extract_intent
from llm.llm_response_generator import generate_response_for_turn

async def main():
    agent_id = "b848f004-1cc1-4c7e-9dd4-749ecfd9c4fc"
    schema_path = f"db/agents/{agent_id}.json"
    
    state_manager = StateManager(schema_path)
    state_manager.reset_state()
    
    # 1. Start with greeting transition
    turn_1 = state_manager.execute_greeting_transition("Hello")
    print("Greeting Node ID:", turn_1.node["id"]) # Smart Greeting
    
    # 2. Transition on greeting response
    user_text_1 = "Yes, I'm Prashant. I want to enroll in a Data Science course."
    intent_data_1 = await extract_intent(user_text_1, state_manager=state_manager)
    print("\n--- TURN 1 ---")
    print("User Text:", user_text_1)
    print("Intent:", intent_data_1)
    
    turn_2 = state_manager.execute_transition(user_text_1, intent_data_1)
    print("Resolved Node:", turn_2.node["id"], turn_2.node.get("name"))
    print("State Data after Turn 1:", {k: v for k, v in state_manager.conversation_data.items() if k not in {"memory", "asked_flags", "last_response", "active_language"}})
    
    # 3. Transition on discovery response
    user_text_2 = "I'm looking to enhance my skills in data analysis and machine learning, preferably a course that covers Python."
    intent_data_2 = await extract_intent(user_text_2, state_manager=state_manager)
    print("\n--- TURN 2 ---")
    print("User Text:", user_text_2)
    print("Intent:", intent_data_2)
    
    turn_3 = state_manager.execute_transition(user_text_2, intent_data_2)
    print("Resolved Node:", turn_3.node["id"], turn_3.node.get("name"))
    print("State Data after Turn 2:", {k: v for k, v in state_manager.conversation_data.items() if k not in {"memory", "asked_flags", "last_response", "active_language"}})
    
    response_3 = await generate_response_for_turn(turn_3, state_manager=state_manager)
    print("Generated Agent Response:", response_3)

asyncio.run(main())
