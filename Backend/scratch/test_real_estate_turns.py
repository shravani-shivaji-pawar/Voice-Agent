import asyncio
import sys
import logging
from pathlib import Path

# Setup logging to console so we see all agent logs
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

sys.path.append(str(Path(__file__).parent.parent))

from llm.state_manager import StateManager
from llm.llm import extract_intent, generate_response

async def run_turn(state_manager, user_text, lang="en"):
    print(f"\n======================================")
    print(f"USER UTTERANCE: '{user_text}' (lang={lang})")
    
    # 1. Generate response which internally extracts intent, runs transition, and generates response
    response, is_terminal = await generate_response(
        user_text,
        language=lang,
        state_manager=state_manager,
        allow_transition=True
    )
    
    print(f"INTENT CLASSIFIED: {state_manager._last_user_text}") # Since it logs
    print(f"CURRENT NODE ID: {state_manager.current_node_id} ({state_manager.get_current_node().get('name')})")
    print(f"AGENT RESPONSE: '{response}'")
    print(f"IS TERMINAL: {is_terminal}")
    print(f"CONVERSATION DATA: { {k: v for k, v in state_manager.conversation_data.items() if k not in {'memory', 'asked_flags', 'last_response', 'active_language'}} }")
    return is_terminal

async def main():
    schema_path = "db/agents/real_estate_sales.json"
    state_manager = StateManager(schema_path)
    state_manager.reset_state()
    
    # Init greeting
    print("Initializing Greeting...")
    turn = state_manager.execute_greeting_transition("Hello")
    print("Greeting Response Template:", turn.node.get("response"))
    print("Current node ID:", state_manager.current_node_id)
    
    # Turn 1: Greet
    await run_turn(state_manager, "I'm Prashant.", lang="en")
    
    # Turn 2: Availability
    await run_turn(state_manager, "Yes.", lang="en")
    
    # Turn 3: Ask city, off topic question
    await run_turn(state_manager, "But what does this company do?", lang="en")
    
    # Turn 4: User says "हाँ, हाँ."
    await run_turn(state_manager, "हाँ, हाँ.", lang="hi")
    
    # Turn 5: User says "उजए पूर।"
    await run_turn(state_manager, "उजए पूर।", lang="hi")

if __name__ == "__main__":
    asyncio.run(main())
