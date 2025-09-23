#!/usr/bin/env python3
"""
UI Element Inspection Module for Language Crash Test

Provides utilities to inspect and analyze Microsoft Copilot UI elements.
Used as a fallback method for dynamic element discovery when known patterns fail.

Key Features:
- UI control tree inspection and analysis
- Element pattern identification for text inputs and buttons
- JSON structured output for automation consumption
- Norwegian language UI support
"""

import json
import sys
import os
import re
from typing import Dict, List, Optional, Any

try:
    from pywinauto.application import Application
    from pywinauto.findwindows import ElementNotFoundError
    from pywinauto.findbestmatch import MatchError
    WINDOWS_AVAILABLE = True
except ImportError:
    # Not on Windows or missing dependencies - define dummy classes
    WINDOWS_AVAILABLE = False
    class Application:
        def __init__(self, backend=None): pass
        def connect(self, title_re=None): return self
        def window(self, title_re=None): return self
    class ElementNotFoundError(Exception): pass
    class MatchError(Exception): pass


def is_likely_text_input(element_info: Dict) -> bool:
    """
    Determine if an element is likely a text input based on its properties.
    
    Args:
        element_info: Dictionary with element properties
        
    Returns:
        Boolean indicating if element is likely a text input
    """
    control_type = element_info.get('control_type', '').lower()
    auto_id = element_info.get('auto_id', '').lower()
    title = element_info.get('title', '').lower()
    class_name = element_info.get('class_name', '').lower()
    
    # Control type indicators
    text_input_types = ['edit', 'text', 'document', 'custom']
    if any(ct in control_type for ct in text_input_types):
        return True
    
    # Auto ID patterns that suggest text input
    text_input_patterns = [
        'input', 'textbox', 'compose', 'message', 'chat', 
        'edit', 'text', 'type', 'enter'
    ]
    if any(pattern in auto_id for pattern in text_input_patterns):
        return True
    
    # Class name patterns
    text_class_patterns = ['edit', 'textbox', 'input', 'compose']
    if any(pattern in class_name for pattern in text_class_patterns):
        return True
    
    return False


def is_likely_send_button(element_info: Dict) -> bool:
    """
    Determine if an element is likely a send button based on its properties.
    
    Args:
        element_info: Dictionary with element properties
        
    Returns:
        Boolean indicating if element is likely a send button
    """
    control_type = element_info.get('control_type', '').lower()
    auto_id = element_info.get('auto_id', '').lower()
    title = element_info.get('title', '').lower()
    class_name = element_info.get('class_name', '').lower()
    
    # Control type indicators
    button_types = ['button', 'custom', 'menuitem']
    if not any(bt in control_type for bt in button_types):
        return False
    
    # Norwegian and English send button patterns, now more robust
    send_patterns = [
        'send', 'submit', 'post', 'snakk', 'mic', 'microphone',
        'composer', 'oldcomposer', 'copilot', 'arrow', 'icon'
    ]
    
    # Combine auto_id and title for a broader search
    combined_text = f"{auto_id} {title}".lower()

    # Check combined text against all patterns
    if any(pattern in combined_text for pattern in send_patterns):
        return True
    
    return False


def is_likely_new_conversation_button(element_info: Dict) -> bool:
    """
    Determine if an element is likely a new conversation button.
    
    Args:
        element_info: Dictionary with element properties
        
    Returns:
        Boolean indicating if element is likely a new conversation button
    """
    control_type = element_info.get('control_type', '').lower()
    auto_id = element_info.get('auto_id', '').lower()
    title = element_info.get('title', '').lower()
    
    # Control type indicators
    button_types = ['button', 'custom', 'menuitem']
    if not any(bt in control_type for bt in button_types):
        return False
    
    # New conversation patterns (Norwegian and English)
    new_conv_patterns = [
        'home', 'hjem', 'new', 'ny', 'conversation', 'samtale',
        'fresh', 'start', 'begin'
    ]
    
    # Check auto_id and title
    text_to_check = f"{auto_id} {title}".lower()
    return any(pattern in text_to_check for pattern in new_conv_patterns)


def extract_element_info(element) -> Dict[str, str]:
    """
    Extract relevant information from a pywinauto element.
    
    Args:
        element: pywinauto element
        
    Returns:
        Dictionary with element properties
    """
    try:
        info = {
            'auto_id': '',
            'title': '',
            'control_type': '',
            'class_name': '',
            'is_visible': False,
            'is_enabled': False
        }
        
        # Safely extract properties
        try:
            info['auto_id'] = element.automation_id() or ''
        except:
            pass
            
        try:
            info['title'] = element.window_text() or ''
        except:
            pass
            
        try:
            info['control_type'] = element.control_type() or ''
        except:
            pass
            
        try:
            info['class_name'] = element.class_name() or ''
        except:
            pass
            
        try:
            info['is_visible'] = element.is_visible()
        except:
            pass
            
        try:
            info['is_enabled'] = element.is_enabled()
        except:
            pass
        
        return info
        
    except Exception:
        return {
            'auto_id': '',
            'title': '',
            'control_type': '',
            'class_name': '',
            'is_visible': False,
            'is_enabled': False
        }


def inspect_ui_elements(window_title_regex: str = r"^Copilot.*") -> Optional[Dict]:
    """
    Inspect UI elements in the Copilot window and categorize potential candidates.
    
    Args:
        window_title_regex: Regex pattern to match the window title
        
    Returns:
        Dictionary with categorized element candidates or None if failed
    """
    if not WINDOWS_AVAILABLE:
        print("❌ pywinauto not available or not on Windows")
        return None
    
    try:
        print(f"🔍 Connecting to window with pattern: {window_title_regex}")
        app = Application(backend="uia").connect(title_re=window_title_regex)
        window = app.window(title_re=window_title_regex)
        
        if not window.exists():
            print("❌ Window not found")
            return None
        
        print("✅ Connected to window, analyzing elements...")
        
        # Get all descendant elements
        descendants = window.descendants()
        
        # Categorize elements
        text_input_candidates = []
        send_button_candidates = []
        new_conversation_candidates = []
        all_elements = []
        
        for element in descendants:
            element_info = extract_element_info(element)
            
            # Only consider visible and enabled elements for interactive candidates
            if element_info['is_visible'] and element_info['is_enabled']:
                if is_likely_text_input(element_info):
                    text_input_candidates.append(element_info)
                
                if is_likely_send_button(element_info):
                    send_button_candidates.append(element_info)
                
                if is_likely_new_conversation_button(element_info):
                    new_conversation_candidates.append(element_info)
            
            # Add to all elements list (for debugging)
            all_elements.append(element_info)
        
        # Prepare structured result
        result = {
            'text_input_candidates': text_input_candidates,
            'send_button_candidates': send_button_candidates,
            'new_conversation_candidates': new_conversation_candidates,
            'total_elements': len(all_elements),
            'analysis_summary': {
                'text_inputs_found': len(text_input_candidates),
                'send_buttons_found': len(send_button_candidates),
                'new_conversation_buttons_found': len(new_conversation_candidates),
                'window_pattern': window_title_regex
            }
        }
        
        print(f"📊 Analysis complete:")
        print(f"   Text input candidates: {len(text_input_candidates)}")
        print(f"   Send button candidates: {len(send_button_candidates)}")
        print(f"   New conversation candidates: {len(new_conversation_candidates)}")
        print(f"   Total elements analyzed: {len(all_elements)}")
        
        return result
        
    except (ElementNotFoundError, MatchError) as e:
        print(f"❌ Could not find window: {e}")
        return None
    except Exception as e:
        print(f"❌ Error during inspection: {type(e).__name__}: {e}")
        return None


def print_control_identifiers(window_title_regex: str = r"^Copilot.*", max_depth: int = 3) -> None:
    """
    Print a tree of UI control identifiers for debugging purposes.
    
    Args:
        window_title_regex: Regex pattern to match the window title
        max_depth: Maximum depth to traverse in the control tree
    """
    if not WINDOWS_AVAILABLE:
        print("❌ pywinauto not available or not on Windows")
        return
    
    try:
        print(f"🔍 Connecting to window with pattern: {window_title_regex}")
        app = Application(backend="uia").connect(title_re=window_title_regex)
        window = app.window(title_re=window_title_regex)
        
        if not window.exists():
            print("❌ Window not found")
            return
        
        print("📋 Control Tree:")
        print("=" * 80)
        
        def print_element(element, depth=0, max_depth=max_depth):
            if depth > max_depth:
                return
            
            indent = "  " * depth
            element_info = extract_element_info(element)
            
            # Format the output
            auto_id = element_info['auto_id']
            title = element_info['title']
            control_type = element_info['control_type']
            class_name = element_info['class_name']
            visible = "👁️" if element_info['is_visible'] else "❌"
            enabled = "✅" if element_info['is_enabled'] else "❌"
            
            # Create display text
            display_parts = []
            if control_type:
                display_parts.append(f"[{control_type}]")
            if auto_id:
                display_parts.append(f"ID:{auto_id}")
            if title:
                display_parts.append(f"Title:'{title}'")
            if class_name:
                display_parts.append(f"Class:{class_name}")
            
            display_text = " ".join(display_parts) if display_parts else "No identifiers"
            
            print(f"{indent}{visible}{enabled} {display_text}")
            
            # Recursively print children
            try:
                children = element.children()
                for child in children:
                    print_element(child, depth + 1, max_depth)
            except:
                pass
        
        # Start printing from the main window
        print_element(window)
        
        print("=" * 80)
        print("Legend: 👁️ = Visible, ❌ = Hidden/Disabled, ✅ = Enabled")
        
    except (ElementNotFoundError, MatchError) as e:
        print(f"❌ Could not find window: {e}")
    except Exception as e:
        print(f"❌ Error during tree printing: {type(e).__name__}: {e}")


def main():
    """Main function for standalone execution."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Copilot UI Element Inspector")
    parser.add_argument(
        '--window-pattern', '-w',
        default=r"^Copilot.*",
        help="Window title regex pattern (default: ^Copilot.*)"
    )
    parser.add_argument(
        '--print-tree', '-t',
        action='store_true',
        help="Print full control tree"
    )
    parser.add_argument(
        '--max-depth', '-d',
        type=int,
        default=3,
        help="Maximum tree depth to print (default: 3)"
    )
    parser.add_argument(
        '--json-output', '-j',
        action='store_true',
        help="Output results as JSON"
    )
    
    args = parser.parse_args()
    
    if args.print_tree:
        print_control_identifiers(args.window_pattern, args.max_depth)
    else:
        result = inspect_ui_elements(args.window_pattern)
        
        if result and args.json_output:
            # Output JSON for automation consumption
            print("JSON_DATA_START")
            print(json.dumps(result, indent=2, ensure_ascii=False))
            print("JSON_DATA_END")
        elif result:
            # Human-readable output
            print("\n🎯 Element Analysis Results:")
            print("=" * 50)
            
            for category, candidates in result.items():
                if category.endswith('_candidates') and candidates:
                    print(f"\n{category.replace('_', ' ').title()}:")
                    for i, candidate in enumerate(candidates, 1):
                        print(f"  {i}. Auto ID: '{candidate.get('auto_id', 'N/A')}'")
                        print(f"     Title: '{candidate.get('title', 'N/A')}'")
                        print(f"     Type: {candidate.get('control_type', 'N/A')}")
                        print()


if __name__ == "__main__":
    main()
