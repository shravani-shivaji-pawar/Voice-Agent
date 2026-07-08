import asyncio
import json
import logging
import sys
from pathlib import Path

# Add parent dir to path so we can import llm
sys.path.append(str(Path(__file__).parent.parent))

from llm.llm import get_llm_client
import llm.config as cfg
from intelligence.extraction import LLM_EXTRACTION_SYSTEM_PROMPT

logging.basicConfig(level=logging.INFO)

async def main():
    print(f"GROQ_API_KEY set: {bool(cfg.GROQ_API_KEY)}")
    print(f"MODEL_NAME: {cfg.MODEL_NAME}")
    
    client = get_llm_client()
    messages = [
        {"role": "system", "content": LLM_EXTRACTION_SYSTEM_PROMPT},
        {"role": "user", "content": "Here is the crawled website text:\nThis is Google. We do search, cloud, and advertising. Founded in 1998 by Larry Page and Sergey Brin."}
    ]
    try:
        completion = await client.chat.completions.create(
            model=cfg.MODEL_NAME,
            messages=messages,
            temperature=0.0,
            max_tokens=4000,
            response_format={"type": "json_object"},
        )
        content = completion.choices[0].message.content
        print("Success! Response:")
        print(content)
    except Exception as e:
        print("Failed with exception:")
        import traceback
        traceback.print_exc()

asyncio.run(main())
