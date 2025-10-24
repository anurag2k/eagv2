# action.py
import subprocess
import traceback

def activate_preview():
    """Helper function to activate Preview.app (unused in main flow)."""
    script = '''
    tell application "Preview"
        activate
    end tell
    '''
    subprocess.run(["osascript", "-e", script])

async def execute_action(decision: dict, mcp_session, tools: list) -> dict:
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

            # --- Find the tool and build arguments ---
            tool = next((t for t in tools if t.name == func_name), None)
            if not tool:
                raise ValueError(f"Unknown tool: {func_name}")

            arguments = {}
            schema_properties = tool.inputSchema.get('properties', {})
            
            for param_name, param_info in schema_properties.items():
                if not params_list:
                    raise ValueError(f"Not enough parameters provided for {func_name}")
                
                value = params_list.pop(0)
                param_type = param_info.get('type', 'string')
                
                # --- Type conversion based on schema ---
                if param_type == 'integer':
                    arguments[param_name] = int(value)
                elif param_type == 'number':
                    arguments[param_name] = float(value)
                elif param_type == 'array':
                    if isinstance(value, str):
                        value = value.strip('[]').split(',')
                    arguments[param_name] = [int(x.strip()) for x in value] # Assuming int array
                else:
                    arguments[param_name] = str(value)
            
            # --- Call the MCP Tool ---
            print(f"Action: Calling MCP tool: {func_name} with args: {arguments}")
            result = await mcp_session.call_tool(func_name, arguments=arguments)
            
            # --- Format the result ---
            tool_result_content = "N/A"
            if hasattr(result, 'content') and result.content:
                if isinstance(result.content, list):
                    tool_result_content = result.content[0].text
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
