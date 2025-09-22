#!/usr/bin/env python3
"""
Microsoft Copilot UI Stress Test Script

Automatiserer sending av meldinger til Microsoft Copilot for Windows-appen
for å teste ytelse og stabilitet gjennom en flerspråklig samtalesimulering.

Krav:
- Installer pywinauto: pip install pywinauto
- Sørg for at Microsoft Copilot er åpen før du kjører skriptet
"""

import time
import random
import subprocess
import sys
import os
import json
import re
import logging

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
        def connect(self, title_re=None): return self
        def window(self, title_re=None): return self
    class ElementNotFoundError(Exception): pass
    class MatchError(Exception): pass
    class timings:
        class Timings:
            window_find_timeout = 5
            after_clickinput_wait = 0

# Global configuration (set by main.py or defaults)
_config = None

def set_config(config):
    """Set the global configuration for this module."""
    global _config
    _config = config

def get_config():
    """Get the current configuration, with fallback to defaults."""
    global _config
    if _config is None:
        # Fallback to default values if no config is set
        from config import Config
        _config = Config()
    return _config

# =============================================================================
# HJELPEFUNKSJONER FOR DYNAMISK UI-ELEMENT OPPDAGELSE
# (Disse funksjonene er uendret)
# =============================================================================

def parse_debug_output(debug_output):
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
            print("⚠️ Ingen strukturert data funnet i debug-output")
            return None
        
        # Extract JSON data
        json_data = debug_output[start_idx + len(start_marker):end_idx].strip()
        return json.loads(json_data)
        
    except json.JSONDecodeError as e:
        print(f"⚠️ Kunne ikke parse JSON fra debug-output: {e}")
        return None
    except Exception as e:
        print(f"⚠️ Feil ved parsing av debug-output: {e}")
        return None

def dump_control_tree_via_script():
    """
    Kaller den separate debug-scriptet for å dumpe kontrolltre.
    Returns parsed structured data or None if failed.
    """
    try:
        script_path = os.path.join(os.path.dirname(__file__), "copilot_ui_debug.py")
        if os.path.exists(script_path):
            config = get_config()
            print("📋 Kjører separat debug-script for kontrolltre (required fallback)...")
            result = subprocess.run([sys.executable, script_path],
                                  capture_output=True, text=True, timeout=config.debug_output_timeout)
            if result.returncode == 0:
                print("✅ Debug-script kjørt vellykket")
                return parse_debug_output(result.stdout)
            else:
                print(f"⚠️ Debug-script feilet med returkode {result.returncode}:")
                print(f"STDERR: {result.stderr}")
                return None
        else:
            print(f"❌ KRITISK: Debug-script ikke funnet: {script_path}")
            return None
    except subprocess.TimeoutExpired:
        print("⚠️ Debug-script timeout")
        return None
    except Exception as e:
        print(f"❌ Feil ved kjøring av debug-script: {type(e).__name__}: {e}")
        return None

def enhanced_element_validation(element, element_type, identifier):
    """Enhanced validation of UI elements."""
    try:
        if not element.exists() or not element.is_visible() or not element.is_enabled():
            return False, "Element not ready"
        return True, "Element is valid"
    except Exception as e:
        return False, f"Validation error: {e}"

def log_recovery_attempt(element_type, attempt_num, total_attempts, method, result, details=""):
    """Log detailed information about element recovery attempts."""
    status_emoji = "✅" if result == "success" else "⚠️" if result == "partial" else "❌"
    logging.info(f"{status_emoji} Attempt {attempt_num}/{total_attempts} for {element_type} via {method}: {result}. Details: {details}")

def try_element_candidates(window, candidates, element_type):
    """Try to find and validate UI elements from prioritized candidate list."""
    if not candidates:
        return None, None
    
    for i, candidate in enumerate(candidates, 1):
        search_criteria = {k: v for k, v in candidate.items() if v and k in ['auto_id', 'title', 'control_type']}
        if not search_criteria:
            continue
        try:
            element = window.child_window(**search_criteria)
            is_valid, _ = enhanced_element_validation(element, element_type, str(search_criteria))
            if is_valid:
                return element, candidate
        except ElementNotFoundError:
            continue
    return None, None

def find_element_with_dynamic_fallback(window, element_type, known_patterns, config):
    """Find UI element using known patterns first, then dynamic discovery as fallback."""
    patterns_map = {
        "text_input": config.text_input_patterns,
        "send_button": config.send_button_patterns,
        "new_conversation": config.new_conversation_patterns
    }
    
    for pattern in patterns_map.get(element_type, []):
        try:
            element = window.child_window(auto_id=pattern)
            if enhanced_element_validation(element, element_type, pattern)[0]:
                return element, f"known_pattern: {pattern}"
        except ElementNotFoundError:
            try:
                element = window.child_window(title=pattern)
                if enhanced_element_validation(element, element_type, pattern)[0]:
                    return element, f"known_pattern: {pattern}"
            except ElementNotFoundError:
                continue

    debug_data = dump_control_tree_via_script()
    if not debug_data:
        return None, None
    
    candidates = debug_data.get(f'{element_type}_candidates', [])
    element, candidate_info = try_element_candidates(window, candidates, element_type)
    if element:
        method = f"dynamic_discovery: {candidate_info.get('auto_id', '')}/{candidate_info.get('title', '')}"
        return element, method
    
    return None, None
    
def validate_window(window):
    """Validates that the window is available and usable."""
    try:
        if window.exists() and window.is_visible() and window.is_enabled():
            window.set_focus()
            return True
    except Exception as e:
        logging.error(f"Window validation failed: {e}")
    return False

# =============================================================================
# REFAKTORERT HOVEDLOGIKK
# =============================================================================

def run_stress_test_logic(config, logger):
    """
    Contains the core stress test logic.
    This function is designed to be called from different entry points (CLI, GUI)
    and returns a result dictionary instead of calling sys.exit().
    """
    logger.info("🚀 Starting Microsoft Copilot UI Stress Test Logic")
    logger.info(f"📊 Configuration: {config.get_runtime_summary()}")
    
    if not WINDOWS_AVAILABLE:
        error_msg = "❌ pywinauto not available or not on Windows"
        logger.error(error_msg)
        return {'success': 0, 'total': config.number_of_messages, 'error': error_msg}

    success_count = 0
    try:
        logger.info("🔗 Connecting to Copilot window...")
        app = Application(backend="uia").connect(title_re=config.window_title_regex)
        window = app.window(title_re=config.window_title_regex)
        logger.info(f"✅ Connected to Copilot window with regex: {config.window_title_regex}")

        if not validate_window(window):
            error_msg = "❌ Window validation failed"
            logger.error(error_msg)
            return {'success': 0, 'total': config.number_of_messages, 'error': error_msg}

        try:
            new_chat_element, method = find_element_with_dynamic_fallback(
                window, "new_conversation", config.new_conversation_patterns, config
            )
            if new_chat_element:
                new_chat_element.click_input()
                logger.info(f"🆕 New conversation started (method: {method})")
                time.sleep(1)
            else:
                logger.warning("ℹ️ New conversation button not found - continuing")
        except Exception as e:
            logger.warning(f"⚠️ Error starting new conversation: {e} - continuing")

        logger.info("🔄 Starting message loop...")
        for i in range(1, config.number_of_messages + 1):
            try:
                message = random.choice(config.sample_messages)
                logger.info(f"📝 Sending message {i}/{config.number_of_messages}: {message[:50]}...")

                text_box, _ = find_element_with_dynamic_fallback(
                    window, "text_input", config.text_input_patterns, config
                )
                if not text_box:
                    logger.error(f"❌ Text input not found for message {i}")
                    continue

                text_box.type_keys("^a{BACKSPACE}", with_spaces=True)
                text_box.type_keys(message, with_spaces=True)

                send_button, _ = find_element_with_dynamic_fallback(
                    window, "send_button", config.send_button_patterns, config
                )
                if not send_button:
                    logger.error(f"❌ Send button not found for message {i}")
                    continue

                send_button.click_input()
                logger.info(f"🚀 Message {i} sent successfully")
                success_count += 1

                if i < config.number_of_messages:
                    time.sleep(config.wait_time_seconds)

            except Exception as e:
                logger.error(f"❌ Unexpected error at message {i}: {type(e).__name__}: {e}")
                continue
        
        return {'success': success_count, 'total': config.number_of_messages}

    except (ElementNotFoundError, MatchError) as e:
        error_msg = f"❌ Could not find Copilot window: {e}"
        logger.critical(error_msg)
        return {'success': 0, 'total': config.number_of_messages, 'error': error_msg}
    except Exception as e:
        error_msg = f"❌ An unexpected critical error occurred: {type(e).__name__}: {e}"
        logger.critical(error_msg)
        return {'success': 0, 'total': config.number_of_messages, 'error': error_msg}

# =============================================================================
# ORIGINAL HOVEDFUNKSJON (FOR KOMMANDOLINJEBRUK)
# =============================================================================

def main():
    """Main function for CLI stress testing."""
    config = get_config()
    
    # Setup logging to console for CLI mode
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', stream=sys.stdout)
    logger = logging.getLogger(__name__)
    
    try:
        result = run_stress_test_logic(config, logger)
        success_count = result.get('success', 0)
        total_messages = result.get('total', 0)
        error = result.get('error')

        print("="*60)
        if error:
            print(f"❌ Testen stoppet på grunn av en kritisk feil: {error}")
            sys.exit(1)

        print("🎉 Stresstest fullført!")
        print(f"📊 Totalt sendt: {success_count} av {total_messages} meldinger")

        if success_count == 0:
            print("❌ Ingen meldinger ble sendt - avslutter med feilkode")
            sys.exit(1)
        elif success_count < total_messages:
            print(f"⚠️ {total_messages - success_count} meldinger feilet - delvis suksess")
            sys.exit(0)
        else:
            print("✅ Alle meldinger sendt vellykket")
            sys.exit(0)

    except KeyboardInterrupt:
        print("\n⏹️ Stoppet av bruker")
        sys.exit(1)

if __name__ == "__main__":
    main()
