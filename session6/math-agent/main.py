# main.py
import os
import asyncio
import traceback
from dotenv import load_dotenv
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from google import genai

# Import the new modules
import perception
import memory
import decision
import action

# Load environment variables
load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")
if not API_KEY:
    raise EnvironmentError("GEMINI_API_KEY not found in .env file")

# Initialize the Gemini client
llm_client = genai.Client(api_key=API_KEY)


async def main():
    print("Orchestrator: Starting main execution...")
    
    # 1. Initialize State
    # Global variables are replaced by this state dictionary
    state = {
        'iteration': 0,
        'history': [],
        'max_iterations': 20 
    }
    user_query = "Add 5 and 4 and return square of the resultant value"

    try:
        # 2. Initialize MCP Connection
        print("Orchestrator: Establishing connection to MCP server...")
        server_params = StdioServerParameters(
            command="python",
            args=["mcp-server2.py"] # Ensure this server file is accessible
        )

        async with stdio_client(server_params) as (read, write):
            print("Orchestrator: Connection established, creating session...")
            async with ClientSession(read, write) as session:
                await session.initialize()
                print("Orchestrator: Session created.")
                
                # 3. Initial Perception: Get tool info once
                tools_result = await session.list_tools()
                tools = tools_result.tools
                print(f"Orchestrator: Retrieved {len(tools)} tools.")
                
                # Format tools and create the static system prompt
                tools_description = perception.format_tool_description(tools)
                system_prompt = perception.build_system_prompt(tools_description)

                # 4. Start the Agent Loop
                print(f"Orchestrator: Starting agent loop for query: '{user_query}'")
                
                while state['iteration'] < state['max_iterations']:
                    print(f"\n--- Orchestrator: Iteration {state['iteration'] + 1} ---")
                    
                    # --- STAGE 1: PERCEPTION ---
                    # Gather all facts, including history, into a prompt
                    facts = perception.perceive(user_query, state, system_prompt)
                    
                    # --- STAGE 2: MEMORY ---
                    # Get user preferences (stubbed for now)
                    preferences = memory.get_preferences(user_id="default_user")
                    
                    # --- STAGE 3: DECISION ---
                    # Call the LLM with the prompt and get a structured action
                    decided_action = await decision.make_decision(
                        facts['full_llm_prompt'], 
                        preferences, 
                        llm_client
                    )
                    
                    # --- STAGE 4: ACTION ---
                    # Execute the structured action (call tool, print answer, etc.)
                    action_result = await action.execute_action(
                        decided_action, 
                        session, 
                        tools
                    )
                    
                    # --- ORCHESTRATION: Update State ---
                    state['history'].append(action_result['history_entry'])
                    state['iteration'] += 1
                    
                    # Check if the loop should terminate
                    if action_result['status'] in ['DONE', 'FATAL_ERROR']:
                        print(f"Orchestrator: Loop ending with status: {action_result['status']}")
                        break
                
                if state['iteration'] >= state['max_iterations']:
                    print("Orchestrator: Reached max iterations. Halting.")

    except Exception as e:
        print(f"Orchestrator ERROR: Unhandled exception in main: {e}")
        traceback.print_exc()
    finally:
        print("Orchestrator: Main execution finished.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nOrchestrator: Execution cancelled by user.")
