# -*- coding: utf-8 -*-
"""
Window Inspector Script

A simple diagnostic tool to list all top-level windows visible to pywinauto.
This helps identify the exact window title for applications when the standard
connect() method fails.

Usage:
1. Make sure the target application (e.g., Copilot) is open and visible.
2. Run this script from your terminal: python window_inspector.py
3. Look for the application's title in the output list.
"""

import sys

try:
    # Use the Desktop object to get all top-level windows
    from pywinauto import Desktop
    print("✅ pywinauto imported successfully.")
except ImportError:
    print("❌ Critical Error: pywinauto is not installed.")
    print("   Please run: pip install pywinauto")
    sys.exit(1)

def inspect_windows():
    """Finds and prints all top-level window titles."""
    print("\n🔍 Inspecting all visible top-level windows...")
    print("="*60)

    try:
        # Initialize the Desktop object with the UIA backend
        desktop = Desktop(backend='uia')

        # Get all top-level windows
        windows = desktop.windows()

        if not windows:
            print("No top-level windows found. This is highly unusual.")
            return

        print(f"Found {len(windows)} top-level windows. Titles are:\n")
        
        found_titles = []
        for w in windows:
            try:
                # Get the window title (window_text)
                title = w.window_text()
                # We only care about windows with visible titles
                if title:
                    found_titles.append(title)
            except Exception:
                # Some windows might not be accessible, which is fine
                continue
        
        if found_titles:
            # Sort and print the titles for easy reading
            for title in sorted(found_titles):
                print(f"  - \"{title}\"")
        else:
            print("Could not find any windows with titles.")

        print("="*60)
        print("\n💡 Please find the exact title of the Copilot window in the list above.")
        print("   Update the 'window_title_regex' in your config.json with this title.")

    except Exception as e:
        print(f"\n❌ An unexpected error occurred: {e}")
        print("   This might be a permissions issue. Try running your terminal as an Administrator.")

if __name__ == "__main__":
    inspect_windows()
