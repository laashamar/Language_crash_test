#!/usr/bin/env python3
"""
Core UI Automation Logic for Language Crash Test

Contains the main automation logic using pywinauto to interact with Microsoft Copilot.
This module is completely decoupled from GUI components and can be called from 
both CLI and GUI contexts.

Key Features:
- Dynamic UI element discovery with fallback strategies
- Comprehensive error handling and logging
- Thread-safe operation for GUI integration
- Configuration-driven UI element detection
- Automatic application launch if not running
"""

import time
import random
import subprocess
import sys
import os
import json
import logging
from typing import Optional, Tuple, Dict, Any

# Import pywinauto only when needed (inside functions) for thread safety
try:
    from pywinauto.application import Application
    from pywinauto import timings
    from pywinauto.findwindows import ElementNotFoundError
    from pywinauto.findbestmatch import MatchError
    WINDOWS_AVAILABLE = True
except ImportError:
    # Not on Windows or missing dependencies - define dummy classes for syntax checking
    WINDOWS_AVAILABLE = False
    class Application:
        def __init__(self, backend=None): pass
        def start(self, cmd_line): return self
        def connect(self, title_re=None, timeout=None): return self
        def window(self, title_re=None): return self
    class ElementNotFoundError(Exception): pass
    class MatchError(Exception): pass
    class timings:
        class Timings:
            window_find_timeout = 5
            after_clickinput_wait = 0


def parse_debug_output(debug_output: str) -> Optional[Dict]:
    """
    Parse structured JSON data from debug script output.
    Returns dictionary with element candidates or None if parsing fails.
    """
    try:
        # Find JSON data between markers
        start_marker = "JSON_DATA_START"
        end_marker = "JSON_DATA_END"
        
        start_idx = debug_output.find(start_marker)
        end_idx = debug_output.find(end_marker)
        
        if start_idx == -1 or end_idx == -1:
            return None
        
        # Extract JSON data
        json_data = debug_output[start_idx + len(start_marker):end_idx].strip()
        return json.loads(json_data)
        
    except json.JSONDecodeError:
        return None
    except Exception:
        return None


def dump_control_tree_via_script(config, logger) -> Optional[Dict]:
    """
    Call the separate debug script to dump control tree.
    Returns parsed structured data or None if failed.
    """
    try:
        # Import debug module dynamically
        from . import debug
        
        logger.info("📋 Running debug script for control tree (fallback method)...")
        
        # Get UI elements using the debug module
        elements_data = debug.inspect_ui_elements(config.window_title_regex)
        
        if elements_data:
            logger.info("✅ Debug script completed successfully")
            return elements_data
        else:
            logger.warning("⚠️ Debug script returned no data")
            return None
            
    except Exception as e:
        logger.error(f"❌ Error running debug script: {type(e).__name__}: {e}")
        return None


def enhanced_element_validation(element, element_type: str, pattern: str) -> Tuple[bool, str]:
    """
    Enhanced validation for UI elements with detailed feedback.
    
    Args:
        element: pywinauto element to validate
        element_type: Type of element (text_input, send_button, etc.)
        pattern: Pattern used to find the element
        
    Returns:
        Tuple of (is_valid, reason)
    """
    try:
        if not element.exists():
            return False, "Element does not exist"
        
        if not element.is_visible():
            return False, "Element is not visible"
        
        if not element.is_enabled():
            return False, "Element is not enabled"
        
        # Element type specific validation
        if element_type == "text_input":
            # For text inputs, try to focus to verify it's interactable
            try:
                element.set_focus()
                return True, f"Valid text input found with pattern: {pattern}"
            except Exception:
                return False, "Cannot focus on text input element"
                
        elif element_type == "send_button":
            # For buttons, verify they can be clicked
            try:
                # Just check if it's clickable, don't actually click
                rect = element.rectangle()
                if rect.width() > 0 and rect.height() > 0:
                    return True, f"Valid button found with pattern: {pattern}"
                else:
                    return False, "Button has zero dimensions"
            except Exception:
                return False, "Cannot access button properties"
        
        return True, f"Element validated with pattern: {pattern}"
        
    except Exception as e:
        return False, f"Validation error: {e}"


def try_element_candidates(window, candidates: list, element_type: str) -> Tuple[Optional[Any], Optional[Dict]]:
    """
    Try a list of element candidates to find a working one.
    
    Args:
        window: pywinauto window object
        candidates: List of candidate element info dictionaries
        element_type: Type of element we're looking for
        
    Returns:
        Tuple of (element, candidate_info) or (None, None)
    """
    for candidate in candidates:
        try:
            auto_id = candidate.get('auto_id', '')
            title = candidate.get('title', '')
            control_type = candidate.get('control_type', '')
            
            # Try different approaches to find the element
            element = None
            
            # First try auto_id
            if auto_id:
                try:
                    element = window.child_window(auto_id=auto_id)
                    if enhanced_element_validation(element, element_type, auto_id)[0]:
                        return element, candidate
                except ElementNotFoundError:
                    pass
            
            # Then try title
            if title and not element:
                try:
                    element = window.child_window(title=title)
                    if enhanced_element_validation(element, element_type, title)[0]:
                        return element, candidate
                except ElementNotFoundError:
                    pass
            
            # Finally try control type
            if control_type and not element:
                try:
                    element = window.child_window(control_type=control_type)
                    if enhanced_element_validation(element, element_type, control_type)[0]:
                        return element, candidate
                except ElementNotFoundError:
                    pass
                    
        except Exception:
            continue
    
    return None, None


def find_element_with_dynamic_fallback(window, element_type: str, patterns: list, config, logger) -> Tuple[Optional[Any], Optional[str]]:
    """
    Find UI element using known patterns first, then dynamic discovery as fallback.
    
    Args:
        window: pywinauto window object
        element_type: Type of element (text_input, send_button, new_conversation)
        patterns: List of known patterns to try first
        config: Configuration object
        logger: Logger instance
        
    Returns:
        Tuple of (element, method_used) or (None, None)
    """
    # First try known patterns
    for pattern in patterns:
        try:
            # Try auto_id first
            element = window.child_window(auto_id=pattern)
            if enhanced_element_validation(element, element_type, pattern)[0]:
                return element, f"known_pattern_auto_id: {pattern}"
        except ElementNotFoundError:
            try:
                # Then try title
                element = window.child_window(title=pattern)
                if enhanced_element_validation(element, element_type, pattern)[0]:
                    return element, f"known_pattern_title: {pattern}"
            except ElementNotFoundError:
                continue
    
    # If known patterns fail, use dynamic discovery
    logger.info(f"Known patterns failed for {element_type}, using dynamic discovery...")
    
    debug_data = dump_control_tree_via_script(config, logger)
    if not debug_data:
        logger.warning("Dynamic discovery failed - no debug data available")
        return None, None
    
    candidates = debug_data.get(f'{element_type}_candidates', [])
    element, candidate_info = try_element_candidates(window, candidates, element_type)
    
    if element:
        auto_id = candidate_info.get('auto_id', '')
        title = candidate_info.get('title', '')
        method = f"dynamic_discovery: {auto_id}/{title}"
        logger.info(f"✅ Dynamic discovery successful for {element_type}: {method}")
        return element, method
    
    logger.error(f"❌ Could not find {element_type} element with any method")
    return None, None


def validate_window(window, logger) -> bool:
    """Validates that the window is available and usable."""
    try:
        if window.exists() and window.is_visible() and window.is_enabled():
            window.set_focus()
            logger.info("✅ Window validation successful")
            return True
    except Exception as e:
        logger.error(f"Window validation failed: {e}")
    return False


def run_stress_test_logic(config, logger) -> Dict[str, Any]:
    """
    Contains the core stress test logic.
    This function is designed to be called from different entry points (CLI, GUI)
    and returns a result dictionary instead of calling sys.exit().
    
    Args:
        config: Configuration object with test parameters
        logger: Logger instance for output
        
    Returns:
        Dictionary with keys: success (int), total (int), error (str, optional)
    """
    logger.info("🚀 Starting Microsoft Copilot UI Stress Test Logic")
    logger.info(f"📊 Configuration: {config.get_runtime_summary()}")
    
    if not WINDOWS_AVAILABLE:
        error_msg = "❌ pywinauto not available or not on Windows"
        logger.error(error_msg)
        return {'success': 0, 'total': config.number_of_messages, 'error': error_msg}

    success_count = 0
    try:
        # NY LOGIKK: Prøv å koble til, hvis det feiler, prøv å starte
        try:
            logger.info("🔗 Attempting to connect to existing Copilot window...")
            app = Application(backend="uia").connect(title_re=config.window_title_regex, timeout=5)
            window = app.window(title_re=config.window_title_regex)
            logger.info(f"✅ Found existing Copilot window.")
        except (ElementNotFoundError, MatchError):
            logger.warning("⚠️ Could not find running Copilot window.")
            if config.launch_if_not_found:
                logger.info(f"🚀 Launching Copilot using command: '{config.copilot_launch_command}'...")
                try:
                    Application(backend="uia").start(config.copilot_launch_command)
                    logger.info("⏳ Waiting 10 seconds for Copilot to initialize...")
                    time.sleep(10)

                    logger.info("🔗 Re-attempting to connect after launch...")
                    app = Application(backend="uia").connect(title_re=config.window_title_regex, timeout=15)
                    window = app.window(title_re=config.window_title_regex)
                    logger.info("✅ Successfully connected to newly launched Copilot window.")
                except Exception as launch_error:
                    error_msg = f"❌ Failed to launch or connect to Copilot after launch: {launch_error}"
                    logger.critical(error_msg)
                    return {'success': 0, 'total': config.number_of_messages, 'error': error_msg}
            else:
                error_msg = "❌ Could not find Copilot window and auto-launch is disabled in config."
                logger.critical(error_msg)
                return {'success': 0, 'total': config.number_of_messages, 'error': error_msg}

        if not validate_window(window, logger):
            error_msg = "❌ Window validation failed after connection attempt."
            logger.error(error_msg)
            return {'success': 0, 'total': config.number_of_messages, 'error': error_msg}

        # Try to start a new conversation (optional)
        try:
            new_chat_element, method = find_element_with_dynamic_fallback(
                window, "new_conversation", config.new_conversation_patterns, config, logger
            )
            if new_chat_element:
                new_chat_element.click_input()
                logger.info(f"🆕 New conversation started (method: {method})")
                time.sleep(1)
            else:
                logger.warning("ℹ️ New conversation button not found - continuing with current conversation")
        except Exception as e:
            logger.warning(f"⚠️ Error starting new conversation: {e} - continuing")

        logger.info("🔄 Starting message loop...")
        for i in range(1, config.number_of_messages + 1):
            try:
                message = random.choice(config.sample_messages)
                logger.info(f"📝 Sending message {i}/{config.number_of_messages}: {message[:50]}...")

                # Find text input
                text_box, method = find_element_with_dynamic_fallback(
                    window, "text_input", config.text_input_patterns, config, logger
                )
                if not text_box:
                    logger.error(f"❌ Text input not found for message {i}")
                    continue

                # Clear and type message
                text_box.type_keys("^a{BACKSPACE}", with_spaces=True)
                text_box.type_keys(message, with_spaces=True)

                # Find send button
                send_button, method = find_element_with_dynamic_fallback(
                    window, "send_button", config.send_button_patterns, config, logger
                )
                if not send_button:
                    logger.error(f"❌ Send button not found for message {i}")
                    continue
                
                # CRITICAL: Wait for the button to be enabled before clicking
                send_button.wait('enabled', timeout=5)
                send_button.click_input()
                
                logger.info(f"🚀 Message {i} sent successfully")
                success_count += 1

                # Wait between messages (except for the last one)
                if i < config.number_of_messages:
                    time.sleep(config.wait_time_seconds)

            except Exception as e:
                logger.error(f"❌ Unexpected error at message {i}: {type(e).__name__}: {e}")
                continue
        
        logger.info(f"✅ Message loop completed. Sent {success_count}/{config.number_of_messages} messages")
        return {'success': success_count, 'total': config.number_of_messages}

    except (ElementNotFoundError, MatchError) as e:
        error_msg = f"❌ Could not find Copilot window: {e}"
        logger.critical(error_msg)
        return {'success': 0, 'total': config.number_of_messages, 'error': error_msg}
    except Exception as e:
        error_msg = f"❌ An unexpected critical error occurred: {type(e).__name__}: {e}"
        logger.critical(error_msg)
        return {'success': 0, 'total': config.number_of_messages, 'error': error_msg}
