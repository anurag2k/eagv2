# decision.py
import asyncio
import json
from concurrent.futures import TimeoutError

async def generate_with_timeout(client, prompt, timeout=10):
    """Generate content with a timeout"""
    print("Decision: Starting LLM generation...")
    try:
        loop = asyncio.get_event_loop()
        response = await asyncio.wait_for(
            loop.run_in_executor(
                None,  
                lambda: client.models.generate_content(
                    model="gemini-2.0-flash",
                    contents=prompt
                )
            ),
            timeout=timeout
        )
        print("Decision: LLM generation completed.")
        return response
    except TimeoutError:
        print("Decision: LLM generation timed out!")
        raise
    except Exception as e:
        print(f"Decision: Error in LLM generation: {e}")
        raise

def parse_llm_json_response(response_text: str) -> dict:
    """Parses the LLM's full JSON output and extracts the necessary components."""
    try:
        # 1. Remove optional markdown code block fences
        if response_text.startswith("```"):
            response_text = response_text.strip().lstrip("```json").rstrip("```").strip()
            
        data = json.loads(response_text)
        
        # Log the reasoning components
        print("\n--- LLM Reasoning Log ---")
        print(f"STEP TYPE: {data.get('step_type', 'N/A')}")
        print(f"THOUGHT: {data.get('thought', 'N/A')}")
        print(f"CHECK: {data.get('internal_check', 'N/A')}")
        print(f"STATUS: {data.get('status', 'IN_PROGRESS')}")
        print("-------------------------")

        action = data.get('action', {})
        return {
            "action_type": action.get('type', 'ERROR'),
            "action_call": action.get('call', 'N/A'),
            "status": data.get('status', 'IN_PROGRESS')
        }
    except json.JSONDecodeError as e:
        print(f"Decision ERROR: Failed to decode JSON from LLM response. Error: {e}")
        print(f"Decision ERROR: Raw text was: {response_text}")
        return {"action_type": "ERROR", "action_call": "N/A", "status": "FATAL_ERROR"}
    except Exception as e:
        print(f"Decision ERROR: Unexpected error during JSON parsing: {e}")
        return {"action_type": "ERROR", "action_call": "N/A", "status": "FATAL_ERROR"}

async def make_decision(llm_prompt: str, preferences: dict, llm_client) -> dict:
    """
    Takes the facts (prompt) and preferences, invokes the LLM, 
    and parses the result into a structured decision.
    """
    print("Decision: Making decision...")
    
    # Preferences are not used here, but could be.
    # e.g., if preferences['log_level'] == 'verbose': 
    #   llm_prompt += "\nProvide extra verbose thoughts."

    try:
        response = await generate_with_timeout(llm_client, llm_prompt)
        response_text = response.text.strip()
        print(f"Decision: LLM Raw Response: {response_text}")
        
        parsed_data = parse_llm_json_response(response_text)
        print(f"Decision: Parsed action: {parsed_data}")
        return parsed_data
        
    except Exception as e:
        print(f"Decision: Failed to get LLM response: {e}")
        return {"action_type": "ERROR", "action_call": "N/A", "status": "FATAL_ERROR"}
