import os
from dotenv import load_dotenv
from mcp import ClientSession, StdioServerParameters, types
from mcp.client.stdio import stdio_client
import asyncio
from google import genai
from concurrent.futures import TimeoutError
from functools import partial
import json
import traceback

# Load environment variables from .env file
load_dotenv()

# Access your API key and initialize Gemini client correctly
api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

max_iterations = 5
last_response = None
iteration = 0
iteration_response = []

import subprocess

def activate_preview():
    script = '''
    tell application "Preview"
        activate
    end tell
    '''
    subprocess.run(["osascript", "-e", script])

async def generate_with_timeout(client, prompt, timeout=10):
    """Generate content with a timeout"""
    print("Starting LLM generation...")
    try:
        # Convert the synchronous generate_content call to run in a thread
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
        print("LLM generation completed")
        return response
    except TimeoutError:
        print("LLM generation timed out!")
        raise
    except Exception as e:
        print(f"Error in LLM generation: {e}")
        raise

def reset_state():
    """Reset all global variables to their initial state"""
    global last_response, iteration, iteration_response
    last_response = None
    iteration = 0
    iteration_response = []

def parse_llm_json_response(response_text):
    """Parses the LLM's full JSON output and extracts the necessary components."""
    try:
        # LLM response must be a valid JSON block
        data = json.loads(response_text)
        
        # Log the reasoning components (for debugging and transparency)
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
        print(f"ERROR: Failed to decode JSON from LLM response. Error: {e}")
        # Return an error state if parsing fails (Criteria 8 Fallback)
        return {"action_type": "ERROR", "action_call": "N/A", "status": "FATAL_ERROR"}
    except Exception as e:
        print(f"ERROR: Unexpected error during JSON parsing: {e}")
        return {"action_type": "ERROR", "action_call": "N/A", "status": "FATAL_ERROR"}


async def main():
    reset_state()  # Reset at the start of main
    print("Starting main execution...")
    try:
        # Create a single MCP server connection
        print("Establishing connection to MCP server...")
        server_params = StdioServerParameters(
            command="python",
            args=["mcp-server.py"]
        )

        async with stdio_client(server_params) as (read, write):
            print("Connection established, creating session...")
            async with ClientSession(read, write) as session:
                print("Session created, initializing...")
                await session.initialize()
                
                # Get available tools
                print("Requesting tool list...")
                tools_result = await session.list_tools()
                tools = tools_result.tools
                print(f"Successfully retrieved {len(tools)} tools")

                # Create system prompt with available tools
                print("Creating system prompt...")
                print(f"Number of tools: {len(tools)}")

                try:
                    # First, let's inspect what a tool object looks like
                    # if tools:
                    #     print(f"First tool properties: {dir(tools[0])}")
                    #     print(f"First tool example: {tools[0]}")
                    
                    tools_description = []
                    for i, tool in enumerate(tools):
                        try:
                            # Get tool properties
                            params = tool.inputSchema
                            desc = getattr(tool, 'description', 'No description available')
                            name = getattr(tool, 'name', f'tool_{i}')
                            
                            # Format the input schema in a more readable way
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
                            print(f"Added description for tool: {tool_desc}")
                        except Exception as e:
                            print(f"Error processing tool {i}: {e}")
                            tools_description.append(f"{i+1}. Error processing tool")
                    
                    tools_description = "\n".join(tools_description)
                    print("Successfully created tools description")
                except Exception as e:
                    print(f"Error creating tools description: {e}")
                    tools_description = "Error loading tools"
                
                # Define the new system prompt that enforces the JSON structure for reasoning and action.
                print("Created new structured system prompt...")

                # Note: The actual content here MUST match the exact JSON structure defined 
                # in the "Revised Prompt: Structured Reasoning and Tool Agent"
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

                #query = """Find the ASCII values of characters in INDIA and then return sum of exponentials of those values. """
                query = """Add 5 and 4 and return square of the resultant value"""
                print("Starting iteration loop...")
            
                # Use global iteration variables
                global iteration, last_response

                print(f"System Prompt {system_prompt}")
                print("Starting iteration loop...")

                # Use global iteration variables
                global iteration, last_response
                last_response = None
                # iteration_response will now be a list of results to append to the query context
                iteration_response = []

                while iteration < max_iterations:
                    print(f"\n--- Iteration {iteration + 1} ---")
                    
                    # --- Conversation Loop Context Preparation ---
                    if last_response is None:
                        current_query = query
                        context_update = "Previous Tool Result: N/A (First turn)"
                    else:
                        # This joins the formatted results from previous tool executions
                        context_history = "\n".join(iteration_response)
                        context_update = f"Previous Tool Results History:\n{context_history}"

                    # --- Generate LLM Response ---
                    print("Preparing to generate LLM response...")
                    
                    # The prompt now includes the full structured system prompt + context
                    prompt = f"{system_prompt}\n\nUSER QUERY: {query}\n\nCONTEXT: {context_update}"
                    
                    try:
                        response = await generate_with_timeout(client, prompt)
                        response_text = response.text.strip()
                        print(f"LLM Raw Response: {response_text}")
                        
                        # 1. Remove optional markdown code block fences and language specifier (e.g., ```json)
                        if response_text.startswith("```"):
                            response_text = response_text.strip().lstrip("```json").rstrip("```").strip()
                        # --- Parse the JSON Response ---
                        parsed_data = parse_llm_json_response(response_text)
                        action_type = parsed_data['action_type']
                        action_call = parsed_data['action_call']
                        status = parsed_data['status']
                        
                    except Exception as e:
                        print(f"Failed to get LLM response: {e}")
                        break

                    # --- Handle Parsed Actions ---

                    if action_type == "FUNCTION_CALL":
                        # Extract function name and parameters from the strict "func|p1|p2" format
                        if '|' not in action_call:
                            print(f"FATAL: Malformed FUNCTION_CALL format: {action_call}")
                            break
                            
                        parts = [p.strip() for p in action_call.split("|")]
                        func_name, params = parts[0], parts[1:]

                        print(f"\nDEBUG: Raw function info: {action_call}")
                        print(f"DEBUG: Split parts: {parts}")
                        print(f"DEBUG: Function name: {func_name}")
                        print(f"DEBUG: Raw parameters: {params}")

                        try:
                            # Find the matching tool to get its input schema
                            tool = next((t for t in tools if t.name == func_name), None)
                            if not tool:
                                print(f"DEBUG: Available tools: {[t.name for t in tools]}")
                                raise ValueError(f"Unknown tool: {func_name}")

                            print(f"DEBUG: Found tool: {tool.name}")
                            print(f"DEBUG: Tool schema: {tool.inputSchema}")

                            # Prepare arguments according to the tool's input schema
                            arguments = {}
                            schema_properties = tool.inputSchema.get('properties', {})
                            print(f"DEBUG: Schema properties: {schema_properties}")

                            for param_name, param_info in schema_properties.items():
                                if not params:  # Check if we have enough parameters
                                    raise ValueError(f"Not enough parameters provided for {func_name}")

                                value = params.pop(0)  # Get and remove the first parameter
                                param_type = param_info.get('type', 'string')

                                print(f"DEBUG: Converting parameter {param_name} with value {value} to type {param_type}")

                                # Convert the value to the correct type based on the schema
                                if param_type == 'integer':
                                    arguments[param_name] = int(value)
                                elif param_type == 'number':
                                    arguments[param_name] = float(value)
                                elif param_type == 'array':
                                    # Handle array input
                                    if isinstance(value, str):
                                        value = value.strip('[]').split(',')
                                    arguments[param_name] = [int(x.strip()) for x in value]
                                else:
                                    arguments[param_name] = str(value)

                            print(f"DEBUG: Calling tool {func_name}")
                            print(f"\nDEBUG: Calling tool: {func_name}, Parameters: {arguments}")

                            result = await session.call_tool(func_name, arguments=arguments)
                            print(f"DEBUG: Raw result: {result}")

                            # Get the full result content
                            if hasattr(result, 'content'):
                                print(f"DEBUG: Result has content attribute")
                                # Handle multiple content items
                                if isinstance(result.content, list):
                                    iteration_result = [
                                        item.text if hasattr(item, 'text') else str(item)
                                        for item in result.content
                                    ]
                                else:
                                    iteration_result = str(result.content)
                            else:
                                print(f"DEBUG: Result has no content attribute")
                    
                            # --- Format Result for Context Update ---
                            # Extract content from the result object (simplified for this example)
                            tool_result_content = result.content[0].text if hasattr(result, 'content') and result.content else str(result)
                            last_response = tool_result_content

                            # Store formatted output for the next turn's context history
                            iteration_response.append(
                                f"TOOL RESULT from {func_name}: {tool_result_content}"
                            )
                            
                        except Exception as e:
                            # Diagnostic 1: Print the type and arguments of the exception
                            print(f"Exception Type: {type(e)}")
                            print(f"Exception Args: {e.args}")
                            print(f"Exception Message (str(e)): {str(e)}")

                    elif action_type == "FINAL_ANSWER":
                        print("\n=== Agent Execution Complete ===")
                        print(f"Final Answer: {action_call}")
                        
                        # Original code's final call (retained for completeness)
                        #result = await session.call_tool("open_paint") 
                        print(result.content[0].text) 
                        break
                        
                    elif action_type == "NO_ACTION":
                        # Handle NO_ACTION: LLM is only performing internal reasoning (Criteria 3)
                        print("\nAgent performed internal reasoning step (NO_ACTION). Continuing loop...")
                        
                        if status in ["UNCERTAIN_RETRY", "FATAL_ERROR"]:
                            print(f"Agent is re-evaluating under status: {status}. Loop continues.")
                        
                        # Don't add a tool result, but ensure context knows an internal step happened
                        iteration_response.append(f"INTERNAL REASONING STEP: Agent is re-evaluating its plan.")
                        last_response = None # No new tool result to process

                    else:
                        # Handle Parsing Errors (Criteria 8)
                        print(f"FATAL: Invalid action type '{action_type}' or parsing error. Aborting.")
                        break
                
                    iteration += 1
                

    except Exception as e:
        print(f"Error in main execution: {e}")
        import traceback
        traceback.print_exc()
    finally:
        reset_state()  # Reset at the end of main

if __name__ == "__main__":
    asyncio.run(main())
    
