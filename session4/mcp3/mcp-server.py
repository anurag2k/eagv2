# basic import 
from mcp.server.fastmcp import FastMCP, Image
from mcp.server.fastmcp.prompts import base
from mcp.types import TextContent
from mcp import types
from PIL import Image as PILImage
import math
import sys
import subprocess
import time
import pyautogui
from AppKit import NSWorkspace, NSScreen, NSApplication
from Quartz import CGDisplayBounds, CGMainDisplayID, CGGetActiveDisplayList
import Cocoa

# instantiate an MCP server client
mcp = FastMCP("Calculator")

# Global variable for paint app process
paint_app = None

# DEFINE TOOLS

#addition tool
@mcp.tool()
def add(a: int, b: int) -> int:
    """Add two numbers"""
    print("CALLED: add(a: int, b: int) -> int:")
    return int(a + b)

@mcp.tool()
def add_list(l: list) -> int:
    """Add all numbers in a list"""
    print("CALLED: add(l: list) -> int:")
    return sum(l)

# subtraction tool
@mcp.tool()
def subtract(a: int, b: int) -> int:
    """Subtract two numbers"""
    print("CALLED: subtract(a: int, b: int) -> int:")
    return int(a - b)

# multiplication tool
@mcp.tool()
def multiply(a: int, b: int) -> int:
    """Multiply two numbers"""
    print("CALLED: multiply(a: int, b: int) -> int:")
    return int(a * b)

#  division tool
@mcp.tool() 
def divide(a: int, b: int) -> float:
    """Divide two numbers"""
    print("CALLED: divide(a: int, b: int) -> float:")
    return float(a / b)

# power tool
@mcp.tool()
def power(a: int, b: int) -> int:
    """Power of two numbers"""
    print("CALLED: power(a: int, b: int) -> int:")
    return int(a ** b)

# square root tool
@mcp.tool()
def sqrt(a: int) -> float:
    """Square root of a number"""
    print("CALLED: sqrt(a: int) -> float:")
    return float(a ** 0.5)

# cube root tool
@mcp.tool()
def cbrt(a: int) -> float:
    """Cube root of a number"""
    print("CALLED: cbrt(a: int) -> float:")
    return float(a ** (1/3))

# factorial tool
@mcp.tool()
def factorial(a: int) -> int:
    """factorial of a number"""
    print("CALLED: factorial(a: int) -> int:")
    return int(math.factorial(a))

# log tool
@mcp.tool()
def log(a: int) -> float:
    """log of a number"""
    print("CALLED: log(a: int) -> float:")
    return float(math.log(a))

# remainder tool
@mcp.tool()
def remainder(a: int, b: int) -> int:
    """remainder of two numbers divison"""
    print("CALLED: remainder(a: int, b: int) -> int:")
    return int(a % b)

# sin tool
@mcp.tool()
def sin(a: int) -> float:
    """sin of a number"""
    print("CALLED: sin(a: int) -> float:")
    return float(math.sin(a))

# cos tool
@mcp.tool()
def cos(a: int) -> float:
    """cos of a number"""
    print("CALLED: cos(a: int) -> float:")
    return float(math.cos(a))

# tan tool
@mcp.tool()
def tan(a: int) -> float:
    """tan of a number"""
    print("CALLED: tan(a: int) -> float:")
    return float(math.tan(a))

# mine tool
@mcp.tool()
def mine(a: int, b: int) -> int:
    """special mining tool"""
    print("CALLED: mine(a: int, b: int) -> int:")
    return int(a - b - b)

@mcp.tool()
def create_thumbnail(image_path: str) -> Image:
    """Create a thumbnail from an image"""
    print("CALLED: create_thumbnail(image_path: str) -> Image:")
    img = PILImage.open(image_path)
    img.thumbnail((100, 100))
    return Image(data=img.tobytes(), format="png")

@mcp.tool()
def strings_to_chars_to_int(string: str) -> list[int]:
    """Return the ASCII values of the characters in a word"""
    print("CALLED: strings_to_chars_to_int(string: str) -> list[int]:")
    return [int(ord(char)) for char in string]

@mcp.tool()
def int_list_to_exponential_sum(int_list: list) -> float:
    """Return sum of exponentials of numbers in a list"""
    print("CALLED: int_list_to_exponential_sum(int_list: list) -> float:")
    return sum(math.exp(i) for i in int_list)

@mcp.tool()
def fibonacci_numbers(n: int) -> list:
    """Return the first n Fibonacci Numbers"""
    print("CALLED: fibonacci_numbers(n: int) -> list:")
    if n <= 0:
        return []
    fib_sequence = [0, 1]
    for _ in range(2, n):
        fib_sequence.append(fib_sequence[-1] + fib_sequence[-2])
    return fib_sequence[:n]

@mcp.tool()
async def draw_rectangle(x1: int, y1: int, x2: int, y2: int) -> dict:
    """Draw a rectangle in Paint from (x1,y1) to (x2,y2)"""
    global paint_app
    try:
        if not paint_app:
            return {
                "content": [
                    TextContent(
                        type="text",
                        text="Paint is not open. Please call open_paint first."
                    )
                ]
            }
    
        # Get primary monitor width (equivalent to GetSystemMetrics)
        screens = NSScreen.screens()
        if len(screens) > 1:
            primary_width = int(screens[0].frame().size.width)
            offset_x = primary_width
        else:
            offset_x = 0
    
        # Focus and activate the paint app (equivalent to paint_window.set_focus())
        subprocess.run(['osascript', '-e', 'tell application "Preview" to activate'])
        time.sleep(0.2)
    
        # Click on canvas area (equivalent to paint_window.click_input)
        pyautogui.click(offset_x + 400, 300)
        time.sleep(0.2)
    
        # Draw rectangle by dragging (equivalent to canvas mouse operations)
        # Use explicit mouse down/move/up instead of dragTo
        pyautogui.moveTo(x1 + offset_x, y1)
        pyautogui.mouseDown(button='left')
        pyautogui.moveTo(x2 + offset_x, y2, duration=0.5)
        pyautogui.mouseUp(button='left')
    
        return {
            "content": [
                TextContent(
                    type="text",
                    text=f"Rectangle drawn from ({x1},{y1}) to ({x2},{y2})"
                )
            ]
        }
    except Exception as e:
        return {
            "content": [
                TextContent(
                    type="text",
                    text=f"Error drawing rectangle: {str(e)}"
                )
            ]
        }

@mcp.tool()
async def add_text_in_paint(text: str) -> dict:
    """Add text in Paint"""
    global paint_app
    try:
        if not paint_app:
            return {
                "content": [
                    TextContent(
                        type="text",
                        text="Paint is not open. Please call open_paint first."
                    )
                ]
            }
        
        # Get primary monitor width (equivalent to GetSystemMetrics)
        screens = NSScreen.screens()
        if len(screens) > 1:
            primary_width = int(screens[0].frame().size.width)
            offset_x = primary_width
        else:
            offset_x = 0
        
        # Focus and activate the paint app (equivalent to paint_window.set_focus())
        subprocess.run(['osascript', '-e', 'tell application "Preview" to activate'])
        time.sleep(0.5)
        
        # Click on canvas area
        pyautogui.click(offset_x + 400, 300)
        time.sleep(0.2)
        
        # Select text tool (equivalent to paint_window.type_keys)
        pyautogui.keyDown('cmd')
        pyautogui.press('t')
        pyautogui.keyUp('cmd')
        time.sleep(0.5)
        
        # Click where to start typing (equivalent to canvas.click_input)
        pyautogui.click(offset_x + 400, 400)
        time.sleep(0.5)
        
        # Type the text (equivalent to paint_window.type_keys)
        pyautogui.typewrite(text)
        time.sleep(0.5)
        
        # Click to exit text mode
        pyautogui.click(offset_x + 600, 600)
        
        return {
            "content": [
                TextContent(
                    type="text",
                    text=f"Text:'{text}' added successfully"
                )
            ]
        }
    except Exception as e:
        return {
            "content": [
                TextContent(
                    type="text",
                    text=f"Error: {str(e)}"
                )
            ]
        }

@mcp.tool()
async def open_paint() -> dict:
    """Open Microsoft Paint maximized on secondary monitor"""
    global paint_app
    try:
        # Start Preview instead of mspaint.exe
        paint_app = subprocess.Popen(['open', '-a', 'Preview'])
        time.sleep(2)
        
        # Get primary monitor width (equivalent to GetSystemMetrics)
        screens = NSScreen.screens()
        primary_width = int(screens[0].frame().size.width) if len(screens) > 0 else 0
        
        if len(screens) > 1:
            # Move to secondary monitor and maximize (equivalent to win32gui operations)
            apple_script = f'''
            tell application "Preview"
                activate
                tell application "System Events"
                    tell process "Preview"
                        set frontmost to true
                        tell window 1
                            set position to {{{primary_width + 1}, 0}}
                            set size to {{1920, 1080}}
                        end tell
                    end tell
                end tell
            end tell
            '''
            subprocess.run(['osascript', '-e', apple_script])
        
        return {
            "content": [
                TextContent(
                    type="text",
                    text="Paint opened successfully on secondary monitor and maximized"
                )
            ]
        }
    except Exception as e:
        return {
            "content": [
                TextContent(
                    type="text",
                    text=f"Error opening Paint: {str(e)}"
                )
            ]
        }

# DEFINE RESOURCES

# Add a dynamic greeting resource
@mcp.resource("greeting://{name}")
def get_greeting(name: str) -> str:
    """Get a personalized greeting"""
    print("CALLED: get_greeting(name: str) -> str:")
    return f"Hello, {name}!"


# DEFINE AVAILABLE PROMPTS
@mcp.prompt()
def review_code(code: str) -> str:
    return f"Please review this code:\n\n{code}"
    print("CALLED: review_code(code: str) -> str:")


@mcp.prompt()
def debug_error(error: str) -> list[base.Message]:
    return [
        base.UserMessage("I'm seeing this error:"),
        base.UserMessage(error),
        base.AssistantMessage("I'll help debug that. What have you tried so far?"),
    ]

if __name__ == "__main__":
    # Check if running with mcp dev command
    print("STARTING")
    if len(sys.argv) > 1 and sys.argv[1] == "dev":
        mcp.run()  # Run without transport for dev server
    else:
        mcp.run(transport="stdio")  # Run with stdio for direct execution

