import ast
import traceback
from mcp import ClientSession
from models import AddInput, AddOutput, SqrtInput, SqrtOutput, StringsToIntsInput, StringsToIntsOutput, ExpSumInput, ExpSumOutput

def parse_function_call_params(param_parts: list[str]) -> dict:
    """
    Parses key=value parts from the FUNCTION_CALL format.
    Supports nested keys like input.string=foo and list values like input.int_list=[1,2,3]
    Returns a nested dictionary.
    """
    print(f"Action: Parsing parameters: {param_parts}")
    result = {}

    for part in param_parts:
        if "=" not in part:
            raise ValueError(f"Invalid parameter format (expected key=value): {part}")

        key, value = part.split("=", 1)

        # Try to parse as Python literal (int, float, list, etc.)
        try:
            parsed_value = ast.literal_eval(value)
        except Exception:
            parsed_value = value.strip() # Default to string

        # Support nested keys like input.string
        keys = key.split(".")
        current = result
        for k in keys[:-1]:
            current = current.setdefault(k, {})
        current[keys[-1]] = parsed_value
    
    print(f"Action: Parsed arguments: {result}")
    return result

async def execute_action(decision: dict, mcp_session: ClientSession, tools: list) -> dict:
    """
    Executes the action decided by the Decision module.
    Returns a result dictionary for the orchestrator.
    """
    action_type = decision['action_type']
    action_call = decision['action_call']
    
    print(f"Action: Executing action_type: {action_type}")
    
    try:
        if action_type == "FUNCTION_CALL":
            # --- Parse the function call string ---
            if '|' not in action_call:
                print(f"Action FATAL: Malformed FUNCTION_CALL format: {action_call}")
                return {'status': 'FATAL_ERROR', 'history_entry': f"ERROR: Malformed call {action_call}"}
                
            parts = [p.strip() for p in action_call.split("|")]
            func_name, params_list = parts[0], parts[1:]
            
            print(f"Action: Attempting to call function '{func_name}' with params {params_list}")

            # --- Find the tool ---
            tool = next((t for t in tools if t.name == func_name), None)
            if not tool:
                raise ValueError(f"Unknown tool: {func_name}")

            # --- Parse key=value parameters ---
            # This is the fix: using `params_list`
            arguments = parse_function_call_params(params_list)
            
            # --- Call the MCP Tool ---
            print(f"Action: Calling MCP tool: {func_name} with args: {arguments}")
            result = await mcp_session.call_tool(func_name, arguments=arguments)
            
            # --- Format the result ---
            tool_result_content = "N/A"
            if hasattr(result, 'content') and result.content:
                if isinstance(result.content, list):
                    # Handle list content, get text from first item
                    tool_result_content = result.content[0].text if hasattr(result.content[0], 'text') else str(result.content[0])
                else:
                    tool_result_content = str(result.content)
            
            print(f"Action: Tool result: {tool_result_content}")
            
            return {
                'status': 'IN_PROGRESS',
                'history_entry': f"TOOL RESULT from {func_name}: {tool_result_content}"
            }

        elif action_type == "FINAL_ANSWER":
            print("\n=== Agent Execution Complete ===")
            print(f"Final Answer: {action_call}")
            return {
                'status': 'DONE',
                'history_entry': f"Final Answer: {action_call}"
            }
            
        elif action_type == "NO_ACTION":
            print("Action: Agent performed internal reasoning (NO_ACTION).")
            return {
                'status': 'IN_PROGRESS',
                'history_entry': "INTERNAL REASONING STEP: Agent is re-evaluating its plan."
            }
            
        else: # ERROR or unknown
            print(f"Action FATAL: Invalid action type '{action_type}' or parsing error.")
            return {
                'status': 'FATAL_ERROR',
                'history_entry': f"ERROR: Invalid action type '{action_type}'."
            }
            
    except Exception as e:
        print(f"Action ERROR: Failed during execution: {e}")
        traceback.print_exc()
        return {
            'status': 'FATAL_ERROR',
            'history_entry': f"EXECUTION ERROR: {str(e)}"
        }

