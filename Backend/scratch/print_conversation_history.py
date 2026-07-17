import asyncio
import sys
import os
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from qa_simulator import QASimulator, generate_qa_response_prompt
from db.db_manager import db
from llm.state_manager import StateManager
from llm.llm import generate_response, get_llm_client

async def main():
    agent_id = "b848f004-1cc1-4c7e-9dd4-749ecfd9c4fc"
    schema_path = f"db/agents/{agent_id}.json"
    
    await db.initialize()
    state_manager = StateManager(schema_path)
    state_manager.reset_state()
    qa_client = get_llm_client()
    
    conversation_history = []
    
    # 1. Greeting
    print("--- STARTING CONVERSATION ---")
    greeting_result = await generate_response(
        "[System: The call has just been connected. No user has spoken yet. Speak only for the current conversation node and do not transition.]",
        [],
        state_manager=state_manager,
        allow_transition=False,
    )
    greeting = greeting_result[0] if isinstance(greeting_result, tuple) else greeting_result
    print(f"Agent: {greeting}")
    conversation_history.append({"role": "assistant", "content": greeting})
    
    scenario = "You are a cooperative student. You want to enroll in a Data Science course. Tell them your course interest first, wait for them to ask education level, then say you have a Bachelor's degree."
    
    for turn in range(4):
        # QA Agent turn
        qa_prompt = generate_qa_response_prompt(scenario, conversation_history, greeting, agent_type="education")
        completion = await qa_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=qa_prompt,
            temperature=0.7,
            max_tokens=100
        )
        human_text = completion.choices[0].message.content
        print(f"User:  {human_text}")
        conversation_history.append({"role": "user", "content": human_text})
        
        # Target Agent turn
        ai_response_result = await generate_response(
            human_text,
            conversation_history,
            state_manager=state_manager,
        )
        ai_response = ai_response_result[0] if isinstance(ai_response_result, tuple) else ai_response_result
        print(f"Agent: {ai_response}")
        conversation_history.append({"role": "assistant", "content": ai_response})
        
        print("STATE DATA:", {k: v for k, v in state_manager.conversation_data.items() if k not in {"memory", "asked_flags", "last_response", "active_language"}})
        if state_manager.is_terminal_node():
            print("--- CONVERSATION TERMINATED GRACEFULLY ---")
            break

asyncio.run(main())
