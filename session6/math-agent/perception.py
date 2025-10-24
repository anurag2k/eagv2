# perception.py
import json

def format_tool_description(tools) -> str:
    """Converts the MCP tool list into a human-readable string for the prompt."""
    print("Perception: Formatting tool descriptions...")
    tools_description = []
    for i, tool in enumerate(tools):
        try:
            params = tool.inputSchema
            desc = getattr(tool, 'description', 'No description available')
            name = getattr(tool, 'name', f'tool_{i}')
            
            if 'properties' in params:
                param_details = []
                for param_name, param_info in params['properties'].items():
                    param_type = param_info.get('type', 'unknown')
                    param_details.append(f"{param_name}: {param_type}")
                params_str = ', '.join(param_details)
            else:
                params_str = 'no parameters'
            
            tool_desc = f"{i+1}. {name}({params_str}) - {desc}"
            tools_description.append(tool_desc)
        except Exception as e:
            print(f"Error processing tool {i}: {e}")
            tools_description.append(f"{i+1}. Error processing tool")
            
    return "\n".join(tools_description)

def build_system_prompt(tools_description: str) -> str:
    """Creates the main system prompt with instructions and tool definitions."""
    print("Perception: Building system prompt...")
    
    # This is the core instruction set for the LLM
    system_prompt = f"""You are a Structured Mathematical Reasoning Agent. Your goal is to solve complex problems in iterations by applying step-by-step reasoning, utilizing available tools, and adhering to a strict output format.

Available tools:
{tools_description}

You MUST respond to every turn with a complete, multi-line JSON object that strictly adheres to the schema below. Do not include any text, code blocks, or comments outside of the JSON object itself.

JSON Schema:
{{
  "step_type": "...",
  "thought": "...",
  "internal_check": "...",
  "action": {{
    "type": "...",
    "call": "..."
  }},
  "status": "..."
}}

Instructional Breakdown:
- step_type: [PLAN, ARITHMETIC, LOGIC, LOOKUP, VERIFICATION]. Identify the reasoning type.
- thought: Detailed, step-by-step explanation of your current logic.
- internal_check: Self-validation, e.g., 'Passed: parameters look correct' or 'Revised: [What was fixed]'.
- action.type: [FUNCTION_CALL, FINAL_ANSWER, NO_ACTION].
- action.call: The command string (e.g., 'add|5|3') or the final answer (e.g., '[42]'). Use 'N/A' for NO_ACTION.
- status: [IN_PROGRESS, DONE, UNCERTAIN_RETRY, FATAL_ERROR]. Use FATAL_ERROR only if the problem is unsolvable.
"""
    return system_prompt

def perceive(user_query: str, state: dict, system_prompt: str) -> dict:
    """
    Gathers all facts (query, history, system prompt) and generates the 
    JSON object (as requested) containing the final prompt for the LLM.
    """
    print(f"Perception: Gathering facts for iteration {state['iteration'] + 1}...")
    
    # 1. Get history from state
    history = state.get('history', [])
    
    # 2. Format context update
    if not history:
        context_update = "Previous Tool Result: N/A (First turn)"
    else:
        context_history = "\n".join(history)
        context_update = f"Previous Tool Results History:\n{context_history}"
        
    # 3. Assemble the full prompt
    full_llm_prompt = f"{system_prompt}\n\nUSER QUERY: {user_query}\n\nCONTEXT: {context_update}"
    
    # 4. Generate the facts JSON
    facts_json = {
        "user_query": user_query,
        "context_update": context_update,
        "system_prompt": system_prompt,
        "full_llm_prompt": full_llm_prompt
    }
    
    print("Perception: Facts gathered and prompt generated.")
    # print(f"Perception: Generated prompt:\n{full_llm_prompt}") # Uncomment for debugging
    return facts_json
