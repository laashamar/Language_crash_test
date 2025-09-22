#!/usr/bin/env python3
"""
Microsoft Copilot UI Stress Test Script

This script automates sending messages to the Microsoft Copilot for Windows app
to stress-test its performance and stability through bilingual conversation simulation.

Prerequisites:
- Install the required library: pip install pywinauto
- Microsoft Copilot for Windows app must be running before executing this script
"""

# Import necessary libraries
import time
import random
from pywinauto import Application
from pywinauto.findbestmatch import MatchError
from pywinauto.findwindows import ElementNotFoundError

# =============================================================================
# CONFIGURATION SECTION - USER EDITABLE PARAMETERS
# =============================================================================

# Number of messages to send during the stress test
NUMBER_OF_MESSAGES = 50

# Wait time in seconds between sending messages
WAIT_TIME_SECONDS = 3

# Bilingual sample messages including English and Norwegian with special characters (æ, ø, å)
# and emojis/combined emojis
SAMPLE_MESSAGES = [
    # English messages with emojis
    "Hello! How are you today? 😊",
    "Can you help me with a coding problem? 🤔💻",
    "What's the weather like? ☀️🌤️⛅",
    "I'm working on a Python project 🐍✨",
    "This is a stress test message 🧪⚡",
    "Thank you for your assistance! 🙏😊",
    "Can you explain machine learning? 🤖📚",
    "I love programming! 💖👨‍💻",
    "Have a great day! 🌟💫",
    "Testing the UI automation 🔧⚙️",
    
    # Norwegian messages with special characters (æ, ø, å) and emojis
    "Hei! Hvordan har du det i dag? 😊🇳🇴",
    "Kan du hjelpe meg med et kodeproblem? 🤔💻",
    "Hvordan er været? ☀️❄️",
    "Jeg jobber med et Python-prosjekt 🐍✨",
    "Dette er en stresstest-melding 🧪⚡",
    "Tusen takk for hjelpen! 🙏😊",
    "Kan du forklare maskinlæring? 🤖📚",
    "Jeg elsker å programmere! 💖👨‍💻",
    "Ha en flott dag! 🌟💫",
    "Tester UI-automatisering 🔧⚙️",
    "Jeg bor i Norge 🇳🇴🏔️",
    "Kaffe og kode er bra 😊☕💻",
    "Rødt, gult og grønt 🔴🟡🟢",
    "Ærlighet, øl og åpenhet 🍺💭",
    "Bjørn går på lørdagstur 🐻🚶‍♂️",
    
    # More complex messages mixing languages
    "Hello! Jeg snakker både engelsk og norsk 🌍🗣️",
    "Machine learning og kunstig intelligens 🤖🧠",
    "Python programming med æ, ø, å karakterer 🐍📝"
]

# =============================================================================
# UI ELEMENT IDENTIFIERS - PLACEHOLDER VALUES
# =============================================================================
# ⚠️  IMPORTANT: THESE ARE PLACEHOLDER VALUES! ⚠️
# 
# You MUST find the correct identifiers for your specific system before running this script.
# Use one of these methods to find the correct identifiers:
# 
# Method 1: Uncomment the window.print_control_identifiers() line in the main() function
#           to print a tree of all available UI elements to the console.
# 
# Method 2: Use Microsoft's Inspect.exe tool (comes with Windows SDK)
#           to inspect the Copilot application and find the correct element identifiers.
# 
# Method 3: Use pywinauto's inspection capabilities or other UI automation tools.
# 
# Replace these placeholder values with the actual identifiers from your system:

# Main window identifier - try window title or process name
COPILOT_WINDOW_TITLE = "Copilot"  # Placeholder: Replace with actual window title

# Text input field identifier - could be AutomationId, control type, or name
TEXT_BOX_AUTO_ID = "TextInput"  # Placeholder: Replace with actual text box identifier

# Send button identifier - could be AutomationId, control type, or name  
SEND_BUTTON_AUTO_ID = "SendButton"  # Placeholder: Replace with actual send button identifier

# Alternative identifiers to try if the above don't work
ALT_TEXT_BOX_CONTROL_TYPE = "Edit"  # Alternative: Control type for text input
ALT_SEND_BUTTON_NAME = "Send"  # Alternative: Button name or visible text


def main():
    """
    Main function containing the core automation logic.
    """
    print("🚀 Starting Microsoft Copilot UI Stress Test")
    print(f"📊 Configuration: {NUMBER_OF_MESSAGES} messages, {WAIT_TIME_SECONDS}s wait time")
    print("="*60)
    
    try:
        # Attempt to connect to the Copilot application window
        print("🔗 Connecting to Microsoft Copilot window...")
        app = Application(backend="uia").connect(title=COPILOT_WINDOW_TITLE)
        window = app.window(title=COPILOT_WINDOW_TITLE)
        
        print("✅ Successfully connected to Copilot window")
        
        # DEBUGGING HELPER: Uncomment the line below to print all available UI elements
        # This will help you find the correct identifiers for your system
        # window.print_control_identifiers()
        
        # Main automation loop
        print(f"🔄 Starting message sending loop...")
        
        for i in range(1, NUMBER_OF_MESSAGES + 1):
            try:
                print(f"📝 Sending message {i} of {NUMBER_OF_MESSAGES}")
                
                # Select a random message from our sample list
                message = random.choice(SAMPLE_MESSAGES)
                print(f"💬 Selected message: {message[:50]}{'...' if len(message) > 50 else ''}")
                
                # Find the text input field
                try:
                    text_box = window.child_window(auto_id=TEXT_BOX_AUTO_ID)
                except ElementNotFoundError:
                    # Try alternative identifier if the first one fails
                    print("⚠️  Primary text box identifier failed, trying alternative...")
                    text_box = window.child_window(control_type=ALT_TEXT_BOX_CONTROL_TYPE)
                
                # Clear any existing text and type the new message
                text_box.click_input()
                text_box.type_keys("^a")  # Select all existing text
                text_box.type_keys(message)
                
                print("✏️  Message typed into text box")
                
                # Find and click the send button
                try:
                    send_button = window.child_window(auto_id=SEND_BUTTON_AUTO_ID)
                except ElementNotFoundError:
                    # Try alternative identifier if the first one fails
                    print("⚠️  Primary send button identifier failed, trying alternative...")
                    send_button = window.child_window(name=ALT_SEND_BUTTON_NAME)
                
                send_button.click()
                print("🚀 Send button clicked")
                
                # Wait before sending the next message
                if i < NUMBER_OF_MESSAGES:  # Don't wait after the last message
                    print(f"⏳ Waiting {WAIT_TIME_SECONDS} seconds before next message...")
                    time.sleep(WAIT_TIME_SECONDS)
                
            except ElementNotFoundError as e:
                print(f"❌ Error finding UI element for message {i}: {e}")
                print("💡 Tip: Check your UI element identifiers in the configuration section")
                print("💡 Tip: Uncomment window.print_control_identifiers() to debug")
                continue
                
            except Exception as e:
                print(f"❌ Unexpected error for message {i}: {e}")
                continue
        
        print("="*60)
        print("🎉 Stress test completed successfully!")
        print(f"📊 Sent {NUMBER_OF_MESSAGES} messages to Microsoft Copilot")
        
    except MatchError:
        print("❌ Error: Could not find Microsoft Copilot window")
        print("💡 Make sure Microsoft Copilot is running and the window title is correct")
        print(f"💡 Current window title setting: '{COPILOT_WINDOW_TITLE}'")
        print("💡 You may need to update COPILOT_WINDOW_TITLE in the configuration section")
        return
        
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        print("💡 Check that Microsoft Copilot is running and accessible")
        return


if __name__ == "__main__":
    main()