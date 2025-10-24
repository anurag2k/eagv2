Below is the complete raw Markdown source for the README.md file. You can copy the text directly from this code block:

# Structured Math Agent

## 1. Problem Description

This agent is designed to solve multi-step arithmetic and logic problems. Instead of attempting to solve a complex query (e.g., "Add 5 and 4 and return the square of the result") in a single pass, this agent breaks the problem down into a series of discrete steps.

It operates in a loop, much like a human would, by:

1. **Thinking** about the problem.

2. **Deciding** on a single, small action to perform (like "add 5 and 4").

3. **Using** an external tool (an MCP tool) to execute that action.

4. **Observing** the result (e.g., "9").

5. **Repeating** the process with the new information (e.g., "Now I need to square 9") until a final answer is reached.

This approach allows the agent to handle complex, chained computations reliably by leveraging specialized, pre-defined tools (like `add`, `subtract`, `square`).

## 2. High-Level Agent Architecture

The agent's logic is refactored from a single monolithic file into a modular, five-part **agentic loop**. This separation of concerns makes the agent easier to maintain, debug, and extend.

The core architecture follows this flow:

1. **Main (Orchestrator)**: Manages the overall state and loop.

2. **Perception**: Gathers all "facts" (query, tool list, history) and builds the prompt for the "brain."

3. **Memory**: Retrieves user preferences or long-term memory (e.g., "user prefers floating-point numbers").

4. **Decision**: The "brain" (LLM) takes the facts and preferences, thinks, and decides on a single, structured action.

5. **Action**: The "hands" execute the decision (e.g., call an MCP tool) and report the result.

This loop (Perception -> Memory -> Decision -> Action) repeats until the **Decision** module returns a `FINAL_ANSWER`.

## 3. Detailed Breakdown & Implementation

The agent is implemented across five distinct Python files:

### `main.py` (The Orchestrator)

This is the entry point and the conductor of the entire process.

* **Role**: Manages the agent's `state` (iteration count, history).

* **Initialization**:

  * Loads the Gemini API key.

  * Initializes the Gemini (LLM) client.

  * Establishes the connection to the MCP tool server.

* **Loop**:

  1. Calls `perception.py` to get the list of available tools and build the system prompt (once).

  2. Runs the main agent loop:

  3. Calls `perception.perceive()` to get the facts for the current turn.

  4. Calls `memory.get_preferences()` to get user settings.

  5. Calls `decision.make_decision()` to get the next action from the LLM.

  6. Calls `action.execute_action()` to run the action and get a result.

  7. Updates the `state` with the result.

  8. Terminates the loop if the action status is `DONE` or `FATAL_ERROR`.

### `perception.py` (The Senses)

This module is responsible for gathering all the information the agent needs to make a decision.

* **Role**: To build the "facts" (in the form of a JSON object) that will be fed to the Decision module.

* **Key Functions**:

  * `format_tool_description(tools)`: Takes the raw MCP tool list and formats it into a human-readable string for the prompt.

  * `build_system_prompt(tools_description)`: Creates the static, main instruction prompt that tells the LLM its persona, rules, and the JSON schema it *must* follow.

  * `perceive(user_query, state, system_prompt)`: This is the main function. It assembles the final, complete prompt by combining the `system_prompt`, the `user_query`, and the `state['history']` (context from previous tool calls).

### `memory.py` (The Memory)

This module is currently a placeholder but is designed to provide long-term memory or user preferences.

* **Role**: To retrieve data that influences the agent's behavior.

* **Key Functions**:

  * `get_preferences(user_id)`: In a real application, this would query a database for user settings (e.g., preferred precision, log verbosity). Currently, it returns a stubbed dictionary.

### `decision.py` (The Brain)

This module is the core intelligence of the agent. It takes the facts and decides what to do next.

* **Role**: To invoke the LLM and parse its (potentially messy) output into a clean, structured command.

* **Key Functions**:

  * `generate_with_timeout(client, prompt)`: A wrapper around the Gemini API call that runs it asynchronously with a 10-second timeout.

  * `parse_llm_json_response(response_text)`: This is a critical error-handling function. It cleans the LLM's raw text (e.g., removing markdown \`\`\`json fences) and safely parses it into a Python dictionary.

  * `make_decision(llm_prompt, preferences, llm_client)`: The main function. It calls the LLM, gets the raw text, and uses `parse_llm_json_response` to return a structured decision dictionary (e.g., `{'action_type': 'FUNCTION_CALL', 'action_call': 'add|5|4', 'status': 'IN_PROGRESS'}`).

### `action.py` (The Hands)

This module is responsible for executing the structured command from the Decision module.

* **Role**: To interact with the "outside world" (the MCP tools) or to print the final answer.

* **Key Functions**:

  * `execute_action(decision, mcp_session, tools)`: The main function. It uses a large `if/elif/else` block to handle the `action_type`:

    * **`FUNCTION_CALL`**: Parses the `action_call` string (e.g., "add|5|4"). It finds the corresponding tool in the `tools` list, intelligently converts the string parameters ("5", "4") into the correct types (e.g., `int(5)`, `int(4)`) based on the tool's schema, and then calls `mcp_session.call_tool()`.

    * **`FINAL_ANSWER`**: Prints the final result to the console and returns a `DONE` status to the orchestrator.

    * **`NO_ACTION`**: Logs that the agent is thinking and returns an `IN_PROGRESS` status.

    * **`ERROR`**: Handles any invalid action types.

  * It returns a `result` dictionary (e.g., `{'status': 'IN_PROGRESS', 'history_entry': 'TOOL RESULT from add: 9'}`) which `main.py` uses to update the state for the next loop.

