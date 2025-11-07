import os
import asyncio
from dotenv import load_dotenv
from fastmcp import Client

# Load environment variables
load_dotenv()

CREDENTIALS_PATH = os.getenv("MCP_GMAIL_CREDENTIALS_PATH")
TOKEN_PATH       = os.getenv("MCP_GMAIL_TOKEN_PATH")
TRANSPORT        = os.getenv("MCP_SERVER_TRANSPORT", "stdio")
SERVER_CMD       = os.getenv("MCP_SERVER_CMD", "uv")
SERVER_SCRIPT    = os.getenv("MCP_SERVER_SCRIPT", "mcp_gmail/server.py")

async def main():
    # Build the client config for FastMCP
    # Example: using stdio transport, running the server script as subprocess
    config = {
        "mcpServers": {
            "gmail": {
                "transport": TRANSPORT,
                "command": SERVER_CMD,
                "args": ["run", SERVER_SCRIPT,
                         f"--creds-file-path={CREDENTIALS_PATH}",
                         f"--token-path={TOKEN_PATH}"],
                "cwd": "/Users/anuagarwal/Documents/Personal/eagv2/session8/assignment/mcp-gmail",
                "env": {
                    "MCP_GMAIL_CREDENTIALS_PATH": CREDENTIALS_PATH,
                    "MCP_GMAIL_TOKEN_PATH": TOKEN_PATH
                }
            }
        }
    }

    async with Client(config) as client:
        # List available tools
        tools = await client.list_tools()
        print("Available tools:", tools)

        # Use the send_email tool
        recipient = "anurag2k@gmail.com"
        subject   = "Here is your Google Sheet link"
        sheet_link = "https://docs.google.com/spreadsheets/d/XYZ123/edit?usp=sharing"
        body      = f"Hello,\n\nHere is the link to the Google Sheet you requested:\n\n{sheet_link}\n\nBest regards,\nAutomated Agent"

        result = await client.call_tool("send_email",
                                        {
                                            "to": recipient,
                                            "subject": subject,
                                            "body": body
                                        })
        print("Send result:", result)

if __name__ == "__main__":
    asyncio.run(main())
